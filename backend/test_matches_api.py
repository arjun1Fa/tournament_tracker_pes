import requests

url = "https://efootball-tracker.onrender.com/api/tournaments/4/matches"

try:
    print(f"Sending GET to {url}")
    response = requests.get(url)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text[:500]}")
except Exception as e:
    print(f"Error: {e}")
