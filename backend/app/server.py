from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import os
import base64
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime
import json
import requests

# ==== 🔐 CONFIGURATION ====
ADMIN_SECRET = os.environ.get("ADMIN_SECRET", "letmein123")
TEXTME_API_TOKEN = os.environ.get("TEXTME_TOKEN")
TEXTME_USERNAME = os.environ.get("TEXTME_USERNAME", "galrusso3@gmail.com")
TEXTME_SOURCE = os.environ.get("TEXTME_SOURCE", "GalBarber")  # Confirm with TextMe!

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

        if phone.startswith("+972"):
            local_number = "0" + phone[4:]
        elif phone.startswith("972"):
            local_number = "0" + phone[3:]
        else:
            local_number = phone

        appt_ref.child(appt_id).update({
            "phone": local_number
        })

        template = data.get("template") or f"שלום {{name}}, תזכורת לתור שלך היום בשעה {{time}}. תודה, {{barber}} 💈"
        message = template.replace("{{name}}", name or "לקוח") \
                          .replace("{{time}}", time or "00:00") \
                          .replace("{{barber}}", barber_name)

        sms_payload = {
            "sms": {
                "user": {
                    "username": TEXTME_USERNAME,
                    "token": TEXTME_API_TOKEN
                },
                "source": TEXTME_SOURCE,
                "destinations": {
                    "phone": [
                        { "_": local_number }
                    ]
                },
                "message": message
            }
        }

        print("🛰️ Sending payload to TextMe:")
        print(json.dumps(sms_payload, indent=2))

        try:
            res = requests.post(
                "https://my.textme.co.il/api",
                json=sms_payload,
                headers={"Content-Type": "application/json"}
            )
            res_data = res.json()

            print("📨 Full API response from TextMe:")
            print(json.dumps(res_data, indent=2))

            if res_data.get("status") == 0:
                appt_ref.child(appt_id).update({
                    "sent": True,
                    "sid": res_data.get("transaction_id", "n/a"),
                    "sent_at": datetime.now().isoformat()
                })
                print(f"✅ Sent to {name} ({local_number}) — TXID: {res_data.get('transaction_id')}")
                sent_count += 1
            else:
                print(f"❌ Failed to send to {name}: {res_data}")

        except Exception as e:
            print(f"❌ Exception while sending to {name} ({local_number}): {e}")

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
