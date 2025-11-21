import os
import requests
from flask import Flask, request, jsonify, Response
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# ---------- ODOO CONFIG ----------
ODOO_URL = os.getenv("ODOO_URL")
DB = os.getenv("ODOO_DB")
UID = int(os.getenv("ODOO_UID"))
API_KEY = os.getenv("ODOO_API_KEY")


def odoo_rpc(model, method, args=None, kwargs=None):
    if args is None:
        args = []
    if kwargs is None:
        kwargs = {}

    payload = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "service": "object",
            "method": "execute_kw",
            "args": [
                DB,
                UID,
                API_KEY,
                model,
                method,
                args,
                kwargs,
            ],
        },
    }

    res = requests.post(f"{ODOO_URL}/jsonrpc", json=payload).json()
    if "error" in res:
        print("ODOO ERROR:", res["error"])
        raise Exception(res["error"])
    return res["result"]


# ---------- OLD LEAD WEBHOOK (WORKING) ----------
@app.route("/webhook/create_lead", methods=["POST"])
def create_lead():
    data = request.json or {}

    name = data.get("name", "No Name")
    phone = data.get("phone")
    email = data.get("email")

    vals = {
        "name": name,
        "phone": phone,
        "email_from": email,
        "description": "Lead created from webhook",
    }

    lead_id = odoo_rpc("crm.lead", "create", [vals])

    return jsonify({"status": "ok", "lead_id": lead_id})


# ---------- INSTAGRAM WEBHOOK ----------
@app.route("/ig/webhook", methods=["GET", "POST"])
def ig_webhook():
    # 1) VERIFY STEP (jab Meta webhook set karega)
    if request.method == "GET":
        verify_token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if verify_token == os.getenv("VERIFY_TOKEN"):
            return challenge or ""
        return "Verification token mismatch", 403

    # 2) REAL MESSAGES
    data = request.json
    print("📩 Incoming IG webhook:", data)

    try:
        entry = data.get("entry", [])[0]
        messaging = entry.get("messaging", [])[0]

        sender_id = messaging["sender"]["id"]
        message = messaging.get("message", {})
        text = message.get("text", "")

        print("Sender:", sender_id, "Text:", text)

        # Odoo me lead create
        vals = {
            "name": f"IG Lead - {sender_id}",
            "phone": "",
            "email_from": "",
            "description": f"Insta DM: {text}",
        }
        lead_id = odoo_rpc("crm.lead", "create", [vals])
        print("✅ Odoo lead from IG:", lead_id)

        # Auto reply
        reply_text = "Thanks for your message! Our team will get back to you shortly."
        send_ig_reply(sender_id, reply_text)

    except Exception as e:
        print("⚠️ Error handling IG message:", e)

    return "EVENT_RECEIVED", 200


def send_ig_reply(recipient_id, text):
    PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
    if not PAGE_ACCESS_TOKEN:
        print("⚠️ PAGE_ACCESS_TOKEN missing")
        return

    url = f"https://graph.facebook.com/v18.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"

    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text},
    }

    res = requests.post(url, json=payload)
    print("IG reply status:", res.status_code, res.text)


# ---------- HEALTH CHECK ----------
@app.route("/")
def home():
    return "Webhook is running!", 200


if __name__ == "__main__":
    app.run(port=5000, debug=True)
