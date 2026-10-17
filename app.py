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
        "Welcome to *Automac Technical Solutions*! 🛠️\n"
        "Your trusted Mercedes-Benz Heavy-Duty Truck & Technical Engineering Hub.\n\n"
        "How can we assist you today? Please reply with a number:\n\n"
        "1️⃣ Mercedes-Benz Truck Diagnostics & Fault Codes\n"
        "2️⃣ Purchase Digital Training Guides & Technical Manuals\n"
        "3️⃣ Technical Consultations & Remote Diagnostic Support\n"
        "4️⃣ Technician Training Programs & Skill Modules\n"
        "5️⃣ General Inquiry / Direct Contact with Peter\n\n"
        "Reply with 1, 2, 3, 4, or 5 to proceed."
    )

def generate_ai_diagnostic_response(user_query):
    """Generates heavy-duty truck diagnostic response using GPT-4o."""
    system_prompt = (
        "You are an expert Mercedes-Benz Heavy-Duty Truck Diagnostic Specialist representing "
        "Automac Technical Solutions in Kenya. "
        "Provide precise diagnostic guidance for models like Actros, Axor, Atego, and Arocs. "
        "Include fault code meanings, component locations, pinout data or ASCII diagrams when helpful, "
        "and troubleshooting steps. Always advise contacting Peter Kagio directly at 0722710633 for hands-on assistance "
        "or booking full diagnostic consultations."
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
        return "An error occurred while generating diagnostic data. Please contact Peter Kagio directly at 0722710633."

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

            if message_body.lower() in ["menu", "hi", "hello", "start", "reset", "automac"]:
                user_sessions[sender_id] = "menu"
                send_whatsapp_message(sender_id, get_menu_text())

            elif current_state == "menu" or current_state is None:
                if message_body == "1":
                    user_sessions[sender_id] = "diagnostics"
                    send_whatsapp_message(
                        sender_id,
                        "🚚 *Automac Diagnostic Assistant*\n\n"
                        "Please state your Mercedes-Benz truck model (e.g., Actros, Axor) and describe the fault code or symptom."
                    )
                elif message_body == "2":
                    user_sessions[sender_id] = "menu"
                    send_whatsapp_message(
                        sender_id,
                        "📚 *Automac Digital Training Materials*\n\n"
                        "We offer practical 10-module training guides for Mercedes truck technicians.\n\n"
                        "🔗 Access materials here: https://linktr.ee/automac.ke\n\n"
                        "Reply *MENU* to return to the main menu."
                    )
                elif message_body == "3":
                    user_sessions[sender_id] = "menu"
                    send_whatsapp_message(
                        sender_id,
                        "💻 *Technical Consultations & Remote Support*\n\n"
                        "Peter Kagio offers specialized virtual/remote diagnostic sessions using DAS/Xentry and ThinkDiag tools.\n\n"
                        "To schedule a session, call or message directly at +254 722 710 633.\n\n"
                        "Reply *MENU* to return to the main menu."
                    )
                elif message_body == "4":
                    user_sessions[sender_id] = "menu"
                    send_whatsapp_message(
                        sender_id,
                        "🎓 *Automac Technician Training Programs*\n\n"
                        "Enhance your technical skills with our structured heavy-duty automotive training modules.\n\n"
                        "Contact Peter at 0722710633 for upcoming schedule and enrollment details.\n\n"
                        "Reply *MENU* to return to the main menu."
                    )
                elif message_body == "5":
                    user_sessions[sender_id] = "general"
                    send_whatsapp_message(
                        sender_id,
                        "Thank you for reaching out to Peter Kagio at Automac Technical Solutions.\n\n"
                        "Your message has been logged, and Peter will get back to you shortly."
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
                    "Message received! Peter will respond as soon as possible."
                )

        return jsonify({"status": "success"}), 200

    return "Not Found", 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
