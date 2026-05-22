# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(10), unique=True, nullable=False)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), nullable=True)
    blood_group = db.Column(db.String(5))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    insurance_type = db.Column(db.String(50))
    emergency_contact_name = db.Column(db.String(100))
    emergency_contact_phone = db.Column(db.String(10))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    bookings = db.relationship('BedBooking', backref='user', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'phone': self.phone,
            'name': self.name,
            'email': self.email,
            'blood_group': self.blood_group,
            'age': self.age,
            'gender': self.gender,
            'insurance_type': self.insurance_type,
        }


class OTP(db.Model):
    __tablename__ = 'otps'
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(10), nullable=False)
    otp_code = db.Column(db.String(6), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    is_used = db.Column(db.Boolean, default=False)

    def __init__(self, phone, otp_code):
        self.phone = phone
        self.otp_code = otp_code
        self.expires_at = datetime.utcnow() + timedelta(minutes=10)


class Hospital(db.Model):
    __tablename__ = 'hospitals'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(20))
    registration_no = db.Column(db.String(50), unique=True)
    gst_number = db.Column(db.String(15), unique=True)
    contact_person = db.Column(db.String(100))
    phone = db.Column(db.String(10))
    email = db.Column(db.String(100))
    address = db.Column(db.String(300))
    city = db.Column(db.String(50), default='Barabanki')
    state = db.Column(db.String(50), default='Uttar Pradesh')
    pincode = db.Column(db.String(6))
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    specialties = db.Column(db.String(500))
    insurance_accepted = db.Column(db.String(500))
    is_verified = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    password_hash = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    icu_beds_total = db.Column(db.Integer, default=0)
    icu_beds_available = db.Column(db.Integer, default=0)
    general_beds_total = db.Column(db.Integer, default=0)
    general_beds_available = db.Column(db.Integer, default=0)
    emergency_beds_total = db.Column(db.Integer, default=0)
    emergency_beds_available = db.Column(db.Integer, default=0)
    maternity_beds_total = db.Column(db.Integer, default=0)
    maternity_beds_available = db.Column(db.Integer, default=0)
    rating = db.Column(db.Float, default=0.0)
    total_reviews = db.Column(db.Integer, default=0)
    last_bed_update = db.Column(db.DateTime)

    def to_dict(self, distance_km=None):
        import json
        d = {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'registration_no': self.registration_no,
            'contact_person': self.contact_person,
            'phone': self.phone,
            'email': self.email,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'pincode': self.pincode,
            'lat': self.lat,
            'lng': self.lng,
            'specialties': json.loads(self.specialties) if self.specialties else [],
            'insurance_accepted': json.loads(self.insurance_accepted) if self.insurance_accepted else [],
            'is_verified': self.is_verified,
            'is_active': self.is_active,
            'icu_beds_total': self.icu_beds_total,
            'icu_beds_available': self.icu_beds_available,
            'general_beds_total': self.general_beds_total,
            'general_beds_available': self.general_beds_available,
            'emergency_beds_total': self.emergency_beds_total,
            'emergency_beds_available': self.emergency_beds_available,
            'maternity_beds_total': self.maternity_beds_total,
            'maternity_beds_available': self.maternity_beds_available,
            'rating': self.rating,
            'total_reviews': self.total_reviews,
            'last_bed_update': self.last_bed_update.isoformat() if self.last_bed_update else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        if distance_km is not None:
            d['distance_km'] = round(distance_km, 1)
        return d


class Lab(db.Model):
    __tablename__ = 'labs'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    accreditation = db.Column(db.String(50))
    registration_no = db.Column(db.String(50), unique=True)
    gst_number = db.Column(db.String(15), unique=True)
    contact_person = db.Column(db.String(100))
    phone = db.Column(db.String(10))
    email = db.Column(db.String(100))
    address = db.Column(db.String(300))
    city = db.Column(db.String(50))
    pincode = db.Column(db.String(6))
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    home_collection = db.Column(db.Boolean, default=True)
    collection_charge = db.Column(db.Integer, default=50)
    report_whatsapp = db.Column(db.Boolean, default=True)
    timings = db.Column(db.String(100))
    coverage_radius_km = db.Column(db.Integer, default=10)
    is_verified = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    password_hash = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    rating = db.Column(db.Float, default=0.0)
    tests = db.relationship('Test', backref='lab', lazy=True)

    def to_dict(self, distance_km=None):
        d = {
            'id': self.id,
            'name': self.name,
            'accreditation': self.accreditation,
            'contact_person': self.contact_person,
            'phone': self.phone,
            'address': self.address,
            'city': self.city,
            'home_collection': self.home_collection,
            'collection_charge': self.collection_charge,
            'timings': self.timings,
            'coverage_radius_km': self.coverage_radius_km,
            'is_verified': self.is_verified,
            'rating': self.rating,
        }
        if distance_km is not None:
            d['distance_km'] = round(distance_km, 1)
        return d


class Test(db.Model):
    __tablename__ = 'tests'
    id = db.Column(db.Integer, primary_key=True)
    lab_id = db.Column(db.Integer, db.ForeignKey('labs.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50))
    price = db.Column(db.Integer, nullable=False)
    tat_hours = db.Column(db.Integer)
    fasting = db.Column(db.Boolean, default=False)
    description = db.Column(db.String(500))
    normal_range = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            'id': self.id,
            'lab_id': self.lab_id,
            'lab_name': self.lab.name if self.lab else None,
            'name': self.name,
            'category': self.category,
            'price': self.price,
            'tat_hours': self.tat_hours,
            'fasting': self.fasting,
            'description': self.description,
            'normal_range': self.normal_range,
        }


class Ambulance(db.Model):
    __tablename__ = 'ambulances'
    id = db.Column(db.Integer, primary_key=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id'), nullable=True)
    driver_name = db.Column(db.String(100), nullable=False)
    driver_phone = db.Column(db.String(10), nullable=False)
    vehicle_no = db.Column(db.String(20), nullable=False, unique=True)
    type = db.Column(db.String(20))
    equipment = db.Column(db.String(500))
    base_fare = db.Column(db.Integer)
    per_km_fare = db.Column(db.Integer)
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    status = db.Column(db.String(20), default='available')
    rating = db.Column(db.Float, default=5.0)
    total_trips = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    last_location_update = db.Column(db.DateTime)

    def to_dict(self, distance_km=None, eta_min=None):
        d = {
            'id': self.id,
            'driver_name': self.driver_name,
            'driver_phone': self.driver_phone,
            'vehicle_no': self.vehicle_no,
            'type': self.type,
            'base_fare': self.base_fare,
            'per_km_fare': self.per_km_fare,
            'lat': self.lat,
            'lng': self.lng,
            'status': self.status,
            'rating': self.rating,
            'total_trips': self.total_trips,
        }
        if distance_km is not None:
            d['distance_km'] = round(distance_km, 1)
        if eta_min is not None:
            d['eta_min'] = eta_min
        return d


class BedBooking(db.Model):
    __tablename__ = 'bed_bookings'
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.String(20), unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id'))
    bed_type = db.Column(db.String(20))
    patient_name = db.Column(db.String(100))
    patient_phone = db.Column(db.String(10))
    patient_age = db.Column(db.Integer)
    diagnosis = db.Column(db.String(300))
    insurance_type = db.Column(db.String(50))
    status = db.Column(db.String(20), default='Confirmed')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    admitted_at = db.Column(db.DateTime, nullable=True)
    discharged_at = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.String(500))
    hospital = db.relationship('Hospital', backref='bed_bookings')

    def to_dict(self):
        return {
            'id': self.id,
            'booking_id': self.booking_id,
            'hospital_name': self.hospital.name if self.hospital else None,
            'bed_type': self.bed_type,
            'patient_name': self.patient_name,
            'patient_phone': self.patient_phone,
            'patient_age': self.patient_age,
            'diagnosis': self.diagnosis,
            'insurance_type': self.insurance_type,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class LabBooking(db.Model):
    __tablename__ = 'lab_bookings'
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.String(20), unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    lab_id = db.Column(db.Integer, db.ForeignKey('labs.id'))
    patient_name = db.Column(db.String(100))
    patient_phone = db.Column(db.String(10))
    address = db.Column(db.String(300))
    slot_date = db.Column(db.Date)
    slot_time = db.Column(db.String(50))
    status = db.Column(db.String(30), default='Booked')
    technician_name = db.Column(db.String(100), nullable=True)
    report_url = db.Column(db.String(300), nullable=True)
    total_amount = db.Column(db.Integer)
    payment_status = db.Column(db.String(20), default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    lab = db.relationship('Lab', backref='bookings')
    items = db.relationship('LabBookingItem', backref='booking', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'booking_id': self.booking_id,
            'lab_name': self.lab.name if self.lab else None,
            'patient_name': self.patient_name,
            'patient_phone': self.patient_phone,
            'address': self.address,
            'slot_date': self.slot_date.isoformat() if self.slot_date else None,
            'slot_time': self.slot_time,
            'status': self.status,
            'total_amount': self.total_amount,
            'payment_status': self.payment_status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'items': [i.to_dict() for i in self.items],
        }


class LabBookingItem(db.Model):
    __tablename__ = 'lab_booking_items'
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('lab_bookings.id'))
    test_id = db.Column(db.Integer, db.ForeignKey('tests.id'))
    test_name = db.Column(db.String(200))
    price = db.Column(db.Integer)

    def to_dict(self):
        return {'test_name': self.test_name, 'price': self.price}


class AmbulanceBooking(db.Model):
    __tablename__ = 'ambulance_bookings'
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.String(20), unique=True)
    ambulance_id = db.Column(db.Integer, db.ForeignKey('ambulances.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    patient_name = db.Column(db.String(100))
    patient_phone = db.Column(db.String(10))
    pickup_lat = db.Column(db.Float)
    pickup_lng = db.Column(db.Float)
    pickup_address = db.Column(db.String(300))
    dest_hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id'), nullable=True)
    dest_address = db.Column(db.String(300))
    distance_km = db.Column(db.Float)
    base_fare = db.Column(db.Integer)
    total_fare = db.Column(db.Integer)
    amb_type = db.Column(db.String(20))
    status = db.Column(db.String(20), default='Confirmed')
    payment_method = db.Column(db.String(20))
    payment_status = db.Column(db.String(20), default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    ambulance = db.relationship('Ambulance', backref='bookings')

    def to_dict(self):
        return {
            'id': self.id,
            'booking_id': self.booking_id,
            'patient_name': self.patient_name,
            'patient_phone': self.patient_phone,
            'pickup_address': self.pickup_address,
            'dest_address': self.dest_address,
            'distance_km': self.distance_km,
            'total_fare': self.total_fare,
            'amb_type': self.amb_type,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'driver_name': self.ambulance.driver_name if self.ambulance else None,
            'driver_phone': self.ambulance.driver_phone if self.ambulance else None,
            'vehicle_no': self.ambulance.vehicle_no if self.ambulance else None,
        }


class ICUPatient(db.Model):
    __tablename__ = 'icu_patients'
    id = db.Column(db.Integer, primary_key=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id'))
    bed_number = db.Column(db.String(20))
    patient_name = db.Column(db.String(100))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(5))
    diagnosis = db.Column(db.String(200))
    admitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    doctor_name = db.Column(db.String(100))
    doctor_phone = db.Column(db.String(10))
    risk_score = db.Column(db.Integer, default=0)
    qsofa_score = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='stable')
    is_active = db.Column(db.Boolean, default=True)
    vitals = db.relationship('ICUVitals', backref='patient', lazy=True, order_by='ICUVitals.recorded_at.desc()')
    alerts = db.relationship('ICUAlert', backref='patient', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'bed_number': self.bed_number,
            'patient_name': self.patient_name,
            'age': self.age,
            'gender': self.gender,
            'diagnosis': self.diagnosis,
            'admitted_at': self.admitted_at.isoformat() if self.admitted_at else None,
            'doctor_name': self.doctor_name,
            'doctor_phone': self.doctor_phone,
            'risk_score': self.risk_score,
            'qsofa_score': self.qsofa_score,
            'status': self.status,
        }


class ICUVitals(db.Model):
    __tablename__ = 'icu_vitals'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('icu_patients.id'))
    heart_rate = db.Column(db.Integer)
    systolic_bp = db.Column(db.Integer)
    diastolic_bp = db.Column(db.Integer)
    temperature = db.Column(db.Float)
    respiratory_rate = db.Column(db.Integer)
    spo2 = db.Column(db.Integer)
    gcs = db.Column(db.Integer)
    wbc_count = db.Column(db.Float, nullable=True)
    lactate = db.Column(db.Float, nullable=True)
    urine_output_ml = db.Column(db.Integer, nullable=True)
    risk_score = db.Column(db.Integer)
    qsofa_score = db.Column(db.Integer)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)
    recorded_by = db.Column(db.String(100))

    def to_dict(self):
        return {
            'id': self.id,
            'heart_rate': self.heart_rate,
            'systolic_bp': self.systolic_bp,
            'diastolic_bp': self.diastolic_bp,
            'temperature': self.temperature,
            'respiratory_rate': self.respiratory_rate,
            'spo2': self.spo2,
            'gcs': self.gcs,
            'wbc_count': self.wbc_count,
            'lactate': self.lactate,
            'risk_score': self.risk_score,
            'qsofa_score': self.qsofa_score,
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None,
            'recorded_by': self.recorded_by,
        }


class ICUAlert(db.Model):
    __tablename__ = 'icu_alerts'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('icu_patients.id'))
    risk_score = db.Column(db.Integer)
    alert_type = db.Column(db.String(50))
    message = db.Column(db.String(300))
    sent_to = db.Column(db.String(100))
    whatsapp_sent = db.Column(db.Boolean, default=False)
    response_received = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'risk_score': self.risk_score,
            'alert_type': self.alert_type,
            'message': self.message,
            'sent_to': self.sent_to,
            'whatsapp_sent': self.whatsapp_sent,
            'response_received': self.response_received,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class Review(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    entity_type = db.Column(db.String(20))
    entity_id = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    rating = db.Column(db.Integer)
    comment = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
class LabReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    patient_name = db.Column(db.String(100))

    filename = db.Column(db.String(200))

    extracted_text = db.Column(db.Text)

    ai_response = db.Column(db.Text)

    language = db.Column(db.String(20))