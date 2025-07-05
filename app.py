import os
from flask import Flask, request
from responder import generate_response
from sheets import log_to_sheets
import requests

app = Flask(__name__)
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

@app.route("/", methods=["GET"])
def verify():
    if request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return "Ошибка верификации", 403

@app.route("/", methods=["POST"])
def webhook():
    data = request.get_json()
    for entry in data.get("entry", []):
        for change in entry.get("changes", []):
            messaging = change.get("value", {})
            if messaging.get("messaging_product") == "instagram":
                sender_id = messaging["messages"][0]["from"]
                message_text = messaging["messages"][0]["text"]
                log_to_sheets(sender_id, message_text)
                reply = generate_response(message_text)
                send_message(sender_id, reply)
    return "ok", 200

def send_message(recipient_id, text):
    url = f"https://graph.facebook.com/v18.0/me/messages?access_token={ACCESS_TOKEN}"
    payload = {
        "messaging_product": "instagram",
        "recipient": {"id": recipient_id},
        "message": {"text": text}
    }
    headers = {"Content-Type": "application/json"}
    requests.post(url, json=payload, headers=headers)

if __name__ == "__main__":
    app.run(debug=True)
