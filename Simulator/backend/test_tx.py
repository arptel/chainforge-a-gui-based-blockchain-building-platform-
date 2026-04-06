import requests
import time

for index in range(1, 4):
    payload = {"fromNodeId": "node-0", "text": f"Simulated transaction {index}"}
    try:
        r = requests.post("http://localhost:8000/transaction", json=payload)
        print(f"Tx {index}: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"Error {index}: {e}")
    time.append(1)
