import asyncio
import httpx
import sqlite3
import subprocess
import time
import os
import glob

API_URL = "http://localhost:8001"
BASE_DIR = r"c:\Users\ARTH PATEL\OneDrive\Desktop\ARTH\Sem-6\Blockchain"
CERT_SYS_DIR = os.path.join(BASE_DIR, "certificate_verification_system")
BACKEND_DIR = os.path.join(CERT_SYS_DIR, "backend")
NODE_DIR = os.path.join(CERT_SYS_DIR, "chainforge_node")

# Define our 3 target database paths
DB1_PATH = os.path.join(CERT_SYS_DIR, "college1.sqlite")
DB2_PATH = os.path.join(BASE_DIR, "college2.sqlite")
DB3_PATH = os.path.join(CERT_SYS_DIR, "data", "college3.sqlite")

def clean_old_dbs():
    for f in [DB1_PATH, DB2_PATH, DB3_PATH]:
        if os.path.exists(f): os.remove(f)
    for db in glob.glob(os.path.join(CERT_SYS_DIR, "data", "*.sqlite")) + glob.glob(os.path.join(BACKEND_DIR, "data", "*.sqlite")):
        try: os.remove(db)
        except: pass

def check_db_state(path, alias):
    if not os.path.exists(path): return f"{alias}: MISSING"
    try:
        conn = sqlite3.connect(path)
        count = conn.execute("SELECT COUNT(*) FROM state WHERE key LIKE 'cert_%'").fetchone()[0]
        conn.close()
        return f"{alias}: {count} certs"
    except Exception as e: return f"{alias}: ERROR {e}"

async def run_test():
    print("🧹 Cleaning old databases...")
    clean_old_dbs()
    
    print("🚀 Starting Backend...")
    backend_proc = subprocess.Popen(["uvicorn", "main:app", "--port", "8001"], cwd=BACKEND_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    print("🚀 Starting Bootstrap Node A (8080)...")
    node_a_log = open(os.path.join(CERT_SYS_DIR, "node_a_debug.log"), "w")
    node_a = subprocess.Popen(["python", "-u", "main.py", "--api-port", "8080", "--port", "5000", "--db-path", "../data/node_a.sqlite"], cwd=NODE_DIR, stdout=node_a_log, stderr=subprocess.STDOUT)
    
    time.sleep(5) # Let servers spin up
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        colleges = [
            ("college1", DB1_PATH),
            ("college2", DB2_PATH),
            ("college3", DB3_PATH)
        ]
        
        for username, path in colleges:
            print(f"📥 Registering {username} at [{path}]...")
            res = await client.post(f"{API_URL}/auth/register", json={
                "username": username,
                "password": "password123",
                "db_path": path
            })
            if res.status_code != 200:
                print(f"❌ Failed to register {username}: {res.text}")
                return
            time.sleep(3) # Wait for node to boot and connect
            
        print("✅ All 3 nodes registered and booted!")
        
        # Login to college1
        res = await client.post(f"{API_URL}/auth/login", json={"username": "college1", "password": "password123"})
        token = res.json()["access_token"]
        
        # Issue a certificate
        print("\n🎓 Issuing certificate from college1...")
        res = await client.post(f"{API_URL}/api/issue", json={
            "cert_id": "CERT-XYZ-999",
            "student_name": "Alice Blockchain",
            "degree": "B.S. Network Gossip",
            "year": 2026
        }, headers={"Authorization": f"Bearer {token}"})
        
        if res.status_code == 200:
            print("✅ Certificate broadcasted! Waiting 6 seconds for PBFT consensus and P2P Gossip propagation...\n")
        else:
            print(f"❌ Failed to issue cert: {res.text}")
            return
            
        time.sleep(6)
        
        print("🔍 Verifying final blockchain states across distinct folders:")
        print("  " + check_db_state(os.path.join(CERT_SYS_DIR, "data", "node_a.sqlite"), "Bootstrap Node A"))
        print("  " + check_db_state(DB1_PATH, "College 1 (cert sys folder)"))
        print("  " + check_db_state(DB2_PATH, "College 2 (blockchain folder)"))
        print("  " + check_db_state(DB3_PATH, "College 3 (data folder)"))
        
    print("\n🧹 Cleaning up processes...")
    subprocess.run(["taskkill", "/F", "/T", "/PID", str(backend_proc.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["taskkill", "/F", "/T", "/PID", str(node_a.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("🎉 Done!")

if __name__ == "__main__":
    asyncio.run(run_test())
