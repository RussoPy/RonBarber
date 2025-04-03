import os
import time
import pyautogui
import pyperclip
import webbrowser
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, db

# === 🌍 LOAD ENVIRONMENT VARIABLES ===
load_dotenv()

FIREBASE_CRED_PATH = os.getenv("FIREBASE_CRED_PATH")
FIREBASE_DB_URL = os.getenv("FIREBASE_DB_URL")

# === 🔐 FIREBASE SETUP ===
cred = credentials.Certificate(FIREBASE_CRED_PATH)
firebase_admin.initialize_app(cred, {
    'databaseURL': FIREBASE_DB_URL
})

# === 💬 SEND ONE MESSAGE ===
def send_message(phone, name, time_str):
    try:
        phone = phone.replace(" ", "").replace("-", "")
        if not phone.startswith("+972"):
            phone = "+972" + phone.lstrip("0")

        message = f"שָׁלוֹם {name}, זוהי תזכורת לתור שלך היום בשעה {time_str}. נתראה! ✂️"

        print(f"\n📨 Sending to {name} ({phone})...")

        url = f"https://web.whatsapp.com/send?phone={phone}&text="
        webbrowser.open(url)
        print("🌐 Opened WhatsApp Web in browser")

        time.sleep(6)

        pyperclip.copy(message)
        pyautogui.hotkey("ctrl", "v")
        print("📋 Message pasted")

        time.sleep(1)
        pyautogui.press("enter")
        print(f"✅ Message sent to {name}")

        time.sleep(1)
        pyautogui.hotkey("ctrl", "w")  # 🚪 Close tab
        print("🧹 Tab closed")

        time.sleep(4)  # wait before next message

    except Exception as e:
        print(f"❌ Error sending to {name}: {e}")

# === 🔁 PROCESS FIREBASE APPOINTMENTS ===
def process():
    trigger_ref = db.reference("trigger/send_whatsapp")
    trigger = trigger_ref.get()

    if not trigger or not trigger.get("send_now"):
        print("🟡 No send trigger found.")
        return

    date = trigger.get("date")
    print(f"\n📅 Sending messages for: {date}")
    appointments = db.reference(f"appointments/{date}").get() or {}

    for appt in appointments.values():
        name = appt.get("name")
        phone = appt.get("phone")
        time_str = appt.get("time")

        if name and phone and time_str:
            send_message(phone, name, time_str)
        else:
            print(f"⚠️ Skipping invalid entry: {appt}")

    # Reset the trigger
    trigger_ref.set({"send_now": False, "date": date})
    print("\n✅ All messages sent and trigger reset.")

# === 🏁 RUN ===
input("💻 Make sure WhatsApp Web is open and you're logged in. Press Enter to begin...\n")
process()
