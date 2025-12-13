import requests
import json

url = "http://localhost:8000/chat"
headers = {"Content-Type": "application/json"}
data = {
    "user_id": "debug_user",
    "message": "gimme the summary of week 6",
    "conversation_history": [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there! How can I help you regarding Intelligent Systems?"}
    ]
}

print(f"Sending request to {url}...")
try:
    response = requests.post(url, headers=headers, json=data)
    print(f"Status Code: {response.status_code}")
    print("Response Body:")
    print(response.text)
except Exception as e:
    print(f"Request failed: {e}")
