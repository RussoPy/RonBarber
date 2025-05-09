from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import os
import base64
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime
from twilio.rest import Client
import json


# ==== 🔐 CONFIGURATION ====
ADMIN_SECRET = os.environ.get("ADMIN_SECRET", "letmein123")
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_SID", "your_sid_here")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_TOKEN", "your_token_here")
TWILIO_SMS_FROM = "+18148461589"

# ==== Firebase Init ====
firebase_b64 = os.environ.get("FIREBASE_CRED_BASE64")
if not firebase_b64:
    raise Exception("❌ Missing FIREBASE_CRED_BASE64 in environment variables")

firebase_path = "firebase.json"
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

    print(f"📥 Incoming send request for UID: {uid}, Date: {date}")
    print("📋 Loaded appointments:", appointments)

    if not appointments:
        return jsonify({"message": "No appointments found.", "sent": 0, "total": 0})

    barber_name = user_info.get("name", "הספר") if user_info else "הספר"
    sent_count = 0
    total_attempts = len(appointments)

    for appt_id, appt in appointments.items():
        print(f"\n🔍 Processing appointment {appt_id}: {appt}")

        if appt.get("sent"):
            print("⏩ Already marked as sent, skipping.")
            continue

        name = appt.get("name")
        phone = appt.get("phone")
        time = appt.get("time")

        if not phone or not time:
            print("⚠️ Missing phone or time, skipping.")
            continue

        # ✅ Normalize phone
        if phone.startswith("+"):
            to_number = phone
        else:
            to_number = f"+972{phone.lstrip('0')}"

        # ✅ Optionally update Firebase with normalized number
        appt_ref.child(appt_id).update({
            "phone": to_number
        })

        # Get template from body or fallback
        template = data.get("template") or f"שלום {{name}}, תזכורת לתור שלך היום בשעה {{time}}. תודה, {{barber}} 💈"

        # Replace variables in template
        message = template.replace("{{name}}", name or "לקוח") \
                        .replace("{{time}}", time or "00:00") \
                        .replace("{{barber}}", barber_name)
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

            print(f"✅ Sent to {name} ({to_number}) — SID: {msg.sid}")
            sent_count += 1

        except Exception as e:
            print(f"❌ Failed to send to {name} ({to_number}): {e}")

    # 🧠 Save daily and total counters
    db.reference(f"users/{uid}/message_stats/{date}").set(sent_count)
    current_total = db.reference(f"users/{uid}/message_total").get() or 0
    db.reference(f"users/{uid}/message_total").set(current_total + sent_count)

    print(f"\n📊 {sent_count} / {total_attempts} messages sent for UID {uid} on {date}")
    return jsonify({
        "message": f"{sent_count} of {total_attempts} messages sent for {date}",
        "sent": sent_count,
        "total": total_attempts
    })

@app.route("/admin/usage", methods=["GET"])
def get_usage():
    auth = request.headers.get("Authorization", "")
    if auth != ADMIN_SECRET:
        return jsonify({"error": "Unauthorized"}), 403

    users_ref = db.reference("users").get()
    result = []

    for uid, data in users_ref.items():
        name = data.get("info", {}).get("name", "Unknown")
        total = data.get("message_total", 0)
        result.append({ "uid": uid, "name": name, "messages_sent": total })
    print("🔥 USAGE DEBUG:")
    print(json.dumps(result, indent=2))
    return jsonify(result), 200


# ==== Run ====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
