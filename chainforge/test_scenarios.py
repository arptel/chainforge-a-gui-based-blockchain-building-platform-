import urllib.request
import urllib.parse
import json
import base64
import zipfile
import io
import os
import shutil

BASE_URL = "http://localhost:8000"
USERNAME = "testuser_automated"
PASSWORD = "testpassword123"

def make_request(method, endpoint, data=None, token=None):
    url = f"{BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    if data:
        json_data = json.dumps(data).encode("utf-8")
    else:
        json_data = None

    req = urllib.request.Request(url, data=json_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            if response.status == 204:
                return None
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.read().decode('utf-8')}")
        raise

def get_token():
    # Register (ignore if exists)
    try:
        make_request("POST", "/auth/register", {
            "username": USERNAME,
            "email": "test@example.com",
            "password": PASSWORD
        })
        print("Registered test user.")
    except:
        print("Test user likely already exists.")

    # Login
    url = f"{BASE_URL}/auth/token"
    data = urllib.parse.urlencode({
        "username": USERNAME,
        "password": PASSWORD
    }).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST")
    
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode("utf-8"))["access_token"]

def download_file(project_id, token):
    url = f"{BASE_URL}/generate/{project_id}/download"
    headers = {"Authorization": f"Bearer {token}"}
    req = urllib.request.Request(url, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as response:
            return response.read()
    except urllib.error.HTTPError as e:
        print(f"Download Error {e.code}: {e.read().decode('utf-8')}")
        raise

def verify_zip(zip_bytes, scenario_name, expected_modules):
    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            file_list = zf.namelist()
            print(f"[{scenario_name}] Zip contains {len(file_list)} files.")
            
            # Basic checks
            required_files = [
                "chain_core/api/server.py",
                "chain_core/p2p/node.py",
                "chain_core/state/ledger.py"
            ]
            
            missing = []
            for rf in required_files:
                if rf not in file_list:
                    missing.append(rf)
            
            # Check specific modules based on scenario
            # This relies on knowing how the builder structures the files.
            # Assuming 'chain_core/modules/consensus/...' etc.
            
            if missing:
                print(f"[{scenario_name}] FAILED: Missing core files: {missing}")
                return False
            
            print(f"[{scenario_name}] PASS: Core files present.")
            return True
            
    except zipfile.BadZipFile:
        print(f"[{scenario_name}] FAILED: Invalid Zip file.")
        return False

SCENARIOS = [
    {
        "name": "Scenario 1 (Public, PoW)",
        "config": {
            "networkType": "public",
            "publicConsensus": "pow",
            "publicRuntime": "wasm",
            "publicSyncMode": "full",
            "publicToken": "native",
            "publicDeployment": "zip"
        }
    },
    {
        "name": "Scenario 2 (Public, PoA, EVM)",
        "config": {
            "networkType": "public",
            "publicConsensus": "poa",
            "publicRuntime": "evm",
            "publicSyncMode": "fast",
            "publicToken": "none",
            "publicDeployment": "zip"
        }
    },
    {
        "name": "Scenario 3 (Permissioned, Centralized, Raft)",
        "config": {
            "networkType": "permissioned",
            "permissionedType": "centralized",
            "centralizedAuthority": "fixed",
            "centralizedConsensus": "raft",
            "centralizedAccess": "rbac",
            "centralizedSync": "realtime",
            "centralizedDeployment": "zip"
        }
    },
    {
        "name": "Scenario 4 (Permissioned, Consortium, PBFT)",
        "config": {
            "networkType": "permissioned",
            "permissionedType": "consortium",
            "consortiumValidatorStruct": "equal",
            "consortiumConsensus": "pbft",
            "consortiumIdentity": "ca",
            "consortiumSync": "full",
            "consortiumDeployment": "zip"
        }
    }
]

def run_tests():
    print("Starting Test Scenarios...")
    try:
        token = get_token()
        print("Authentication successful.")
    except Exception as e:
        print(f"Authentication failed: {e}")
        return

    for scenario in SCENARIOS:
        print(f"\nRunning {scenario['name']}...")
        try:
            # 1. Create Project
            project_data = {
                "name": f"Test_{scenario['name'].replace(' ', '_').replace('(', '').replace(')', '').replace(',', '')}",
                "config": scenario['config']
            }
            project = make_request("POST", "/projects/", project_data, token)
            project_id = project["id"]
            print(f"Project created with ID: {project_id}")

            # 2. Download Zip
            zip_bytes = download_file(project_id, token)
            print(f"Downloaded {len(zip_bytes)} bytes.")

            # 3. Verify
            if verify_zip(zip_bytes, scenario['name'], []):
                # Save locally for manual inspection (optional, user asked to download at specific path)
                # s2: download a zip file at "C:\Users\ARTH PATEL\OneDrive\Desktop\ARTH\Sem-6"
                target_dir = r"C:\Users\ARTH PATEL\OneDrive\Desktop\ARTH\Sem-6"
                filename = f"ChainForge_Test_{project_id}.zip"
                full_path = os.path.join(target_dir, filename)
                
                with open(full_path, "wb") as f:
                    f.write(zip_bytes)
                print(f"Saved to {full_path}")
                
                # s4: deelte the zip
                os.remove(full_path)
                print("Deleted zip file.")
                
            else:
                print(f"[{scenario['name']}] Verification FAILED.")

        except Exception as e:
            print(f"[{scenario['name']}] EXCEPTION: {e}")

if __name__ == "__main__":
    run_tests()
