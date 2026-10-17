import os
from flask import Flask, request, jsonify
import requests
import openai

app = Flask(__name__)

# Environment Variables
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "peter_kagio_verify_token")
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

# Dictionary to track simple user session states in memory
user_sessions = {}

def send_whatsapp_message(to_number, message_text):
    """Sends a text message back to the user via WhatsApp Cloud API."""
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": message_text}
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()

def get_menu_text():
    return (
        "Hello! Welcome to Peter Kagio Technical Services.\n\n"
        "How can we assist you today? Please reply with a number:\n\n"
        "1️⃣ Vehicle Diagnostics & Technical Support (Mercedes-Benz Heavy-Duty Trucks)\n"
        "2️⃣ General Inquiry / Personal Message for Peter\n\n"
        "Reply with 1 or 2 to proceed."
    )

def generate_ai_diagnostic_response(user_query):
    """Generates heavy-duty truck diagnostic response using GPT-4o."""
    system_prompt = (
        "You are an expert Mercedes-Benz Heavy-Duty Truck Diagnostic Assistant working for "
        "Peter Kagio Automotive Technical Services in Kenya. "
        "Provide precise diagnostic guidance for models like Actros, Axor, Atego, and Arocs. "
        "Include fault code meanings, component locations, pinout data or ASCII diagrams when helpful, "
        "and troubleshooting steps. Always advise contacting Peter directly at 0722710633 for hands-on assistance."
    )
    
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ],
            max_tokens=800,
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"An error occurred while generating diagnostic data. Please call Peter directly at 0722710633."

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
    return "Hello World", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    if data.get("object"):
        if (
            data.get("entry") and
            data["entry"][0].get("changes") and
            data["entry"][0]["changes"][0].get("value") and
            data["entry"][0]["changes"][0]["value"].get("messages")
        ):
            message = data["entry"][0]["changes"][0]["value"]["messages"][0]
            sender_id = message["from"]
            message_body = message.get("text", {}).get("body", "").strip()

            current_state = user_sessions.get(sender_id)

            # Handle response based on user input
            if message_body.lower() in ["menu", "hi", "hello", "start", "reset"]:
                user_sessions[sender_id] = "menu"
                send_whatsapp_message(sender_id, get_menu_text())

            elif current_state == "menu" or current_state is None:
                if message_body == "1":
                    user_sessions[sender_id] = "diagnostics"
                    send_whatsapp_message(
                        sender_id,
                        "🚚 **Mercedes-Benz Heavy-Duty Vehicle Diagnostics**\n\n"
                        "Please provide your truck model (e.g., Actros, Axor) and describe the fault, symptom, or fault code."
                    )
                elif message_body == "2":
                    user_sessions[sender_id] = "general"
                    send_whatsapp_message(
                        sender_id,
                        "Thank you for reaching out! Your message has been received.\n\n"
                        "Peter will reply to you directly as soon as possible. "
                        "If urgent, feel free to call directly at 0722710633."
                    )
                else:
                    user_sessions[sender_id] = "menu"
                    send_whatsapp_message(sender_id, get_menu_text())

            elif current_state == "diagnostics":
                ai_reply = generate_ai_diagnostic_response(message_body)
                send_whatsapp_message(sender_id, ai_reply)

            elif current_state == "general":
                send_whatsapp_message(
                    sender_id,
                    "Message received. Peter will get back to you shortly!"
                )

        return jsonify({"status": "success"}), 200

    return "Not Found", 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
