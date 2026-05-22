# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from flask import Flask, render_template, jsonify
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_mail import Mail

from config import Config
from database.models import db
from auth.routes import auth_bp
from api.hospitals import hospitals_bp
from api.labs import labs_bp
from api.ambulance import ambulance_bp
from api.icuguard import icu_bp
from api.location import location_bp
from api.admin import admin_bp
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
JWTManager(app)
CORS(app, resources={r"/api/*": {"origins": "*"}, r"/auth/*": {"origins": "*"}})
mail = Mail(app)

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(hospitals_bp, url_prefix='/api/hospital')
app.register_blueprint(labs_bp, url_prefix='/api/lab')
app.register_blueprint(ambulance_bp, url_prefix='/api/ambulance')
app.register_blueprint(icu_bp, url_prefix='/api/icu')
app.register_blueprint(location_bp, url_prefix='/api/location')
app.register_blueprint(admin_bp, url_prefix='/api/admin')


# ── Page Routes ────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/bedfinder')
def bedfinder():
    return render_template('bedfinder.html')

@app.route('/labconnect')
def labconnect():
    return render_template('labconnect.html')

@app.route('/ambulance')
def ambulance():
    return render_template('ambulance.html')

@app.route('/icuguard')
def icuguard():
    return render_template('icuguard.html')

@app.route('/patient/login')
def patient_login():
    return render_template('patient/login.html')

@app.route('/patient/dashboard')
def patient_dashboard():
    return render_template('patient/dashboard.html')

@app.route('/hospital/register')
def hospital_register():
    return render_template('hospital/register.html')

@app.route('/hospital/dashboard')
def hospital_dashboard():
    return render_template('hospital/dashboard.html')

@app.route('/lab/register')
def lab_register():
    return render_template('lab/register.html')

@app.route('/lab/dashboard')
def lab_dashboard():
    return render_template('lab/dashboard.html')

