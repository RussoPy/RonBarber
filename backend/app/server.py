from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import os
import base64
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime
from twilio.rest import Client

# ==== 🔐 CONFIGURATION ====
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_SID", "your_sid_here")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_TOKEN", "your_token_here")
TWILIO_SMS_FROM = "+1415xxxxxxx"

# ==== Firebase Init ====
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

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# ==== Flask Init ====
app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return Response("🧠 Barber Reminder Flask Server is Running!", mimetype='text/plain')

@app.route("/send_messages", methods=["POST"])
def send_messages():
    data = request.get_json()
    uid = data.get("uid")
    date = data.get("date")

    if not uid or not date:
        return jsonify({"error": "Missing 'uid' or 'date'"}), 400

    appt_ref = db.reference(f"appointments/{uid}/{date}")
    user_ref = db.reference(f"users/{uid}/info")
    appointments = appt_ref.get()
    user_info = user_ref.get()

    if not appointments:
        return jsonify({"message": "No appointments found."})

    barber_name = user_info.get("name", "הספר") if user_info else "הספר"
    sent_count = 0

    for appt_id, appt in appointments.items():
        if appt.get("sent"):
            continue

        name = appt.get("name")
        phone = appt.get("phone")
        time = appt.get("time")

        if not phone or not time:
            continue

        to_number = phone if phone.startswith('+') else f"+972{phone.lstrip('0')}"
        message = f"שלום {name}, תזכורת לתור שלך היום בשעה {time}. תודה, {barber_name} 💈"

        try:
            msg = client.messages.create(
                from_=TWILIO_SMS_FROM,
                body=message,
                to=to_number
            )

            appt_ref.child(appt_id).update({
                "sent": True,
                "sid": msg.sid,
                "sent_at": datetime.now().isoformat()
            })
            sent_count += 1

        except Exception as e:
            print(f"❌ Failed to send to {name}: {e}")

    db.reference(f"users/{uid}/message_stats/{date}").set(sent_count)

    return jsonify({ "message": f"{sent_count} messages sent for {date}" })

# ==== Run ====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
