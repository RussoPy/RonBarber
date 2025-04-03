from flask import Flask, jsonify, Response
from flask_cors import CORS
import os
import base64
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime

app = Flask(__name__)
CORS(app)

# === 🔐 Firebase Init From .env (base64) ===
firebase_b64 = os.environ.get("FIREBASE_CRED_BASE64")

if not firebase_b64:
    raise Exception("❌ Missing FIREBASE_CRED_BASE64 in environment variables")

firebase_path = "/tmp/firebase.json"
with open(firebase_path, "wb") as f:
    f.write(base64.b64decode(firebase_b64))

cred = credentials.Certificate(firebase_path)

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://barberreminder-default-rtdb.europe-west1.firebasedatabase.app'
    })

# === 🌐 Routes ===

@app.route("/")
def home():
    return Response("🧠 Barber Reminder Flask Server is Running!", mimetype='text/plain')

@app.route("/send_messages", methods=["GET"])
def send_messages():
    date_str = datetime.now().strftime("%Y-%m-%d")
    trigger_ref = db.reference("trigger/send_whatsapp")
    trigger_ref.set({
        "send_now": True,
        "date": date_str
    })
    return jsonify({"status": "trigger_set", "date": date_str}), 200

# === 🏁 Start Server ===
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
