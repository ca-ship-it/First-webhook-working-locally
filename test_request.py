import requests

url = "https://web-production-19e3.up.railway.app/webhook/create_lead"

payload = {
    "name": "Lead from Railway LIVE",
    "phone": "+923001234567",
    "email": "railway@test.com"
}

res = requests.post(url, json=payload)
print("Status code:", res.status_code)
print("Response:", res.text)
