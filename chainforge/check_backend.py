import requests
try:
    res = requests.post("http://localhost:8000/auth/register", json={
        "username": "user123_test3", 
        "password": "pwd", 
        "email": "user@test.com"
    })
    print("STATUS", res.status_code)
    print("TEXT", res.text)
except Exception as e:
    print("Failed to connect:", e)
