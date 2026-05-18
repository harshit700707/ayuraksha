# -*- coding: utf-8 -*-
from datetime import datetime, date
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from database.models import db, Hospital, Lab, BedBooking, LabBooking, AmbulanceBooking, ICUPatient
from utils import success_response, error_response
from utils.whatsapp import send_hospital_verified

admin_bp = Blueprint('admin', __name__)


def require_admin():
    claims = get_jwt()
    if claims.get('role') != 'superadmin':
        return False
    return True


@admin_bp.route('/hospitals/pending', methods=['GET'])
@jwt_required()
def pending_hospitals():
    if not require_admin():
        return jsonify(error_response("Unauthorized")[0]), 403
    hospitals = Hospital.query.filter_by(is_verified=False, is_active=True).order_by(Hospital.created_at.desc()).all()
    return jsonify(success_response([h.to_dict() for h in hospitals]))


@admin_bp.route('/hospital/<int:hid>/verify', methods=['PUT'])
@jwt_required()
def verify_hospital(hid):
    if not require_admin():
        return jsonify(error_response("Unauthorized")[0]), 403
    h = Hospital.query.get_or_404(hid)
    h.is_verified = True
    db.session.commit()
    if h.phone:
        send_hospital_verified(h.phone, h.name)
    return jsonify(success_response(h.to_dict(), f"{h.name} verified successfully"))


@admin_bp.route('/hospital/<int:hid>/reject', methods=['PUT'])
@jwt_required()
def reject_hospital(hid):
    if not require_admin():
        return jsonify(error_response("Unauthorized")[0]), 403
    h = Hospital.query.get_or_404(hid)
    h.is_active = False
    db.session.commit()
    return jsonify(success_response({}, "Hospital registration rejected"))


@admin_bp.route('/labs/pending', methods=['GET'])
@jwt_required()
def pending_labs():
    if not require_admin():
        return jsonify(error_response("Unauthorized")[0]), 403
    labs = Lab.query.filter_by(is_verified=False, is_active=True).order_by(Lab.created_at.desc()).all()
    return jsonify(success_response([l.to_dict() for l in labs]))


@admin_bp.route('/lab/<int:lid>/verify', methods=['PUT'])
@jwt_required()
def verify_lab(lid):
    if not require_admin():
        return jsonify(error_response("Unauthorized")[0]), 403
    lab = Lab.query.get_or_404(lid)
    lab.is_verified = True
    db.session.commit()
    return jsonify(success_response(lab.to_dict(), f"{lab.name} verified successfully"))


@admin_bp.route('/stats', methods=['GET'])
@jwt_required()
def admin_stats():
    if not require_admin():
        return jsonify(error_response("Unauthorized")[0]), 403

    today = date.today()
    total_hospitals = Hospital.query.count()
    verified_hospitals = Hospital.query.filter_by(is_verified=True).count()
    total_labs = Lab.query.count()
    verified_labs = Lab.query.filter_by(is_verified=True).count()

    bed_bookings_today = BedBooking.query.filter(db.func.date(BedBooking.created_at) == today).count()
    lab_bookings_today = LabBooking.query.filter(db.func.date(LabBooking.created_at) == today).count()
    amb_bookings_today = AmbulanceBooking.query.filter(db.func.date(AmbulanceBooking.created_at) == today).count()
    total_bookings_today = bed_bookings_today + lab_bookings_today + amb_bookings_today

    total_amb = AmbulanceBooking.query.count()
    active_icu = ICUPatient.query.filter_by(is_active=True).count()
    critical_icu = ICUPatient.query.filter_by(is_active=True, status='critical').count()

    total_revenue = db.session.query(db.func.sum(LabBooking.total_amount)).scalar() or 0
    total_revenue += db.session.query(db.func.sum(AmbulanceBooking.total_fare)).scalar() or 0

    return jsonify(success_response({
        'total_hospitals': total_hospitals,
        'verified_hospitals': verified_hospitals,
        'pending_hospitals': total_hospitals - verified_hospitals,
        'total_labs': total_labs,
        'verified_labs': verified_labs,
        'pending_labs': total_labs - verified_labs,
        'total_bookings_today': total_bookings_today,
        'bed_bookings_today': bed_bookings_today,
        'lab_bookings_today': lab_bookings_today,
        'total_ambulance_bookings': total_amb,
        'total_revenue': total_revenue,
        'active_icu_patients': active_icu,
        'critical_icu_patients': critical_icu,
    }))


@admin_bp.route('/hospitals/all', methods=['GET'])
@jwt_required()
def all_hospitals():
    if not require_admin():
        return jsonify(error_response("Unauthorized")[0]), 403
    hospitals = Hospital.query.order_by(Hospital.created_at.desc()).all()
    return jsonify(success_response([h.to_dict() for h in hospitals]))


@admin_bp.route('/bookings/recent', methods=['GET'])
@jwt_required()
def recent_bookings():
    if not require_admin():
        return jsonify(error_response("Unauthorized")[0]), 403
    bed = BedBooking.query.order_by(BedBooking.created_at.desc()).limit(10).all()
    lab = LabBooking.query.order_by(LabBooking.created_at.desc()).limit(10).all()
    return jsonify(success_response({
        'bed_bookings': [b.to_dict() for b in bed],
        'lab_bookings': [b.to_dict() for b in lab],
    }))
