# -*- coding: utf-8 -*-
import json
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from werkzeug.security import generate_password_hash
from database.models import db, Hospital, BedBooking
from utils import validate_gst, validate_phone, haversine, success_response, error_response, generate_booking_id
from utils.whatsapp import send_bed_booking_confirmation, send_hospital_registration_notification

hospitals_bp = Blueprint('hospitals', __name__)


@hospitals_bp.route('/register', methods=['POST'])
def register_hospital():
    data = request.get_json()
    required = ['name', 'type', 'registration_no', 'gst_number', 'contact_person', 'phone', 'password', 'address']
    for field in required:
        if not data.get(field):
            return jsonify(error_response(f"Field '{field}' is required")[0]), 400

    ok, msg = validate_gst(data['gst_number'])
    if not ok:
        return jsonify(error_response(msg)[0]), 400

    ok, msg = validate_phone(data['phone'])
    if not ok:
        return jsonify(error_response(msg)[0]), 400

    if Hospital.query.filter_by(gst_number=data['gst_number'].upper()).first():
        return jsonify(error_response("GST number already registered")[0]), 409
    if Hospital.query.filter_by(registration_no=data['registration_no']).first():
        return jsonify(error_response("Registration number already registered")[0]), 409

    specialties = data.get('specialties', [])
    insurance = data.get('insurance_accepted', [])

    h = Hospital(
        name=data['name'],
        type=data['type'],
        registration_no=data['registration_no'],
        gst_number=data['gst_number'].upper(),
        contact_person=data['contact_person'],
        phone=data['phone'],
        email=data.get('email', ''),
        address=data['address'],
        city=data.get('city', 'Barabanki'),
        state=data.get('state', 'Uttar Pradesh'),
        pincode=data.get('pincode', ''),
        lat=data.get('lat'),
        lng=data.get('lng'),
        specialties=json.dumps(specialties),
        insurance_accepted=json.dumps(insurance),
        password_hash=generate_password_hash(data['password']),
        icu_beds_total=data.get('icu_beds_total', 0),
        icu_beds_available=data.get('icu_beds_total', 0),
        general_beds_total=data.get('general_beds_total', 0),
        general_beds_available=data.get('general_beds_total', 0),
        emergency_beds_total=data.get('emergency_beds_total', 0),
        emergency_beds_available=data.get('emergency_beds_total', 0),
        maternity_beds_total=data.get('maternity_beds_total', 0),
        maternity_beds_available=data.get('maternity_beds_total', 0),
    )
    db.session.add(h)
    db.session.commit()

    send_hospital_registration_notification(
        '9453013645', data['name'], data['type'],
        data['gst_number'], data['contact_person'], data['phone'],
        data.get('city', 'Barabanki')
    )
    return jsonify(success_response(
        {'hospital_id': h.id},
        "Registration submitted. Admin will verify within 24 hours."
    ))


@hospitals_bp.route('/all', methods=['GET'])
def get_all_hospitals():
    hospitals = Hospital.query.filter_by(is_active=True, is_verified=True).all()
    return jsonify(success_response([h.to_dict() for h in hospitals]))


@hospitals_bp.route('/<int:hid>', methods=['GET'])
def get_hospital(hid):
    h = Hospital.query.get_or_404(hid)
    return jsonify(success_response(h.to_dict()))


@hospitals_bp.route('/beds', methods=['PUT'])
@jwt_required()
def update_beds():
    claims = get_jwt()
    if claims.get('role') != 'hospital':
        return jsonify(error_response("Unauthorized")[0]), 403

    hospital_id = claims.get('hospital_id')
    h = Hospital.query.get_or_404(hospital_id)
    data = request.get_json()

    if 'icu_available' in data:
        h.icu_beds_available = min(data['icu_available'], h.icu_beds_total)
    if 'general_available' in data:
        h.general_beds_available = min(data['general_available'], h.general_beds_total)
    if 'emergency_available' in data:
        h.emergency_beds_available = min(data['emergency_available'], h.emergency_beds_total)
    if 'maternity_available' in data:
        h.maternity_beds_available = min(data['maternity_available'], h.maternity_beds_total)

    h.last_bed_update = datetime.utcnow()
    db.session.commit()
    return jsonify(success_response(h.to_dict(), "Bed counts updated"))


