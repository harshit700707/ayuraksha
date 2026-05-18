import os
from twilio.rest import Client


def format_phone(to_phone):
    """Format Indian number properly"""

    phone = str(to_phone).replace(" ", "").replace("+", "")

    if not phone.startswith("91"):
        phone = "91" + phone

    return f"whatsapp:+{phone}"


def send_whatsapp(to_phone, message):
    """Send WhatsApp via Twilio"""

    try:
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        from_number = os.getenv(
            "TWILIO_WHATSAPP_NUMBER",
            "whatsapp:+14155238886"
        )

        if not account_sid or not auth_token:
            print("Twilio credentials missing")
            return False

        client = Client(account_sid, auth_token)

        formatted_phone = format_phone(to_phone)

        msg = client.messages.create(
            body=message,
            from_=from_number,
            to=formatted_phone
        )

        print(f"WhatsApp sent successfully: {msg.sid}")
        return True

    except Exception as e:
        print(f"WhatsApp Error: {e}")
        return False


def send_bed_booking_confirmation(patient_phone, booking_id, hospital_name, bed_type, patient_name):

    msg = (
        f"*AyuRaksha - Bed Booking Confirmed*\n\n"
        f"Booking ID: {booking_id}\n"
        f"Hospital: {hospital_name}\n"
        f"Bed Type: {bed_type}\n"
        f"Patient: {patient_name}\n\n"
        f"Please arrive within 2 hours."
    )

    return send_whatsapp(patient_phone, msg)


def send_lab_booking_confirmation(patient_phone, booking_id, test_names, date, slot, tat_hours):

    msg = (
        f"*AyuRaksha - Lab Booking Confirmed*\n\n"
        f"Booking ID: {booking_id}\n"
        f"Tests: {test_names}\n"
        f"Date: {date}\n"
        f"Slot: {slot}\n\n"
        f"Reports in {tat_hours} hours."
    )

    return send_whatsapp(patient_phone, msg)


def send_ambulance_dispatch(patient_phone, booking_id, driver_name, vehicle_no, amb_type, eta, driver_phone):

    msg = (
        f"*AyuRaksha - Ambulance Dispatched*\n\n"
        f"Booking ID: {booking_id}\n"
        f"Driver: {driver_name}\n"
        f"Vehicle: {vehicle_no}\n"
        f"Type: {amb_type}\n"
        f"ETA: {eta} mins\n"
        f"Driver Contact: {driver_phone}"
    )

    return send_whatsapp(patient_phone, msg)


def send_icu_alert(doctor_phone, patient_name, bed_number, risk_score, qsofa, timestamp):

    msg = (
        f"*URGENT - AyuRaksha ICU Alert*\n\n"
        f"Patient: {patient_name}\n"
        f"Bed: {bed_number}\n"
        f"Risk Score: {risk_score}/100\n"
        f"qSOFA: {qsofa}/3\n"
        f"Status: HIGH RISK\n\n"
        f"Time: {timestamp}"
    )

    return send_whatsapp(doctor_phone, msg)


def send_hospital_registration_notification(admin_phone, name, htype, gst_number, contact_person, phone, city):

    msg = (
        f"*New Hospital Registration*\n\n"
        f"Hospital: {name}\n"
        f"Type: {htype}\n"
        f"GST: {gst_number}\n"
        f"Contact: {contact_person}\n"
        f"Phone: {phone}\n"
        f"City: {city}"
    )

    return send_whatsapp(admin_phone, msg)


def send_hospital_verified(hospital_phone, hospital_name):

    msg = (
        f"*Congratulations!*\n\n"
        f"{hospital_name} is now VERIFIED on AyuRaksha."
    )

    return send_whatsapp(hospital_phone, msg)