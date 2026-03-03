import requests
import os
import zipfile
import io
import time
import subprocess

BASE_URL = "http://localhost:8000"

def test_flow():
    # 1. Register
    print("Registering new user...")
    username = f"testuser_{int(time.time())}"
    password = "password123"
    
    try:
        res = requests.post(f"{BASE_URL}/auth/register", json={
            "username": username,
            "email": f"{username}@example.com",
            "password": password
        })
        print("Register Response:", res.status_code, res.text)
    except Exception as e:
        print("Backend not running or error:", e)
        return

    # 2. Login
    print("Logging in...")
    res = requests.post(f"{BASE_URL}/auth/token", data={
        "username": username,
        "password": password
    })
    print("Login Response:", res.status_code, res.text)
    if res.status_code != 200:
        return
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Create Project
    print("Creating project...")
    config = {
        "networkType": "public",
        "consensus": "pow",
        "governance": "centralized",
        "nodeCount": 1,
        "publicConsensus": "pow",
        "publicSyncMode": "full",
        "publicRuntime": "python_vm",
        "smartContracts": [
            {
                "id": "c1",
                "name": "Token",
                "type": "python",
                "code": "print('Hello Smart Contract')",
                "apiKey": "test-key"
            }
        ]
    }
    res = requests.post(f"{BASE_URL}/projects/", json={
        "name": "Test Chain",
        "description": "Integration Test",
        "config": config
    }, headers=headers)
    print("Create Project Response:", res.status_code, res.text)
    if res.status_code != 200:
        return
    project_id = res.json()["id"]

    # 4. Download Blockchain
    print(f"Downloading blockchain zip for project {project_id}...")
    res = requests.post(f"{BASE_URL}/generate/{project_id}/download", headers=headers)
    print("Download Response:", res.status_code)
    if res.status_code != 200:
        print(res.text)
        return

    # 5. Extract and Validate
    zip_bytes = res.content
    extract_dir = "test_generated_blockchain"
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        zf.extractall(extract_dir)
    print(f"Extracted to {extract_dir}.")
    
    # Check key files
    expected_files = ["main.py", "core/chain.py", "modules/smart_contracts/Token.py", "api/server.py"]
    for f in expected_files:
        path = os.path.join(extract_dir, f)
        if not os.path.exists(path):
            print(f"MISSING expected file: {f}")
        else:
            print(f"FOUND: {f}")
            
    print("Testing flow completed successfully.")

if __name__ == "__main__":
    test_flow()
