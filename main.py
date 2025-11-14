import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- CONFIG ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
VOICEFLOW_API_KEY = os.getenv("VOICEFLOW_API_KEY")

TELEGRAM_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
VOICEFLOW_URL = "https://general-runtime.voiceflow.com/state/user/{user_id}/interact"

VERSION_ID = "development"  # ou production


# =======================
#   ROUTE WEBHOOK
# =======================
@app.route("/", methods=["POST"])
def webhook():
    data = request.json

    if not data:
        return jsonify({"status": "no data"}), 200

    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        user_id = str(chat_id)
        user_message = data["message"].get("text", "")

        # ---- 1. Envoyer le message à Voiceflow ----
        vf_payload = {
            "request": {
                "type": "text",
                "payload": user_message
            }
        }

        headers = {
            "Authorization": f"Bearer {VOICEFLOW_API_KEY}",
            "versionID": VERSION_ID,
            "Content-Type": "application/json"
        }

        vf_response = requests.post(
            VOICEFLOW_URL.format(user_id=user_id),
            json=vf_payload,
            headers=headers
        )

        output = vf_response.json()

        # ---- 2. Extraire la réponse textuelle de Voiceflow ----
        response_text = ""

        # DM API 2024 format: { "trace": [ ... ] }
        if isinstance(output, dict) and "trace" in output:
            for trace in output["trace"]:
                if trace.get("type") == "text":
                    msg = trace["payload"].get("message", "")
                    response_text += msg + "\n"

        response_text = response_text.strip()

        # Si aucune réponse → fallback
        if not response_text:
            response_text = "Désolé, je n'ai pas compris 🐾"

        # ---- 3. Envoyer la réponse Telegram ----
        send_message(chat_id, response_text)

    return "ok", 200


# =======================
#    TELEGRAM SEND
# =======================
def send_message(chat_id, text):
    url = f"{TELEGRAM_URL}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    requests.post(url, json=payload)


# =======================
#    RUN LOCAL
# =======================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
