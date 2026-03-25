import asyncio
import httpx
import sqlite3
import subprocess
import time
import os

API_URL = "http://localhost:8001"
DATA_DIR = r"c:\Users\ARTH PATEL\OneDrive\Desktop\ARTH\Sem-6\Blockchain\certificate_verification_system\data"
BACKEND_DIR = r"c:\Users\ARTH PATEL\OneDrive\Desktop\ARTH\Sem-6\Blockchain\certificate_verification_system\backend"
NODE_DIR = r"c:\Users\ARTH PATEL\OneDrive\Desktop\ARTH\Sem-6\Blockchain\certificate_verification_system\chainforge_node"

def check_db_state(db_name):
    path = os.path.join(DATA_DIR, db_name)
    if not os.path.exists(path): return 0
    try:
        conn = sqlite3.connect(path)
        count = conn.execute("SELECT COUNT(*) FROM state WHERE key LIKE 'cert_%'").fetchone()[0]
        conn.close()
        return count
    except: return 0

async def run_test():
    print("Starting E2E Sync Test...")
    
    # Wipe DBs for clean run
    import glob
    for db in glob.glob(os.path.join(DATA_DIR, "*.sqlite")) + glob.glob(os.path.join(BACKEND_DIR, "data", "*.sqlite")):
        try: os.remove(db)
        except: pass
    
    # Start Backend
    print("Starting Backend...")
    backend_proc = subprocess.Popen(["uvicorn", "main:app", "--port", "8001"], cwd=BACKEND_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Start Node A & B
    print("Starting Node A & B...")
    node_a = subprocess.Popen(["python", "main.py", "--api-port", "8080", "--port", "5000", "--db-path", "../data/node_a.sqlite"], cwd=NODE_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    node_b = subprocess.Popen(["python", "main.py", "--api-port", "8081", "--port", "5001", "--peers", "127.0.0.1:8080", "--db-path", "../data/node_b.sqlite"], cwd=NODE_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    time.sleep(6) # Wait for startup
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        colleges = []
        for i in range(1, 4):
            print(f"Registering College {i}...")
            res = await client.post(f"{API_URL}/auth/register", json={
                "username": f"college_{i}",
                "password": "password123",
                "db_path": f"../data/college_{i}.sqlite"
            })
            if res.status_code != 200:
                print(f"Register failed: {res.text}")
                res.raise_for_status()
            data = res.json()
            time.sleep(3) # Give node time to boot and sync
            
            # Login to get token
            res = await client.post(f"{API_URL}/auth/login", json={
                "username": f"college_{i}", "password": "password123"
            })
            token = res.json()["access_token"]
            
            # Issue a certificate
            print(f"Issuing certificate from College {i}...")
            cert_id = f"CERT-TEST-{i}000"
            await client.post(f"{API_URL}/api/issue", json={
                "cert_id": cert_id,
                "student_name": f"Student {i}",
                "degree": f"Degree {i}",
                "year": 2026
            }, headers={"Authorization": f"Bearer {token}"})
            
            time.sleep(5) # Wait for PBFT consensus and block mining
            
        print("\nChecking state sync across all nodes:")
        for db in ["node_a.sqlite", "node_b.sqlite", "college_1.sqlite", "college_2.sqlite", "college_3.sqlite"]:
            print(f"  {db}: {check_db_state(db)} certs")
            
        print("\nNow registering a late College 4 to test historical sync...")
        res = await client.post(f"{API_URL}/auth/register", json={
            "username": "college_4",
            "password": "password123",
            "db_path": "../data/college_4.sqlite"
        })
        time.sleep(6)
        print(f"  college_4.sqlite: {check_db_state('college_4.sqlite')} certs")
        
    print("\nCleaning up processes...")
    subprocess.run(["taskkill", "/F", "/T", "/PID", str(backend_proc.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["taskkill", "/F", "/T", "/PID", str(node_a.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["taskkill", "/F", "/T", "/PID", str(node_b.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("Done!")

if __name__ == "__main__":
    asyncio.run(run_test())
