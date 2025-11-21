import os
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

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
        raise Exception(res["error"])

    return res["result"]


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
        "description": "Lead created from Railway webhook"
    }

    lead_id = odoo_rpc("crm.lead", "create", [vals])

    return jsonify({
        "status": "ok",
        "lead_id": lead_id
    })


@app.route("/")
def home():
    return "Webhook is running!", 200


if __name__ == "__main__":
    app.run(port=5000, debug=True)
