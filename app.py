import os
from flask import Flask, request
from responder import generate_response
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

@app.route("/", methods=["GET"])
def verify():
    if request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return "Verification failed", 403

@app.route("/", methods=["POST"])
def webhook():
    data = request.get_json()
    if not data or "entry" not in data:
        return "Invalid payload", 400
    for entry in data.get("entry", []):
        for change in entry.get("changes", []):
            messaging = change.get("value", {})
            if messaging.get("messaging_product") == "instagram" and "messages" in messaging:
                message = messaging["messages"][0]
                if "text" in message:
                    sender_id = message["from"]
                    message_text = message["text"]
                    reply = generate_response(message_text)
                    send_message(sender_id, reply)
    return "ok", 200

def send_message(recipient_id, text):
    if not ACCESS_TOKEN:
        print("Error: ACCESS_TOKEN is not set")
        return
    url = f"https://graph.facebook.com/v21.0/me/messages?access_token={ACCESS_TOKEN}"
    payload = {
        "messaging_product": "instagram",
        "recipient": {"id": recipient_id},
        "message": {"text": text}
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code != 200:
        print(f"Failed to send message: {response.text}")

if __name__ == "__main__":
    app.run(debug=True)
