from flask import Flask, request, jsonify, session, make_response, send_from_directory
from flask_pymongo import PyMongo
from bson import ObjectId
from bson.errors import InvalidId
import face_recognition
import numpy as np
import bcrypt
from flask_cors import CORS
import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import random
import string
import io
import os
import re

# ===================================
# Flask + MongoDB
# ===================================
app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/smartVoting"

# Absolute path for uploads
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.config["UPLOAD_FOLDER"] = os.path.join(BASE_DIR, "uploads")

app.secret_key = "your_secret_key_here"
mongo = PyMongo(app)

# Ensure upload folder exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Enable CORS
CORS(app, supports_credentials=True)

# Collections
voters = mongo.db.voters
candidates = mongo.db.candidates
votes = mongo.db.votes
election = mongo.db.election
students_list = mongo.db.students_list


# ===================================
# Helper functions
# ===================================
def clean(text):
    """Normalize strings for comparison."""
    if not isinstance(text, str):
        return ""
    text = text.replace("\u00A0", " ").replace("\u200B", "")
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()


def decode_base64_image(image_base64):
    """Decode base64 → PIL RGB image."""
    if not image_base64:
        raise ValueError("Empty image data")

    if "," in image_base64:
        image_base64 = image_base64.split(",", 1)[1]

    try:
        img = Image.open(BytesIO(base64.b64decode(image_base64)))
        return img.convert("RGB")
    except Exception as e:
        raise ValueError(f"Invalid image: {e}")


# ===================================
# CAPTCHA
# ===================================
def generate_captcha_text():
    letters = string.ascii_uppercase + string.digits
    captcha = ''.join(random.choice(letters) for _ in range(5))
    session["captcha_text"] = captcha
    return captcha


def generate_captcha_image(text):
    width, height = 280, 100
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("fonts/arialbd.ttf", 50)
    except:
        font = ImageFont.load_default()

    for y in range(height):
        draw.line([(0, y), (width, y)], fill=(180, 220, 255))

    x = 25
    for char in text:
        color = (random.randint(0, 150), random.randint(0, 150), random.randint(0, 150))
        draw.text((x, 20), char, font=font, fill=color)
        x += 45

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


@app.route("/captcha")
def serve_captcha():
    text = generate_captcha_text()
    img = generate_captcha_image(text)
    response = make_response(img.getvalue())
    response.headers["Content-Type"] = "image/png"
    return response


# ===================================
# Home
# ===================================
@app.route("/")
def home():
    return "Backend running 🎉"


# ===================================
# Serve Uploaded Images
# ===================================
@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


