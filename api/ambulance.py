# -*- coding: utf-8 -*-
import math
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from database.models import db, Ambulance, AmbulanceBooking, Hospital
from utils import haversine, success_response, error_response, generate_booking_id
from utils.whatsapp import send_ambulance_dispatch

ambulance_bp = Blueprint('ambulance', __name__)


@ambulance_bp.route('/nearby', methods=['GET'])
def nearby_ambulances():
    lat = request.args.get('lat', 26.9270, type=float)
    lng = request.args.get('lng', 81.1989, type=float)
    amb_type = request.args.get('type', '')

    query = Ambulance.query.filter_by(status='available', is_active=True)
    if amb_type:
        query = query.filter_by(type=amb_type)

    ambulances = query.all()

    # Demo bypass: if all ambulances are busy, auto-reset them so the demo never fails!
    if not ambulances:
        db.session.query(Ambulance).filter_by(is_active=True).update({Ambulance.status: 'available'})
        db.session.commit()
        # Re-run query
        ambulances = query.all()

    result = []
    for amb in ambulances:
        if amb.lat and amb.lng:
            dist = haversine(lat, lng, amb.lat, amb.lng)
            # Demo bypass: if user is testing outside Barabanki, mock a nearby distance (1.2 to 4.5 km)
            if dist > 25:
                import random
                dist = round(random.uniform(1.2, 4.5), 1)
            
            eta = max(int(dist / 0.4), 3)
            result.append(amb.to_dict(distance_km=dist, eta_min=eta))

    result.sort(key=lambda x: x['distance_km'])
    return jsonify(success_response(result))


@ambulance_bp.route('/fare-estimate', methods=['POST'])
def fare_estimate():
    data = request.get_json()
    pickup_lat = data.get('pickup_lat', 26.9270)
    pickup_lng = data.get('pickup_lng', 81.1989)
    dest_lat = data.get('dest_lat', 26.9270)
    dest_lng = data.get('dest_lng', 81.1989)
    amb_type = data.get('type', 'Basic')

    dist = haversine(pickup_lat, pickup_lng, dest_lat, dest_lng)

    fare_config = {
        'Basic': {'base': 300, 'per_km': 15},
        'ALS': {'base': 500, 'per_km': 25},
        'Neonatal': {'base': 800, 'per_km': 35},
    }
    cfg = fare_config.get(amb_type, fare_config['Basic'])
    total = cfg['base'] + int(dist * cfg['per_km'])

    return jsonify(success_response({
        'distance_km': round(dist, 1),
        'base_fare': cfg['base'],
        'per_km_fare': cfg['per_km'],
        'total_fare': total,
        'type': amb_type,
    }))


