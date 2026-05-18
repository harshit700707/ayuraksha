# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from database.models import db, ICUPatient, ICUVitals, ICUAlert, Hospital
from utils import success_response, error_response
from utils.whatsapp import send_icu_alert

icu_bp = Blueprint('icu', __name__)


def calculate_risk(vitals_data):
    """Calculate qSOFA and risk score from vitals."""
    qsofa = 0
    if vitals_data.get('respiratory_rate', 0) >= 22:
        qsofa += 1
    if vitals_data.get('gcs', 15) < 15:
        qsofa += 1
    if vitals_data.get('systolic_bp', 120) <= 100:
        qsofa += 1

    risk = (qsofa / 3) * 60

    temp = vitals_data.get('temperature', 37.0)
    if temp > 38.5:
        risk += 10
    elif temp < 36.0:
        risk += 8

    hr = vitals_data.get('heart_rate', 80)
    if hr > 130:
        risk += 18
    elif hr > 110:
        risk += 10

    lactate = vitals_data.get('lactate')
    if lactate and lactate > 2.0:
        risk += 12

    spo2 = vitals_data.get('spo2', 98)
    if spo2 < 95:
        risk += 8

    risk = min(int(risk), 100)

    if risk >= 70:
        status = 'critical'
    elif risk >= 40:
        status = 'moderate'
    else:
        status = 'stable'

    return qsofa, risk, status


def get_recommendations(risk, qsofa, vitals):
    recs = []
    if risk >= 70:
        recs.append("IMMEDIATE: Blood cultures x2 before antibiotics")
        recs.append("IMMEDIATE: Start broad-spectrum IV antibiotics")
        recs.append("IMMEDIATE: 30ml/kg IV fluid bolus (crystalloid)")
        recs.append("URGENT: Serum lactate measurement")
        recs.append("URGENT: Urine output monitoring (target >0.5ml/kg/hr)")
    elif risk >= 40:
        recs.append("Monitor vitals every 30 minutes")
        recs.append("Check blood cultures if fever persists")
        recs.append("Reassess fluid status")
    else:
        recs.append("Continue routine monitoring")
        recs.append("Vitals stable — reassess in 4 hours")

    if vitals.get('spo2', 98) < 95:
        recs.append("Supplemental oxygen — target SpO2 >= 95%")
    if vitals.get('heart_rate', 80) > 120:
        recs.append("ECG to rule out arrhythmia")

    return recs


@icu_bp.route('/patients', methods=['GET'])
@jwt_required()
def get_patients():
    claims = get_jwt()
    hospital_id = claims.get('hospital_id') or request.args.get('hospital_id', type=int)
    patients = ICUPatient.query.filter_by(hospital_id=hospital_id, is_active=True).all()
    return jsonify(success_response([p.to_dict() for p in patients]))


@icu_bp.route('/patient/add', methods=['POST'])
@jwt_required()
def add_patient():
    claims = get_jwt()
    if claims.get('role') != 'hospital':
        return jsonify(error_response("Unauthorized")[0]), 403
    hospital_id = claims.get('hospital_id')
    data = request.get_json()
    patient = ICUPatient(
        hospital_id=hospital_id,
        bed_number=data['bed_number'],
        patient_name=data['patient_name'],
        age=data.get('age', 0),
        gender=data.get('gender', 'M'),
        diagnosis=data.get('diagnosis', ''),
        doctor_name=data.get('doctor_name', ''),
        doctor_phone=data.get('doctor_phone', ''),
    )
    db.session.add(patient)
    db.session.commit()
    return jsonify(success_response(patient.to_dict(), "Patient added to ICU"))


