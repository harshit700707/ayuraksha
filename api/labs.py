# -*- coding: utf-8 -*-
import json
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from werkzeug.security import generate_password_hash
from database.models import db, Lab, Test, LabBooking, LabBookingItem
from utils import validate_gst, validate_phone, success_response, error_response, generate_booking_id
from utils.whatsapp import send_lab_booking_confirmation
import os
import pytesseract

from PIL import Image
from werkzeug.utils import secure_filename

from flask import request, render_template

from ai.report_analyzer import analyze_report

labs_bp = Blueprint('labs', __name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR,'..' ,'static','uploads')


@labs_bp.route('/upload-report', methods=['GET', 'POST'])
def upload_report():
    if request.method == 'POST':
        file = request.files['report']

        language = request.form.get('language')

        filename = secure_filename(file.filename)

        filepath = os.path.join(UPLOAD_FOLDER, filename)

        file.save(filepath)

        image = Image.open(filepath)

        extracted_text = pytesseract.image_to_string(image)

        ai_result = analyze_report(filepath, language)

        return render_template(
            'report_result.html',
            result=ai_result
        )
    return render_template('upload_report.html')



@labs_bp.route('/register', methods=['POST'])
def register_lab():
    data = request.get_json()
    required = ['name', 'registration_no', 'gst_number', 'contact_person', 'phone', 'password', 'address']
    for field in required:
        if not data.get(field):
            return jsonify(error_response(f"Field '{field}' is required")[0]), 400

    ok, msg = validate_gst(data['gst_number'])
    if not ok:
        return jsonify(error_response(msg)[0]), 400

    ok, msg = validate_phone(data['phone'])
    if not ok:
        return jsonify(error_response(msg)[0]), 400

    if Lab.query.filter_by(gst_number=data['gst_number'].upper()).first():
        return jsonify(error_response("GST number already registered")[0]), 409

    lab = Lab(
        name=data['name'],
        accreditation=data.get('accreditation', 'None'),
        registration_no=data['registration_no'],
        gst_number=data['gst_number'].upper(),
        contact_person=data['contact_person'],
        phone=data['phone'],
        email=data.get('email', ''),
        address=data['address'],
        city=data.get('city', 'Barabanki'),
        pincode=data.get('pincode', ''),
        lat=data.get('lat'),
        lng=data.get('lng'),
        home_collection=data.get('home_collection', True),
        collection_charge=data.get('collection_charge', 50),
        coverage_radius_km=data.get('coverage_radius_km', 10),
        timings=data.get('timings', '7 AM - 9 PM'),
        password_hash=generate_password_hash(data['password']),
    )
    db.session.add(lab)
    db.session.commit()
    return jsonify(success_response({'lab_id': lab.id}, "Lab registered. Admin will verify within 24 hours."))


@labs_bp.route('/tests', methods=['POST'])
@jwt_required()
def add_test():
    claims = get_jwt()
    if claims.get('role') != 'lab':
        return jsonify(error_response("Unauthorized")[0]), 403
    lab_id = claims.get('lab_id')
    data = request.get_json()
    test = Test(
        lab_id=lab_id,
        name=data['name'],
        category=data.get('category', 'General'),
        price=data['price'],
        tat_hours=data.get('tat_hours', 24),
        fasting=data.get('fasting', False),
        description=data.get('description', ''),
        normal_range=data.get('normal_range', ''),
    )
    db.session.add(test)
    db.session.commit()
    return jsonify(success_response(test.to_dict(), "Test added successfully"))


@labs_bp.route('/tests', methods=['GET'])
def get_tests():
    city = request.args.get('city', '')
    category = request.args.get('category', '')
    search = request.args.get('search', '')

    query = Test.query.join(Lab).filter(Lab.is_verified == True, Lab.is_active == True, Test.is_active == True)
    if category:
        query = query.filter(Test.category.ilike(f'%{category}%'))
    if search:
        query = query.filter(Test.name.ilike(f'%{search}%'))

    tests = query.all()
    return jsonify(success_response([t.to_dict() for t in tests]))


