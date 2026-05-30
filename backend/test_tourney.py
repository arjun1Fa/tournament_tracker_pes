import requests

url_login = "https://efootball-tracker.onrender.com/api/auth/login"
data_login = {
    "email": "winternx135@gmail.com",
    "password": "WinterFA2026!"
}

try:
    print("Logging in...")
    r1 = requests.post(url_login, json=data_login)
    token = r1.json().get("access_token")
    
    url_tourney = "https://efootball-tracker.onrender.com/api/tournaments"
    headers = {"Authorization": f"Bearer {token}"}
    data_tourney = {
        "name": "Test Render Tournament",
        "format": "efl",
        "is_public": True
    }
    
    print("Creating tournament...")
    r2 = requests.post(url_tourney, headers=headers, json=data_tourney)
    print(f"Status Code: {r2.status_code}")
    print(f"Response: {r2.text}")
    
except Exception as e:
    print(f"Error: {e}")
