import requests
import uuid
import sys

BASE_URL = "http://localhost:8000"

def test_full_flow():
    # 1. Register & Login
    username = str(uuid.uuid4())[:8]
    password = "password123!"
    
    print(f"Registering user {username}...")
    res = requests.post(f"{BASE_URL}/auth/register", json={
        "username": username,
        "email": f"{username}@example.com",
        "password": password
    })
    if res.status_code != 200:
        print(f"Registration Failed: {res.text}")
        sys.exit(1)
        
    print("Logging in...")
    res = requests.post(f"{BASE_URL}/auth/token", data={
        "username": username,
        "password": password
    })
    if res.status_code != 200:
        print(f"Login Failed: {res.text}")
        sys.exit(1)
        
    token = res.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    print("Login successful.")

    # 2. Get Default Contracts
    print("Fetching default contracts based on partial config...")
    partial_config = {"networkType": "public", "publicConsensus": "pow", "publicToken": "native"}
    res = requests.post(f"{BASE_URL}/generate/default-contracts", json=partial_config, headers=headers)
    if res.status_code != 200:
        print(f"Fetch Default Contracts Failed: {res.status_code} - {res.text}")
        sys.exit(1)
        
    contracts = res.json().get("contracts", [])
    print(f"Success! Found {len(contracts)} default contracts.")

    # 3. Create Project
    print("Creating Blockchain Project...")
    project_payload = {
         "name": f"TestChain-{username}",
         "description": "E2E testing generated chain.",
         "config": {
             **partial_config,
             "publicSyncMode": "full",
             "nodeCount": 3,
             "consensus": "pow",
             "governance": "centralized",
             "smartContracts": contracts
         }
    }
    res = requests.post(f"{BASE_URL}/projects/", json=project_payload, headers=headers)
    if res.status_code != 200:
        print(f"Create Project Failed: {res.status_code} - {res.text}")
        sys.exit(1)
        
    print("Project creation response:", res.text)
    project_id = res.json().get("id")
    print(f"Project created with ID: {project_id}")

    # 4. Download / Generate
    print("Generating & downloading blockchain ZIP...")
    res = requests.post(f"{BASE_URL}/generate/{project_id}/download", headers=headers)
    if res.status_code != 200:
        print(f"Download Failed: {res.status_code} - {res.text}")
        sys.exit(1)
        
    with open("output.zip", "wb") as f:
        f.write(res.content)
        
    print("SUCCESS: Zip downloaded, size:", len(res.content), "bytes.")

if __name__ == "__main__":
    test_full_flow()