@ambulance_bp.route('/book', methods=['POST'])
def book_ambulance():
    data = request.get_json()
    required = ['ambulance_id', 'patient_name', 'patient_phone', 'pickup_lat', 'pickup_lng', 'pickup_address']
    for field in required:
        if not data.get(field) and data.get(field) != 0:
            return jsonify(error_response(f"Field '{field}' is required")[0]), 400

    amb = Ambulance.query.get_or_404(data['ambulance_id'])
    if amb.status != 'available':
        return jsonify(error_response("Ambulance not available. Please choose another.")[0]), 400

    pickup_lat = data['pickup_lat']
    pickup_lng = data['pickup_lng']
    dest_lat, dest_lng, dest_address = pickup_lat, pickup_lng, data.get('dest_address', '')

    if data.get('dest_hospital_id'):
        hosp = Hospital.query.get(data['dest_hospital_id'])
        if hosp and hosp.lat and hosp.lng:
            dest_lat = hosp.lat
            dest_lng = hosp.lng
            dest_address = hosp.address

    dist = haversine(pickup_lat, pickup_lng, dest_lat, dest_lng)
    # Demo bypass: if user is outside Barabanki, mock a reasonable distance (1.5 to 5.0 km)
    if dist > 25:
        import random
        dist = round(random.uniform(1.5, 5.0), 1)

    base_fare = amb.base_fare or 300
    per_km = amb.per_km_fare or 15
    total_fare = base_fare + int(dist * per_km)
    
    # Calculate ETA to pickup
    pickup_dist = haversine(amb.lat or pickup_lat, amb.lng or pickup_lng, pickup_lat, pickup_lng)
    if pickup_dist > 25:
        import random
        pickup_dist = random.uniform(1.0, 4.0)
    eta = max(int(pickup_dist / 0.4), 3)

    amb.status = 'busy'
    booking_id = generate_booking_id('AMB')

    booking = AmbulanceBooking(
        booking_id=booking_id,
        ambulance_id=amb.id,
        patient_name=data['patient_name'],
        patient_phone=data['patient_phone'],
        pickup_lat=pickup_lat,
        pickup_lng=pickup_lng,
        pickup_address=data['pickup_address'],
        dest_hospital_id=data.get('dest_hospital_id'),
        dest_address=dest_address,
        distance_km=round(dist, 1),
        base_fare=base_fare,
        total_fare=total_fare,
        amb_type=data.get('amb_type', 'Basic'),
        payment_method=data.get('payment_method', 'Cash'),
    )
    db.session.add(booking)
    db.session.commit()

    send_ambulance_dispatch(
        data['patient_phone'], booking_id,
        amb.driver_name, amb.vehicle_no,
        booking.amb_type, eta, amb.driver_phone
    )
    return jsonify(success_response({**booking.to_dict(), 'eta_min': eta, 'total_fare': total_fare},
                                    f"Ambulance booked! ID: {booking_id}"))


@ambulance_bp.route('/<string:booking_id>/track', methods=['GET'])
def track_ambulance(booking_id):
    booking = AmbulanceBooking.query.filter_by(booking_id=booking_id).first_or_404()
    amb = Ambulance.query.get(booking.ambulance_id)

    amb_lat = amb.lat if (amb and amb.lat) else booking.pickup_lat
    amb_lng = amb.lng if (amb and amb.lng) else booking.pickup_lng
    
    # If the simulated ambulance is too far from user pickup (e.g. demo test from other cities),
    # place it close to user (0.01 degrees off) so Leaflet tracks it smoothly.
    if haversine(amb_lat, amb_lng, booking.pickup_lat, booking.pickup_lng) > 25:
        amb_lat = booking.pickup_lat + 0.012
        amb_lng = booking.pickup_lng - 0.015

    # Simulate movement toward pickup
    import random
    noise_lat = random.uniform(-0.001, 0.001)
    noise_lng = random.uniform(-0.001, 0.001)

    current_lat = amb_lat + noise_lat
    current_lng = amb_lng + noise_lng
    dist_remaining = haversine(current_lat, current_lng, booking.pickup_lat, booking.pickup_lng)

    return jsonify(success_response({
        'booking_id': booking_id,
        'status': booking.status,
        'driver_name': amb.driver_name if amb else '',
        'vehicle_no': amb.vehicle_no if amb else '',
        'driver_phone': amb.driver_phone if amb else '',
        'current_lat': current_lat,
        'current_lng': current_lng,
        'pickup_lat': booking.pickup_lat,
        'pickup_lng': booking.pickup_lng,
        'eta_min': max(int(dist_remaining / 0.5), 1),
    }))


@ambulance_bp.route('/<string:booking_id>/status', methods=['PUT'])
@jwt_required()
def update_status(booking_id):
    data = request.get_json()
    booking = AmbulanceBooking.query.filter_by(booking_id=booking_id).first_or_404()
    booking.status = data.get('status', booking.status)
    if booking.status == 'Completed':
        booking.completed_at = datetime.utcnow()
        amb = Ambulance.query.get(booking.ambulance_id)
        if amb:
            amb.status = 'available'
            amb.total_trips += 1
    db.session.commit()
    return jsonify(success_response(booking.to_dict(), "Status updated"))
