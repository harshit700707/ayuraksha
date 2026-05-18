# -*- coding: utf-8 -*-
from flask import Blueprint, request, jsonify
from database.models import Hospital, Lab, Ambulance
from utils import haversine, success_response, error_response

location_bp = Blueprint('location', __name__)


@location_bp.route('/detect', methods=['GET'])
def detect_location():
    lat = request.args.get('lat', type=float)
    lng = request.args.get('lng', type=float)

    if not lat or not lng:
        return jsonify(success_response({
            'city': 'Barabanki', 'state': 'Uttar Pradesh',
            'lat': 26.9270, 'lng': 81.1989
        }))

    try:
        import requests as req
        res = req.get(
            f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lng}&format=json",
            headers={'User-Agent': 'AyuRaksha/2.0'},
            timeout=5
        )
        data = res.json()
        addr = data.get('address', {})
        city = addr.get('city') or addr.get('town') or addr.get('village') or 'Barabanki'
        state = addr.get('state', 'Uttar Pradesh')
        return jsonify(success_response({'city': city, 'state': state, 'lat': lat, 'lng': lng}))
    except Exception:
        return jsonify(success_response({'city': 'Barabanki', 'state': 'Uttar Pradesh', 'lat': lat, 'lng': lng}))


@location_bp.route('/nearby-hospitals', methods=['GET'])
def nearby_hospitals():
    lat = request.args.get('lat', 26.9270, type=float)
    lng = request.args.get('lng', 81.1989, type=float)
    radius = request.args.get('radius', 20, type=float)
    htype = request.args.get('type', '')

    hospitals = Hospital.query.filter_by(is_active=True, is_verified=True).all()
    result = []
    for h in hospitals:
        if h.lat and h.lng:
            dist = haversine(lat, lng, h.lat, h.lng)
            if dist <= radius:
                if htype and h.type != htype:
                    continue
                d = h.to_dict(distance_km=dist)
                result.append(d)

    result.sort(key=lambda x: x['distance_km'])
    return jsonify(success_response(result))


@location_bp.route('/nearby-labs', methods=['GET'])
def nearby_labs():
    lat = request.args.get('lat', 26.9270, type=float)
    lng = request.args.get('lng', 81.1989, type=float)
    radius = request.args.get('radius', 15, type=float)

    labs = Lab.query.filter_by(is_active=True, is_verified=True).all()
    result = []
    for lab in labs:
        if lab.lat and lab.lng:
            dist = haversine(lat, lng, lab.lat, lab.lng)
            if dist <= radius:
                d = lab.to_dict(distance_km=dist)
                result.append(d)

    result.sort(key=lambda x: x['distance_km'])
    return jsonify(success_response(result))


@location_bp.route('/nearby-ambulances', methods=['GET'])
def nearby_ambulances():
    lat = request.args.get('lat', 26.9270, type=float)
    lng = request.args.get('lng', 81.1989, type=float)

    ambulances = Ambulance.query.filter_by(status='available', is_active=True).all()
    result = []
    for amb in ambulances:
        if amb.lat and amb.lng:
            dist = haversine(lat, lng, amb.lat, amb.lng)
            if dist <= 25:
                eta = int(dist / 0.5)  # ~30 km/h average
                d = amb.to_dict(distance_km=dist, eta_min=max(eta, 3))
                result.append(d)

    result.sort(key=lambda x: x['distance_km'])
    return jsonify(success_response(result))