@icu_bp.route('/vitals', methods=['POST'])
@jwt_required()
def record_vitals():
    claims = get_jwt()
    if claims.get('role') != 'hospital':
        return jsonify(error_response("Unauthorized")[0]), 403

    data = request.get_json()
    patient = ICUPatient.query.get_or_404(data['patient_id'])

    qsofa, risk, status = calculate_risk(data)

    vitals = ICUVitals(
        patient_id=patient.id,
        heart_rate=data.get('heart_rate'),
        systolic_bp=data.get('systolic_bp'),
        diastolic_bp=data.get('diastolic_bp'),
        temperature=data.get('temperature'),
        respiratory_rate=data.get('respiratory_rate'),
        spo2=data.get('spo2'),
        gcs=data.get('gcs'),
        wbc_count=data.get('wbc_count'),
        lactate=data.get('lactate'),
        urine_output_ml=data.get('urine_output_ml'),
        risk_score=risk,
        qsofa_score=qsofa,
        recorded_by=data.get('recorded_by', 'Nurse'),
    )
    db.session.add(vitals)

    patient.risk_score = risk
    patient.qsofa_score = qsofa
    patient.status = status

    alert_sent = False
    if risk >= 70:
        alert = ICUAlert(
            patient_id=patient.id,
            risk_score=risk,
            alert_type='SEPSIS',
            message=f"HIGH RISK SEPSIS - Patient {patient.patient_name}, Bed {patient.bed_number}, Score {risk}/100",
            sent_to=patient.doctor_phone,
        )
        db.session.add(alert)

        if patient.doctor_phone:
            sent = send_icu_alert(
                patient.doctor_phone,
                patient.patient_name,
                patient.bed_number,
                risk, qsofa,
                datetime.utcnow().strftime('%Y-%m-%d %H:%M IST')
            )
            alert.whatsapp_sent = sent
        alert_sent = True

    db.session.commit()

    recs = get_recommendations(risk, qsofa, data)
    return jsonify(success_response({
        'risk_score': risk,
        'qsofa_score': qsofa,
        'status': status,
        'alert_sent': alert_sent,
        'recommendations': recs,
        'vitals_id': vitals.id,
    }, "Vitals recorded"))


@icu_bp.route('/patient/<int:pid>/vitals-history', methods=['GET'])
@jwt_required()
def vitals_history(pid):
    since = datetime.utcnow() - timedelta(hours=24)
    vitals = ICUVitals.query.filter(
        ICUVitals.patient_id == pid,
        ICUVitals.recorded_at >= since
    ).order_by(ICUVitals.recorded_at.asc()).all()
    return jsonify(success_response([v.to_dict() for v in vitals]))


@icu_bp.route('/alerts', methods=['GET'])
@jwt_required()
def get_alerts():
    claims = get_jwt()
    hospital_id = claims.get('hospital_id') or request.args.get('hospital_id', type=int)
    patients = ICUPatient.query.filter_by(hospital_id=hospital_id).all()
    patient_ids = [p.id for p in patients]
    alerts = ICUAlert.query.filter(ICUAlert.patient_id.in_(patient_ids)).order_by(ICUAlert.created_at.desc()).all()
    return jsonify(success_response([a.to_dict() for a in alerts]))


@icu_bp.route('/alert/<int:aid>/respond', methods=['PUT'])
@jwt_required()
def respond_alert(aid):
    alert = ICUAlert.query.get_or_404(aid)
    alert.response_received = True
    db.session.commit()
    return jsonify(success_response({}, "Alert marked as responded"))


@icu_bp.route('/stats', methods=['GET'])
@jwt_required()
def icu_stats():
    claims = get_jwt()
    hospital_id = claims.get('hospital_id') or request.args.get('hospital_id', type=int)
    patients = ICUPatient.query.filter_by(hospital_id=hospital_id, is_active=True).all()
    total = len(patients)
    critical = sum(1 for p in patients if p.status == 'critical')
    moderate = sum(1 for p in patients if p.status == 'moderate')
    stable = sum(1 for p in patients if p.status == 'stable')

    today = datetime.utcnow().date()
    patient_ids = [p.id for p in patients]
    alerts_today = ICUAlert.query.filter(
        ICUAlert.patient_id.in_(patient_ids),
        db.func.date(ICUAlert.created_at) == today
    ).count()

    return jsonify(success_response({
        'total_patients': total,
        'critical': critical,
        'moderate': moderate,
        'stable': stable,
        'alerts_today': alerts_today,
    }))
