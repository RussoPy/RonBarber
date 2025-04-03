from flask import Flask, jsonify
from flask_cors import CORS
import subprocess

app = Flask(__name__)
CORS(app)

@app.route("/send_messages", methods=["GET"])
def send_messages():
    subprocess.Popen(["python", "whatsapp_script.py"])
    return jsonify({"status": "started"}), 200

if __name__ == "__main__":
    app.run(debug=True, port=5000)
