import requests
import sqlite3
import os

print("Sending 5 requests fast...")
for i in range(5):
    resp = requests.post("http://localhost:8000/transaction", json={
        "fromNodeId": "node-0",
        "text": f"test_multi_{i}"
    })
    print(f"Tx {i} Result:", resp.json())

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "node_node-0.sqlite")
conn = sqlite3.connect(db_path)
count = conn.execute("SELECT COUNT(*) FROM blocks").fetchone()[0]
conn.close()
print(f"DB Block Count: {count}")
