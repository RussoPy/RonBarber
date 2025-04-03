from flask import Flask, jsonify
from flask_cors import CORS
import subprocess
import os

app = Flask(__name__)
CORS(app)

@app.route("/send_messages", methods=["GET"])
def send_messages():
    subprocess.Popen(["python", "whatsapp_script.py"])
    return jsonify({"status": "started"}), 200


@app.route("/")
def home():
    return "🧠 Barber Reminder Flask Server is Running!"
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)