import requests
import json

url = "http://127.0.0.1:8000/feedback"
headers = {"Content-Type": "application/json"}
data = {
    "score": 4,
    "user_id": "test-user-456",
    "session_id": "test-session-456",
    "text": "Great response!"
}

try:
    response = requests.post(url, headers=headers, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {response.headers}")
    print(f"Content: {response.text}")
except Exception as e:
    print(f"Error: {e}")
