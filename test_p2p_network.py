import subprocess
import time
import requests
import os

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_SCRIPT = os.path.join(BASE_DIR, "chainforge", "templates", "chain_core", "main.py")

print("Starting P2P Network Simulation...")

full_node = subprocess.Popen(["python", MAIN_SCRIPT, "--port", "5000", "--api-port", "8000", "--role", "full"])
time.sleep(2) 

miner_node = subprocess.Popen(["python", MAIN_SCRIPT, "--port", "5001", "--api-port", "8001", "--role", "miner", "--peers", "http://localhost:8000"])
time.sleep(2)

light_node = subprocess.Popen(["python", MAIN_SCRIPT, "--port", "5002", "--api-port", "8002", "--role", "light", "--peers", "http://localhost:8001"])
time.sleep(2)

print("\n--- Network is up! ---\n")

try:
    print("Submitting transaction to Full Node...")
    tx = {
        "sender": "college_abc",
        "action": "issue_certificate",
        "data": "Degree for John Doe"
    }
    res = requests.post("http://localhost:8000/transactions", json=tx)
    print("Full Node Response:", res.json())
    
    print("Attempting to submit transaction directly to Light Node (Should fail)...")
    res = requests.post("http://localhost:8002/transactions", json=tx)
    print("Light Node Response:", res.json())

    print("\nWaiting 10 seconds for transactions to be gossiped and mined...")
    for i in range(10):
        print(f"Waiting... {10-i}s")
        time.sleep(1)

    print("\n--- Verifying Blockchains ---")
    
    res = requests.get("http://localhost:8000/blocks")
    full_blocks = res.json()
    print(f"Full Node blocks count: {len(full_blocks)}")
    if len(full_blocks) > 1:
        print(f"Full Node latest block transactions: {full_blocks[-1].get('transactions')}")

    res = requests.get("http://localhost:8002/blocks")
    light_blocks = res.json()
    print(f"\nLight Node blocks count: {len(light_blocks)}")
    if len(light_blocks) > 1:
        print(f"Light Node latest block transactions (Should be empty!): {light_blocks[-1].get('transactions')}")

    print("\nSimulation Complete!")

except Exception as e:
    print(f"Error during simulation: {e}")

finally:
    print("\nShutting down nodes...")
    full_node.terminate()
    miner_node.terminate()
    light_node.terminate()
