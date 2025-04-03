from flask import Flask, jsonify, Response
from flask_cors import CORS
from firebase_admin import credentials, initialize_app, db
import os
from datetime import datetime
import base64

app = Flask(__name__)
CORS(app)

# === 🔐 Firebase Setup ===
# Load from file if running locally; in production, credentials should be set securely
# Decode firebase.json from ENV
firebase_b64 = os.environ.get("FIREBASE_CRED_BASE64")

if not firebase_b64:
    raise Exception("Missing FIREBASE_CRED_BASE64 env var")

firebase_path = "/tmp/firebase.json"
with open(firebase_path, "wb") as f:
    f.write(base64.b64decode(firebase_b64))

cred = credentials.Certificate(firebase_path)
initialize_app(cred, {
    'databaseURL': 'https://barberreminder-default-rtdb.europe-west1.firebasedatabase.app'
})
initialize_app(cred, {
    'databaseURL': 'https://barberreminder-default-rtdb.europe-west1.firebasedatabase.app'
})

@app.route("/")
def home():
    return Response("🧠 Barber Reminder Flask Server is Running!", mimetype='text/plain')


@app.route("/send_messages", methods=["GET"])
def send_messages():
    date_str = datetime.now().strftime("%Y-%m-%d")

    # ✅ Set trigger in Firebase
    trigger_ref = db.reference("trigger/send_whatsapp")
    trigger_ref.set({
        "send_now": True,
        "date": date_str
    })
    return jsonify({"status": "trigger_set", "date": date_str}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