# ===================================
# Get candidates (with image URLs)
# ===================================
@app.route("/candidates", methods=["GET"])
def get_candidates():
    try:
        data = []
        for c in candidates.find():
            symbol_path = c.get("symbol", "").lstrip("/")
            if symbol_path:
                base = request.host_url.rstrip("/")
                full_url = f"{base}/uploads/{symbol_path}"
            else:
                full_url = ""

            data.append({
                "_id": str(c["_id"]),
                "name": c.get("name", "Unknown"),
                "symbol": full_url
            })
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ===================================
# Register student
# ===================================
@app.route("/register", methods=["POST"])
def register():
    try:
        data = request.json or {}

        required = ["usn", "name", "email", "phone", "password", "image"]
        if any(k not in data or not str(data[k]).strip() for k in required):
            return jsonify({"error": "Missing required fields"}), 400

        usn = data["usn"].strip().upper()
        name = data["name"].strip()
        email = data["email"].strip()
        phone = data["phone"].strip()
        password = data["password"].strip()
        img_b64 = data["image"]

        # 1) Find student in preloaded list
        student = students_list.find_one({"usn": usn})
        if not student:
            return jsonify({"error": "USN not found"}), 404

        # 2) Compare details (normalized)
        if clean(student.get("name", "")) != clean(name):
            return jsonify({"error": "Name mismatch"}), 403

        if clean(student.get("email", "")) != clean(email):
            return jsonify({"error": "Email mismatch"}), 403

        if str(student.get("phone", "")).strip() != phone:
            return jsonify({"error": "Phone mismatch"}), 403

        # 3) Check if already registered in voters (source of truth)
        if voters.find_one({"usn": usn}):
            return jsonify({"error": "Already registered"}), 400

        # 4) Face encoding from uploaded live image
        img = decode_base64_image(img_b64)
        encodings = face_recognition.face_encodings(np.array(img))
        if len(encodings) != 1:
            return jsonify({"error": "Face not detected"}), 400
        uploaded_encoding = encodings[0]

        # 5) Compare with official stored encoding from students_list
        if "face_encoding" not in student:
            return jsonify({"error": "No official face stored for this student"}), 400

        official = np.array(student["face_encoding"])
        distance = face_recognition.face_distance([official], uploaded_encoding)[0]
        if distance > 0.45:
            return jsonify({"error": "Face does not match official photo"}), 401

        # 6) Hash password and store voter entry
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        voters.insert_one({
            "usn": usn,
            "name": name,
            "email": email,
            "phone": phone,
            "password_hash": hashed,
            "face_encoding": uploaded_encoding.tolist()
        })

        # 7) Optionally mark as registered (for admin view only)
        students_list.update_one({"usn": usn}, {"$set": {"is_registered": True}})

        return jsonify({"status": "registered"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ===================================
# Login
# ===================================
@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.json or {}
        required = ["usn", "password", "captcha_input", "image"]
        if any(k not in data or not str(data[k]).strip() for k in required):
            return jsonify({"error": "Missing required fields"}), 400

        usn = data["usn"].upper().strip()
        password = data["password"]
        captcha = data["captcha_input"].upper().strip()
        img_b64 = data["image"]

        if captcha != session.get("captcha_text", "").upper():
            return jsonify({"error": "Incorrect CAPTCHA"}), 400

        voter = voters.find_one({"usn": usn})
        if not voter:
            return jsonify({"error": "User not found"}), 404

        if not bcrypt.checkpw(password.encode(), voter["password_hash"].encode()):
            return jsonify({"error": "Wrong password"}), 401

        img = decode_base64_image(img_b64)
        encodings = face_recognition.face_encodings(np.array(img))
        if len(encodings) != 1:
            return jsonify({"error": "Face not detected"}), 400

        distance = face_recognition.face_distance(
            [np.array(voter["face_encoding"])], encodings[0]
        )[0]

        if distance > 0.45:
            return jsonify({"error": "Face mismatch"}), 401

        return jsonify({
    "status": "login success",
    "name": voter["name"]
}), 200


    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ===================================
# Election Status (GET)
# ===================================
@app.route("/election_status", methods=["GET"])
def get_election_status():
    try:
        doc = election.find_one({"name": "main_election"})
        status = doc.get("election_status", "open") if doc else "open"
        return jsonify({"status": status}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ===================================
# Set Election Status (ADMIN)
# ===================================
@app.route("/set_election_status", methods=["POST"])
def set_election_status():
    try:
        data = request.json or {}
        new_status = data.get("status")

        if new_status not in ["open", "closed"]:
            return jsonify({"error": "Invalid status"}), 400

        election.update_one(
            {"name": "main_election"},
            {"$set": {"election_status": new_status}},
            upsert=True
        )

        return jsonify({"status": "updated"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ===================================
# Vote
# ===================================
@app.route("/vote", methods=["POST"])
def vote():
    try:
        # Check election status FIRST
        doc = election.find_one({"name": "main_election"})
        if doc and doc.get("election_status") == "closed":
            return jsonify({"success": False, "error": "Election is closed"}), 403

        data = request.json or {}
        if "usn" not in data or "candidate_id" not in data:
            return jsonify({"success": False, "error": "Missing USN or candidate_id"}), 400

        usn = data["usn"].upper().strip()
        cid = data["candidate_id"].strip()

        voter = voters.find_one({"usn": usn})
        if not voter:
            return jsonify({"success": False, "error": "Voter not found"}), 404

        if votes.find_one({"voter_id": voter["_id"]}):
            return jsonify({"success": False, "error": "Already voted"}), 400

        try:
            candidate_obj_id = ObjectId(cid)
        except InvalidId:
            return jsonify({"success": False, "error": "Invalid candidate ID"}), 400

        votes.insert_one({
            "voter_id": voter["_id"],
            "candidate_id": candidate_obj_id
        })

        return jsonify({"success": True}), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ===================================
# Results
# ===================================
@app.route("/results", methods=["GET"])
def results():
    try:
        pipeline = [
            {"$group": {"_id": "$candidate_id", "votes": {"$sum": 1}}},
            {"$sort": {"votes": -1}}
        ]

        result_list = []
        for r in votes.aggregate(pipeline):
            cand = candidates.find_one({"_id": r["_id"]})
            result_list.append({
                "candidate": cand["name"] if cand else "Unknown",
                "votes": r["votes"]
            })

        return jsonify(result_list)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ===================================
# Run App
# ===================================
if __name__ == "__main__":
    app.run(debug=True, port=5000)

