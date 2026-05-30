import requests

url = "https://efootball-tracker.onrender.com/api/auth/login"
data = {
    "email": "winternx135@gmail.com",
    "password": "WinterFA2026!"
}

try:
    print(f"Sending POST to {url}")
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
