import requests, sqlite3, os, time

log = []
def p(s):
    print(s)
    log.append(s)

p("Sending 1 tx (Node-0 only)...")
resp = requests.post("http://localhost:8000/transaction", json={"fromNodeId": "node-0", "text": "tx 1"})
p(f"Tx 1: {resp.json()}")

p("Adding node-1...")
resp = requests.post("http://localhost:8000/nodes", json={"role": "validator"})
join_data = resp.json()
p(f"Join: {join_data}")

if join_data.get("status") == "pending":
    req_id = join_data["request_id"]
    p(f"Approving join request {req_id}...")
    resp = requests.post("http://localhost:8000/nodes/vote", json={
        "voterNodeId": "node-0",
        "requestId": req_id,
        "approve": True
    })
    p(f"Vote: {resp.json()}")

time.sleep(1)

p("Sending next tx (Now 2 nodes in network)...")
resp = requests.post("http://localhost:8000/transaction", json={"fromNodeId": "node-0", "text": "tx 2"})
p(f"Tx 2: {resp.json()}")

time.sleep(1)

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "node_node-0.sqlite")
conn = sqlite3.connect(db_path)
count = conn.execute("SELECT COUNT(*) FROM blocks").fetchone()[0]
conn.close()
p(f"DB Block Count node-0: {count}")

with open("test2_log.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(log))
