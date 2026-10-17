import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Environment variables configured in hosting platform
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "peter_kagio_verify_token")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

PETER_KAGIO_SYSTEM_PROMPT = """
You are an expert AI Master Diagnostic Technician operating on behalf of Peter Kagio, 
a senior Mercedes-Benz Heavy-Duty Commercial Vehicle Specialist (Contact: 0722710633). 
Provide automated diagnostic quotes, repair steps, ASCII pinouts, and triage advice 
for Mercedes-Benz commercial vehicles (Actros, Axor, Atego, Arocs). 
Always maintain a professional, practical tone and include Peter Kagio's contact details for escalations.
"""

@app.route("/", methods=["GET"])
def home():
    return "Peter Kagio Mercedes Diagnostic Webhook is Live!", 200

@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200
        else:
            return "Verification failed", 403
    return "Webhook Endpoint Ready", 200

@app.route("/webhook", methods=["POST"])
def receive_whatsapp_message():
    body = request.get_json()
    try:
        if "object" in body and body["object"] == "whatsapp_business_account":
            for entry in body["entry"]:
                for change in entry["changes"]:
                    value = change.get("value", {})
                    if "messages" in value:
                        message_data = value["messages"][0]
                        sender_phone = message_data["from"]
                        message_body = message_data["text"]["body"]

                        diagnostic_reply = generate_diagnostic_reply(message_body)
                        send_whatsapp_message(sender_phone, diagnostic_reply)

            return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"Error processing webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

def generate_diagnostic_reply(client_prompt):
    api_url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": PETER_KAGIO_SYSTEM_PROMPT},
            {"role": "user", "content": client_prompt}
        ],
        "temperature": 0.2
    }
    
    response = requests.post(api_url, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return "Diagnostic engine processing error. Contact Peter Kagio directly at 0722710633."

def send_whatsapp_message(recipient_phone, text_message):
    url = f"https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient_phone,
        "type": "text",
        "text": {"body": text_message}
    }
    requests.post(url, json=payload, headers=headers)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
