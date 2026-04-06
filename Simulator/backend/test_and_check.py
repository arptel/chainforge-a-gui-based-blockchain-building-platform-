import requests
import sqlite3
import os

print("Sending 1 request...")
resp = requests.post("http://localhost:8000/transaction", json={
    "fromNodeId": "node-0",
    "text": "test_persistent_tx"
})
print("Result:", resp.json())

# Check DB
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "node_node-0.sqlite")
conn = sqlite3.connect(db_path)
count = conn.execute("SELECT COUNT(*) FROM blocks").fetchone()[0]
rows = conn.execute("SELECT idx, hash FROM blocks ORDER BY idx").fetchall()
conn.close()

print(f"DB Block Count: {count}")
for r in rows:
    print(f"  - Block {r[0]}: {r[1]}")
