# -*- coding: utf-8 -*-
import math
import re


def haversine(lat1, lng1, lat2, lng2):
    """Calculate distance in km between two GPS coordinates."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


def validate_gst(gst):
    """Validate Indian GST number format: 22AAAAA0000A1Z5"""
    if not gst:
        return False, "GST number required"
    gst = gst.strip().upper()
    if len(gst) != 15:
        return False, "GST must be 15 characters"
    pattern = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$'
    if not re.match(pattern, gst):
        return False, "Invalid GST format. Example: 09AABCU9603R1ZX"
    return True, "Valid"


def validate_phone(phone):
    """Validate 10-digit Indian mobile number."""
    if not phone:
        return False, "Phone number required"
    phone = str(phone).strip()
    if not re.match(r'^[6-9][0-9]{9}$', phone):
        return False, "Invalid phone number (must be 10 digits starting with 6-9)"
    return True, "Valid"


def success_response(data=None, message="Success"):
    resp = {"success": True, "message": message}
    if data is not None:
        resp["data"] = data
    return resp


def error_response(message="Error", code=400):
    return {"success": False, "message": message}, code


def generate_booking_id(prefix):
    import random
    return f"{prefix}{random.randint(100000, 999999)}"
