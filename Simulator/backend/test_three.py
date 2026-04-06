import requests, sqlite3, os, time

log = []
def p(s): print(s); log.append(s)

# Reset network to clear DBs
requests.post("http://localhost:8000/reset")
time.sleep(1)

p("Adding node-1 as public...")
resp = requests.post("http://localhost:8000/nodes", json={"role": "validator"})
# In the simulator, main config might be consortium, so it needs voting.
# Let's bypass voting by forcing it? No, just use the reset network, and vote.

# This simulates the user adding a node and seeing the bug.
requests.post("http://localhost:8000/transaction", json={"fromNodeId": "node-0", "text": "tx1"})

with open("test3_log.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(log))
