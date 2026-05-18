# -*- coding: utf-8 -*-
import random
import os
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from werkzeug.security import check_password_hash
from database.models import db, User, OTP, Hospital, Lab
from utils import validate_phone, success_response, error_response
from utils.whatsapp import send_whatsapp

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/patient/send-otp', methods=['POST'])
def send_otp():
    data = request.get_json()
    phone = data.get('phone', '').strip()

    ok, msg = validate_phone(phone)
    if not ok:
        return jsonify(error_response(msg)[0]), 400

    otp_code = str(random.randint(100000, 999999))
    otp = OTP(phone=phone, otp_code=otp_code)
    db.session.add(otp)
    db.session.commit()

    print(f"[OTP] Phone: {phone} | Code: {otp_code}")
    send_whatsapp(phone, f"*AyuRaksha OTP*\nYour login OTP is: {otp_code}\nValid for 10 minutes.\nDo not share with anyone.")

    return jsonify(success_response(message="OTP sent successfully"))


@auth_bp.route('/patient/verify-otp', methods=['POST'])
def verify_otp():
    data = request.get_json()
    phone = data.get('phone', '').strip()
    otp_code = data.get('otp', '').strip()

    otp = OTP.query.filter_by(phone=phone, otp_code=otp_code, is_used=False).order_by(OTP.created_at.desc()).first()

    if not otp:
        return jsonify(error_response("Invalid OTP")[0]), 401
    if datetime.utcnow() > otp.expires_at:
        return jsonify(error_response("OTP expired. Please request a new one.")[0]), 401

    otp.is_used = True
    db.session.commit()

    user = User.query.filter_by(phone=phone).first()
    if not user:
        user = User(phone=phone)
        db.session.add(user)
        db.session.commit()

    token = create_access_token(identity=str(user.id), additional_claims={'role': 'patient', 'user_id': user.id})
    return jsonify(success_response({'token': token, 'user': user.to_dict()}, "Login successful"))


@auth_bp.route('/hospital/login', methods=['POST'])
def hospital_login():
    data = request.get_json()
    phone = data.get('phone', '').strip()
    password = data.get('password', '')

    hospital = Hospital.query.filter_by(phone=phone, is_active=True).first()
    if not hospital:
        return jsonify(error_response("Hospital not found")[0]), 404
    if not check_password_hash(hospital.password_hash, password):
        return jsonify(error_response("Invalid password")[0]), 401
    if not hospital.is_verified:
        return jsonify(error_response("Your hospital is pending admin verification.")[0]), 403

    token = create_access_token(identity=str(hospital.id), additional_claims={'role': 'hospital', 'hospital_id': hospital.id})
    return jsonify(success_response({'token': token, 'hospital': hospital.to_dict()}, "Login successful"))


@auth_bp.route('/lab/login', methods=['POST'])
def lab_login():
    data = request.get_json()
    phone = data.get('phone', '').strip()
    password = data.get('password', '')

    lab = Lab.query.filter_by(phone=phone, is_active=True).first()
    if not lab:
        return jsonify(error_response("Lab not found")[0]), 404
    if not check_password_hash(lab.password_hash, password):
        return jsonify(error_response("Invalid password")[0]), 401

    token = create_access_token(identity=str(lab.id), additional_claims={'role': 'lab', 'lab_id': lab.id})
    return jsonify(success_response({'token': token, 'lab': lab.to_dict()}, "Login successful"))


@auth_bp.route('/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    username = data.get('username', '')
    password = data.get('password', '')

    if username != os.getenv('ADMIN_USERNAME', 'admin') or password != os.getenv('ADMIN_PASSWORD', 'ayuraksha@2026'):
        return jsonify(error_response("Invalid credentials")[0]), 401

    token = create_access_token(identity='admin', additional_claims={'role': 'superadmin'})
    return jsonify(success_response({'token': token}, "Admin login successful"))