@app.route('/admin')
def admin_login_page():
    return render_template('admin/login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    return render_template('admin/dashboard.html')

@app.route('/api/stats')
def platform_stats():
    from database.models import Hospital, Lab, Ambulance
    return jsonify({
        'success': True,
        'data': {
            'hospitals': Hospital.query.filter_by(is_verified=True, is_active=True).count(),
            'labs': Lab.query.filter_by(is_verified=True, is_active=True).count(),
            'ambulances': Ambulance.query.filter_by(status='available', is_active=True).count(),
            'tests': 0,
        }
    })


def seed_demo_data():
    """Seed demo hospitals, labs, and ambulances for pitch demo."""
    from database.models import Hospital, Lab, Test, Ambulance
    from werkzeug.security import generate_password_hash
    import json

    if Hospital.query.count() > 0:
        return

    print("[SEED] Adding demo hospitals...")
    hospitals = [
        Hospital(
            name="Arya Hospital Barabanki",
            type="Private",
            registration_no="UP-2019-12345",
            gst_number="09AABCU9603R1ZX",
            contact_person="Dr. Rohit Agarwal",
            phone="9453013645",
            email="arya@hospital.com",
            address="Chowdhary Nagar, Barabanki",
            city="Barabanki",
            state="Uttar Pradesh",
            pincode="225001",
            lat=26.9270, lng=81.1989,
            specialties=json.dumps(["Orthopaedics", "Dental", "ICU", "General Surgery"]),
            insurance_accepted=json.dumps(["Ayushman Bharat", "Cash", "UPI"]),
            password_hash=generate_password_hash("hospital@123"),
            icu_beds_total=10, icu_beds_available=7,
            general_beds_total=50, general_beds_available=32,
            emergency_beds_total=8, emergency_beds_available=5,
            maternity_beds_total=15, maternity_beds_available=10,
            is_verified=True, rating=4.5, total_reviews=128,
        ),
        Hospital(
            name="District Hospital Barabanki",
            type="Government",
            registration_no="UP-GOVT-2001-001",
            gst_number="09GOVTH1234A1ZX",
            contact_person="Dr. Suresh Verma",
            phone="9876500001",
            email="dh@barabanki.gov.in",
            address="Civil Lines, Barabanki",
            city="Barabanki",
            state="Uttar Pradesh",
            pincode="225001",
            lat=26.9310, lng=81.2050,
            specialties=json.dumps(["General Medicine", "Surgery", "Gynaecology", "Paediatrics", "ICU"]),
            insurance_accepted=json.dumps(["Ayushman Bharat", "PMJAY", "ESI", "CGHS", "Cash"]),
            password_hash=generate_password_hash("govt@123"),
            icu_beds_total=20, icu_beds_available=3,
            general_beds_total=200, general_beds_available=45,
            emergency_beds_total=15, emergency_beds_available=8,
            maternity_beds_total=30, maternity_beds_available=12,
            is_verified=True, rating=3.8, total_reviews=342,
        ),
        Hospital(
            name="Lifeline Multispeciality Hospital",
            type="Private",
            registration_no="UP-2021-67890",
            gst_number="09LLMSH7654B1ZX",
            contact_person="Dr. Parul Tandon",
            phone="9876500002",
            email="lifeline@barabanki.com",
            address="Ram Nagar Colony, Barabanki",
            city="Barabanki",
            state="Uttar Pradesh",
            pincode="225001",
            lat=26.9200, lng=81.1900,
            specialties=json.dumps(["Cardiology", "Neurology", "Oncology", "ICU", "Trauma"]),
            insurance_accepted=json.dumps(["Star Health", "New India", "Private Insurance", "Cash", "UPI"]),
            password_hash=generate_password_hash("lifeline@123"),
            icu_beds_total=15, icu_beds_available=9,
            general_beds_total=80, general_beds_available=55,
            emergency_beds_total=10, emergency_beds_available=6,
            maternity_beds_total=20, maternity_beds_available=15,
            is_verified=True, rating=4.7, total_reviews=89,
        ),
    ]
    for h in hospitals:
        db.session.add(h)
    db.session.flush()

    print("[SEED] Adding demo labs...")
    lab1 = Lab(
        name="SRL Diagnostics Barabanki",
        accreditation="NABL",
        registration_no="LAB-UP-2020-456",
        gst_number="09SRLDB9876C1ZX",
        contact_person="Ramesh Kumar",
        phone="9000000000",
        email="srl@barabanki.com",
        address="Civil Lines, Barabanki",
        city="Barabanki",
        pincode="225001",
        lat=26.9280, lng=81.2010,
        home_collection=True,
        collection_charge=50,
        coverage_radius_km=15,
        timings="7 AM - 9 PM",
        password_hash=generate_password_hash("lab@123"),
        is_verified=True,
        rating=4.6,
    )
    lab2 = Lab(
        name="Pathcare Labs",
        accreditation="ISO",
        registration_no="LAB-UP-2019-123",
        gst_number="09PATHC4567D1ZX",
        contact_person="Sunita Gupta",
        phone="9800000001",
        email="pathcare@barabanki.com",
        address="Station Road, Barabanki",
        city="Barabanki",
        pincode="225001",
        lat=26.9350, lng=81.1950,
        home_collection=True,
        collection_charge=30,
        coverage_radius_km=10,
        timings="6 AM - 8 PM",
        password_hash=generate_password_hash("lab@123"),
        is_verified=True,
        rating=4.3,
    )
    db.session.add(lab1)
    db.session.add(lab2)
    db.session.flush()

    tests = [
        Test(lab_id=lab1.id, name="Complete Blood Count (CBC)", category="Haematology", price=200, tat_hours=6, fasting=False),
        Test(lab_id=lab1.id, name="HbA1c (Glycated Haemoglobin)", category="Diabetes", price=350, tat_hours=12, fasting=False),
        Test(lab_id=lab1.id, name="Thyroid Profile (T3, T4, TSH)", category="Thyroid", price=450, tat_hours=24, fasting=False),
        Test(lab_id=lab1.id, name="Lipid Profile", category="Cardiac", price=300, tat_hours=12, fasting=True),
        Test(lab_id=lab1.id, name="Liver Function Test (LFT)", category="Liver", price=400, tat_hours=12, fasting=False),
        Test(lab_id=lab1.id, name="Kidney Function Test (KFT)", category="Kidney", price=400, tat_hours=12, fasting=False),
        Test(lab_id=lab2.id, name="Blood Sugar Fasting", category="Diabetes", price=80, tat_hours=4, fasting=True),
        Test(lab_id=lab2.id, name="Blood Sugar PP", category="Diabetes", price=80, tat_hours=4, fasting=False),
        Test(lab_id=lab2.id, name="Urine Routine", category="General", price=100, tat_hours=4, fasting=False),
        Test(lab_id=lab2.id, name="Dengue NS1 Antigen", category="Infectious", price=600, tat_hours=24, fasting=False),
    ]
    for t in tests:
        db.session.add(t)

    print("[SEED] Adding demo ambulances...")
    ambulances = [
        Ambulance(driver_name="Ramesh Yadav", driver_phone="980011111", vehicle_no="UP32AB1234",
                  type="Basic", base_fare=300, per_km_fare=12,
                  lat=26.9260, lng=81.1970, status="available",
                  equipment='["Oxygen", "Stretcher", "First Aid"]', rating=4.8, total_trips=234),
        Ambulance(driver_name="Sunil Kumar", driver_phone="9800000000", vehicle_no="UP32CD5678",
                  type="ALS", base_fare=500, per_km_fare=22,
                  lat=26.9320, lng=81.2060, status="available",
                  equipment='["Defibrillator", "Ventilator", "IV Lines", "Cardiac Monitor"]', rating=4.9, total_trips=156),
        Ambulance(driver_name="Mahesh Gupta", driver_phone="9800000000", vehicle_no="UP32EF9012",
                  type="Neonatal", base_fare=800, per_km_fare=32,
                  lat=26.9180, lng=81.1880, status="available",
                  equipment='["Incubator", "Neonatal Ventilator", "IV Pump", "SpO2 Monitor"]', rating=5.0, total_trips=78),
        Ambulance(driver_name="Ravi Sharma", driver_phone="9000000000", vehicle_no="UP32GH3456",
                  type="Basic", base_fare=250, per_km_fare=10,
                  lat=26.9400, lng=81.2100, status="available",
                  equipment='["Oxygen", "Stretcher", "BP Cuff"]', rating=4.5, total_trips=312),
    ]
    for amb in ambulances:
        db.session.add(amb)

    db.session.commit()
    print("[SEED] Demo data seeded successfully!")


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        #db.init_app(app)
        seed_demo_data()
    app.run(debug=True, host='0.0.0.0', port=5000)