@hospitals_bp.route('/search', methods=['GET'])
def search_hospitals():
    lat = request.args.get('lat', 26.9270, type=float)
    lng = request.args.get('lng', 81.1989, type=float)
    bed_type = request.args.get('bed_type', '')
    insurance = request.args.get('insurance', '')
    specialty = request.args.get('specialty', '')
    radius = request.args.get('radius', 30, type=float)

    hospitals = Hospital.query.filter_by(is_active=True, is_verified=True).all()
    result = []
    for h in hospitals:
        if h.lat and h.lng:
            dist = haversine(lat, lng, h.lat, h.lng)
            if dist > radius:
                continue
            if bed_type:
                avail_map = {
                    'icu': h.icu_beds_available,
                    'general': h.general_beds_available,
                    'emergency': h.emergency_beds_available,
                    'maternity': h.maternity_beds_available,
                }
                if avail_map.get(bed_type, 0) <= 0:
                    continue
            if specialty:
                specs = json.loads(h.specialties) if h.specialties else []
                if not any(specialty.lower() in s.lower() for s in specs):
                    continue
            if insurance:
                ins_list = json.loads(h.insurance_accepted) if h.insurance_accepted else []
                if not any(insurance.lower() in i.lower() for i in ins_list):
                    continue
            result.append(h.to_dict(distance_km=dist))

    result.sort(key=lambda x: x['distance_km'])
    return jsonify(success_response(result))


@hospitals_bp.route('/bed/book', methods=['POST'])
def book_bed():
    data = request.get_json()
    required = ['hospital_id', 'bed_type', 'patient_name', 'patient_phone', 'patient_age']
    for field in required:
        if not data.get(field):
            return jsonify(error_response(f"Field '{field}' is required")[0]), 400

    h = Hospital.query.get_or_404(data['hospital_id'])
    bed_type = data['bed_type']

    avail_map = {
        'icu': h.icu_beds_available,
        'general': h.general_beds_available,
        'emergency': h.emergency_beds_available,
        'maternity': h.maternity_beds_available,
    }
    if avail_map.get(bed_type, 0) <= 0:
        return jsonify(error_response(f"No {bed_type} beds available")[0]), 400

    # Decrease available count
    if bed_type == 'icu':
        h.icu_beds_available -= 1
    elif bed_type == 'general':
        h.general_beds_available -= 1
    elif bed_type == 'emergency':
        h.emergency_beds_available -= 1
    elif bed_type == 'maternity':
        h.maternity_beds_available -= 1

    booking_id = generate_booking_id('BED')
    booking = BedBooking(
        booking_id=booking_id,
        hospital_id=h.id,
        bed_type=bed_type,
        patient_name=data['patient_name'],
        patient_phone=data['patient_phone'],
        patient_age=data['patient_age'],
        diagnosis=data.get('diagnosis', ''),
        insurance_type=data.get('insurance_type', 'Cash'),
        status='Confirmed'
    )
    db.session.add(booking)
    db.session.commit()

    send_bed_booking_confirmation(
        data['patient_phone'], booking_id, h.name, bed_type, data['patient_name']
    )
    return jsonify(success_response(booking.to_dict(), f"Bed booked! ID: {booking_id}"))


@hospitals_bp.route('/bookings', methods=['GET'])
@jwt_required()
def get_hospital_bookings():
    claims = get_jwt()
    if claims.get('role') != 'hospital':
        return jsonify(error_response("Unauthorized")[0]), 403
    hospital_id = claims.get('hospital_id')
    bookings = BedBooking.query.filter_by(hospital_id=hospital_id).order_by(BedBooking.created_at.desc()).all()
    return jsonify(success_response([b.to_dict() for b in bookings]))


@hospitals_bp.route('/booking/<int:bid>/status', methods=['PUT'])
@jwt_required()
def update_booking_status(bid):
    claims = get_jwt()
    if claims.get('role') != 'hospital':
        return jsonify(error_response("Unauthorized")[0]), 403
    data = request.get_json()
    booking = BedBooking.query.get_or_404(bid)
    booking.status = data.get('status', booking.status)
    if data.get('status') == 'Admitted':
        booking.admitted_at = datetime.utcnow()
    elif data.get('status') == 'Discharged':
        booking.discharged_at = datetime.utcnow()
        h = Hospital.query.get(booking.hospital_id)
        if booking.bed_type == 'icu':
            h.icu_beds_available = min(h.icu_beds_available + 1, h.icu_beds_total)
        elif booking.bed_type == 'general':
            h.general_beds_available = min(h.general_beds_available + 1, h.general_beds_total)
    db.session.commit()
    return jsonify(success_response(booking.to_dict(), "Status updated"))
