import requests

url = "http://127.0.0.1:5000/webhook/create_lead"

payload = {
    "name": "Lead from Local",
    "phone": "+923001234567",
    "email": "local@test.com"
}

res = requests.post(url, json=payload)
print("Status code:", res.status_code)
print("Response:", res.text)
