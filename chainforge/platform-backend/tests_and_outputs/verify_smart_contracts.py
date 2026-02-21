import sys
import os
import io
import zipfile
import json
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

from schemas import Project, ProjectCreate
# Mocking strict schemas if needed, but Project is Pydantic model
from generator.builder import ChainBuilder

def verify_smart_contracts():
    print("Starting Smart Contracts Verification...")
    
    # 1. Define Mock Config
    config = {
        "networkType": "public",
        "publicConsensus": "pow",
        "smartContracts": [
            {
                "id": "contract_123",
                "name": "MyStorage",
                "type": "python",
                "code": "class MyStorage:\n    def set(self, value):\n        self.ctx.state['storage_value'] = value\n",
                "apiKey": "sk_test_123"
            },
            {
                "id": "contract_456",
                "name": "MyToken",
                "type": "solidity",
                "code": "// SPDX...",
                "apiKey": "sk_test_456"
            }
        ]
    }
    
    project = Project(
        id=1,
        owner_id=1,
        name="Test Chain",
        description="Test",
        config=config,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    # 2. Build Package
    builder = ChainBuilder(project)
    try:
        zip_bytes = builder.build_package()
        print("Package built successfully.")
    except Exception as e:
        print(f"FAILED to build package: {e}")
        return

    # 3. Inspect Zip
    with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as z:
        file_list = z.namelist()
        print(f"Zip contains {len(file_list)} files.")
        
        # Check Python Contract
        if "modules/smart_contracts/MyStorage.py" in file_list:
             print("[PASS] modules/smart_contracts/MyStorage.py exists")
        else:
             print("[FAIL] modules/smart_contracts/MyStorage.py MISSING")
             
        # Check Solidity Contract
        if "smart_contracts/MyToken.sol" in file_list:
             print("[PASS] smart_contracts/MyToken.sol exists")
        else:
             print("[FAIL] smart_contracts/MyToken.sol MISSING")
             
        # Check Routes
        if "api/contract_routes.py" in file_list:
            content = z.read("api/contract_routes.py").decode("utf-8")
            if "class_name = \"MyStorage\"" in content:
                 print("[PASS] api/contract_routes.py contains MyStorage logic")
            else:
                 print("[FAIL] api/contract_routes.py does not contain MyStorage logic")
                 print(content[:500])
        else:
            print("[FAIL] api/contract_routes.py MISSING")
            
        # Check Server
        if "api/server.py" in file_list:
            content = z.read("api/server.py").decode("utf-8")
            if "app.include_router(contract_routes.router" in content:
                print("[PASS] api/server.py includes contract router")
            else:
                print("[FAIL] api/server.py does not include contract router")
        else:
            print("[FAIL] api/server.py MISSING")
            return

    print("Extracting for execution test...")
    extract_dir = "test_extraction"
    with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as z:
        z.extractall(extract_dir)

    print("Running generated chain and testing execution...")
    try:
        sys.path.insert(0, os.path.abspath(extract_dir))
        
        # We simulate the initialization done in main.py
        import api.contract_routes as routes
        from core.chain import Blockchain
        from modules.vm.python_vm import PythonVM
        
        # Initialize chain with python VM
        runtime = PythonVM()
        chain = Blockchain(consensus=None, runtime=runtime)
        
        # Mock load routes since we are importing from a different directory 
        routes.contracts = {}
        # load manually
        import modules.smart_contracts.MyStorage as MyStorageModule
        routes.contracts["contract_123"] = MyStorageModule.MyStorage()
        
        # Link chain
        routes.set_chain(chain)

        # Call the endpoint handler function directly to simulate an HTTP post
        print("Simulating API call to execute smart contract...")
        response = routes.execute_contract("contract_123", "set", {"value": 42}, None)
        print(f"API Response: {response}")
        
        if response.get("status") == "queued":
             print("[PASS] Contract call was queued as transaction")
        else:
             print(f"[FAIL] Expected queued status, got: {response}")
        
        print(f"Pending transactions before mining: {len(chain.pending_transactions)}")
        if len(chain.pending_transactions) == 1:
            print("[PASS] Transaction added to pool successfully")
        
        # Mine the block
        chain.mine_pending_transactions("mock_miner")
        
        print(f"Pending transactions after mining: {len(chain.pending_transactions)}")
        print(f"Chain length: {len(chain.chain)}")
        
        print(f"Blockchain state: {chain.state}")
        if chain.state.get("storage_value") == 42:
            print("[PASS] Smart contract successfully updated blockchain state!")
        else:
            print("[FAIL] State was not updated by smart contract")
            
    except Exception as e:
        print(f"Execution Test Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_smart_contracts()
