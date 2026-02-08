# routes/otp_routes.py
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import random

otp_bp = Blueprint("otp_bp", __name__)

# Temporary OTP store
otp_store = {}

# Configuration
OTP_EXPIRY_MINUTES = 5
MAX_ATTEMPTS = 5

def generate_otp():
    return random.randint(100000, 999999)

def cleanup_otps():
    now = datetime.now()
    for key in list(otp_store.keys()):
        if otp_store[key]["expiry"] < now:
            otp_store.pop(key)

def verify_individual_otp(key, otp_value):
    data = otp_store.get(key)
    if not data:
        return "OTP invalid"
    if data["expiry"] < datetime.now():
        otp_store.pop(key, None)
        return "OTP expired"
    if data["attempts"] >= MAX_ATTEMPTS:
        return "OTP blocked due to too many attempts"
    try:
        if data["otp"] != int(otp_value):
            data["attempts"] += 1
            return "OTP invalid"
    except (TypeError, ValueError):
        return "OTP must be a number"
    return None

@otp_bp.route("/request", methods=["POST"])
def request_otp():
    cleanup_otps()
    data = request.json
    phone = data.get("phone")
    email = data.get("email")

    if not phone or not email:
        return jsonify({"error": "Phone and Email required"}), 400

    otp_phone = generate_otp()
    otp_email = generate_otp()
    expiry_time = datetime.now() + timedelta(minutes=OTP_EXPIRY_MINUTES)

    otp_store[phone] = {"otp": otp_phone, "expiry": expiry_time, "attempts": 0}
    otp_store[email] = {"otp": otp_email, "expiry": expiry_time, "attempts": 0}

    # For local testing, return OTPs in JSON
    print(f"[TEST] OTP for phone ({phone}): {otp_phone}")
    print(f"[TEST] OTP for email ({email}): {otp_email}")

    return jsonify({
        "message": "OTPs generated successfully",
        "phone_otp": otp_phone,
        "email_otp": otp_email
    }), 200

@otp_bp.route("/verify", methods=["POST"])
def verify_otp():
    cleanup_otps()
    data = request.json
    phone = data.get("phone")
    email = data.get("email")
    otp_phone_input = data.get("otp_phone")
    otp_email_input = data.get("otp_email")

    if otp_phone_input is None or otp_email_input is None:
        return jsonify({"error": "Both otp_phone and otp_email are required"}), 400

    errors = []

    err = verify_individual_otp(phone, otp_phone_input)
    if err:
        errors.append(f"Phone: {err}")

    err = verify_individual_otp(email, otp_email_input)
    if err:
        errors.append(f"Email: {err}")

    if errors:
        return jsonify({"success": False, "errors": errors}), 400

    otp_store.pop(phone, None)
    otp_store.pop(email, None)

    return jsonify({"success": True, "message": "OTP verified successfully"}), 200