@labs_bp.route('/<int:lid>/tests', methods=['GET'])
def get_lab_tests(lid):
    tests = Test.query.filter_by(lab_id=lid, is_active=True).all()
    return jsonify(success_response([t.to_dict() for t in tests]))


@labs_bp.route('/book', methods=['POST'])
def book_lab():
    data = request.get_json()
    required = ['lab_id', 'test_ids', 'patient_name', 'patient_phone', 'slot_date', 'slot_time']
    for field in required:
        if not data.get(field):
            return jsonify(error_response(f"Field '{field}' is required")[0]), 400

    lab = Lab.query.get_or_404(data['lab_id'])
    test_ids = data['test_ids']
    tests = Test.query.filter(Test.id.in_(test_ids), Test.lab_id == lab.id).all()

    if not tests:
        return jsonify(error_response("No valid tests found")[0]), 400

    total = sum(t.price for t in tests) + (lab.collection_charge if lab.home_collection else 0)
    booking_id = generate_booking_id('LAB')

    from datetime import date
    slot_date = data['slot_date']
    if isinstance(slot_date, str):
        slot_date = date.fromisoformat(slot_date)

    booking = LabBooking(
        booking_id=booking_id,
        lab_id=lab.id,
        patient_name=data['patient_name'],
        patient_phone=data['patient_phone'],
        address=data.get('address', ''),
        slot_date=slot_date,
        slot_time=data['slot_time'],
        total_amount=total,
    )
    db.session.add(booking)
    db.session.flush()

    for t in tests:
        item = LabBookingItem(booking_id=booking.id, test_id=t.id, test_name=t.name, price=t.price)
        db.session.add(item)

    db.session.commit()

    test_names = ', '.join(t.name for t in tests)
    max_tat = max(t.tat_hours for t in tests)
    send_lab_booking_confirmation(
        data['patient_phone'], booking_id, test_names,
        str(slot_date), data['slot_time'], max_tat
    )
    return jsonify(success_response(booking.to_dict(), f"Lab booking confirmed! ID: {booking_id}"))


@labs_bp.route('/booking/<string:bid>/status', methods=['GET'])
def get_booking_status(bid):
    booking = LabBooking.query.filter_by(booking_id=bid).first_or_404()
    return jsonify(success_response(booking.to_dict()))


@labs_bp.route('/booking/<int:bid>/status', methods=['PUT'])
@jwt_required()
def update_booking_status(bid):
    claims = get_jwt()
    if claims.get('role') != 'lab':
        return jsonify(error_response("Unauthorized")[0]), 403
    data = request.get_json()
    booking = LabBooking.query.get_or_404(bid)
    booking.status = data.get('status', booking.status)
    if data.get('technician_name'):
        booking.technician_name = data['technician_name']
    db.session.commit()
    return jsonify(success_response(booking.to_dict(), "Status updated"))


@labs_bp.route('/report/explain', methods=['POST'])
def explain_report():
    data = request.get_json()
    test_name = data.get('test_name', '')
    value = data.get('value', '')
    unit = data.get('unit', '')

    explanations = {
        'hba1c': f"HbA1c {value}% matlab aapke last 3 mahine ka average blood sugar. 7% se upar diabetes control nahi hai. Doctor se milein.",
        'cbc': "CBC (Complete Blood Count) se blood cells ki count hoti hai. Anemia, infection ya platelet problems detect hote hain.",
        'creatinine': f"Creatinine {value} {unit} - kidney function test hai. High hone par kidney specialist se milein.",
        'thyroid': f"Thyroid test se thyroid gland ki activity pata chalti hai. Abnormal hone par endocrinologist se milein.",
    }

    key = test_name.lower().replace(' ', '')
    explanation = explanations.get(key, f"{test_name} ka result {value} {unit} hai. Iske baare mein apne doctor se samjhein.")
    return jsonify(success_response({'explanation': explanation, 'test': test_name, 'value': value}))
