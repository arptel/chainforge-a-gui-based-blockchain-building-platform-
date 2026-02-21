import shutil
import os
import json
import schemas
import zipfile
import io

TEMPLATE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../templates/chain_core"))

class ChainBuilder:
    def __init__(self, project: schemas.Project):
        self.project = project
        self.config = project.config

    def build_package(self) -> bytes:
        """
        Generates the blockchain source code and returns a ZIP file as bytes.
        """
        bio = io.BytesIO()
        with zipfile.ZipFile(bio, "w", zipfile.ZIP_DEFLATED) as zip_file:
             for root, dirs, files in os.walk(TEMPLATE_DIR):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, TEMPLATE_DIR)
                    # Skip files we want to overwrite
                    if arcname.replace("\\", "/") == "api/server.py":
                        continue
                    zip_file.write(file_path, arcname)
                    
             # Add a specific config file
             config_json = json.dumps(self.config, indent=4)
             zip_file.writestr("config/genesis.json", config_json)

            # Smart Contracts
             contracts = self.config.get('smartContracts', [])
             has_contracts = len(contracts) > 0
             
             if has_contracts:
                 from .solidity_transpiler import transpile
                 
                 zip_file.writestr("modules/smart_contracts/__init__.py", "")
                 for c in contracts:
                     # Transpile Solidity to Python if necessary
                     safe_name = "".join(x for x in c['name'] if x.isalnum() or x == "_")
                     if not safe_name: safe_name = f"Contract_{c['id']}"

                     if c['type'] == 'solidity':
                         try:
                             print(f"Transpiling Solidity contract {safe_name} via LLM...")
                             c['code'] = transpile(c['code'], safe_name)
                             c['type'] = 'python' # Trick the rest of the generator
                         except Exception as e:
                             print(f"Failed to transpile {safe_name}: {e}")
                             # Fallback to keeping it as solidity and using mock wrapper
                             
                     if c['type'] == 'python':
                         zip_file.writestr(f"modules/smart_contracts/{safe_name}.py", c['code'])
                     else:
                         zip_file.writestr(f"smart_contracts/{safe_name}.sol", c['code'])
                 
                 # Generate Routes
                 routes_code = self._generate_routes(contracts)
                 zip_file.writestr("api/contract_routes.py", routes_code)
                 
                 # Generate SDK
                 zip_file.writestr("sdk/__init__.py", "")
                 zip_file.writestr("sdk/config.py", 'API_BASE_URL = "http://localhost:8000"\n')
                 client_code = self._generate_sdk_client(contracts)
                 zip_file.writestr("sdk/client.py", client_code)
                 
                 js_client_code = self._generate_js_sdk_client(contracts)
                 zip_file.writestr("sdk/client.js", js_client_code)

             # Generate Server
             server_code = self._generate_server(has_contracts)
             zip_file.writestr("api/server.py", server_code)

        bio.seek(0)
        return bio.getvalue()

    def _generate_sdk_client(self, contracts):
        code = """import requests
from .config import API_BASE_URL

class SmartContract:
    def __init__(self, contract_id, api_key):
        self.contract_id = contract_id
        self.api_key = api_key
        self.base_url = f"{API_BASE_URL}/api/v1/contracts/execute/{contract_id}"

    def _call(self, method, **kwargs):
        headers = {"x-api-key": self.api_key}
        payload = {"args": kwargs}
        response = requests.post(f"{self.base_url}/{method}", json=payload, headers=headers)
        if response.status_code == 200:
            return response.json().get("result")
        else:
            raise Exception(f"Error {response.status_code}: {response.text}")

    def __getattr__(self, name):
        def method(**kwargs):
            return self._call(name, **kwargs)
        return method

"""
        # Generate wrapper classes for each contract
        for c in contracts:
            if c['type'] == 'python':
                safe_name = "".join(x for x in c['name'] if x.isalnum() or x == "_")
                code += f"""
class {safe_name}Wrapper(SmartContract):
    def __init__(self):
        super().__init__("{c['id']}", "{c['apiKey']}")

    # Note: We can't statically know methods without parsing AST, 
    # so we use __getattr__ for dynamic method calls or generate specific ones if we parsed it.
    # For now, we'll use __getattr__ to catch any method call and forward it.
    
    def __getattr__(self, name):
        def method(**kwargs):
            return self._call(name, **kwargs)
        return method
"""

        code += """
class Client:
    def __init__(self, base_url=None):
        if base_url:
            global API_BASE_URL
            API_BASE_URL = base_url
"""
        for c in contracts:
            safe_name = "".join(x for x in c['name'] if x.isalnum() or x == "_")
            if c['type'] == 'python':
                code += f"        self.{safe_name} = {safe_name}Wrapper()\n"
            elif c['type'] == 'solidity':
                # Solidity contracts use a generic wrapper in this MVP
                code += f"        self.{safe_name} = SmartContract('{c['id']}', '{c['apiKey']}')\n"

        return code

    def _generate_js_sdk_client(self, contracts):
        code = """class SmartContract {
    constructor(contractId, apiKey, baseUrl) {
        this.contractId = contractId;
        this.apiKey = apiKey;
        this.baseUrl = `${baseUrl}/api/v1/contracts/execute/${contractId}`;
    }

    async _call(method, args = {}) {
        const response = await fetch(`${this.baseUrl}/${method}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'x-api-key': this.apiKey
            },
            body: JSON.stringify({ args: args })
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Error ${response.status}: ${errorText}`);
        }
        
        const data = await response.json();
        return data.result;
    }
}

function createContractProxy(contractId, apiKey, baseUrl) {
    const contract = new SmartContract(contractId, apiKey, baseUrl);
    return new Proxy(contract, {
        get(target, prop) {
            if (prop in target) {
                return target[prop];
            }
            return async (args = {}) => {
                return await target._call(prop, args);
            };
        }
    });
}

export class ChainForgeClient {
    constructor(baseUrl = "http://localhost:8000") {
        this.baseUrl = baseUrl;
"""
        for c in contracts:
            safe_name = "".join(x for x in c['name'] if x.isalnum() or x == "_")
            code += f'        this.{safe_name} = createContractProxy("{c["id"]}", "{c["apiKey"]}", this.baseUrl);\n'
        
        code += """    }
}
"""
        return code

    def _generate_routes(self, contracts):
        code = """from fastapi import APIRouter, HTTPException, Header
from typing import Optional, Dict, Any
import importlib
import sys
import os

router = APIRouter()

# Helper to load contracts dynamically
contracts = {}

def load_contracts():
    sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
"""
        # Generate loader logic
        for c in contracts:
            if c['type'] == 'python':
                safe_name = "".join(x for x in c['name'] if x.isalnum() or x == "_")
                if not safe_name: safe_name = f"Contract_{c['id']}"
                code += f"""
    try:
        module = importlib.import_module("modules.smart_contracts.{safe_name}")
        class_name = "{safe_name}"
        if hasattr(module, class_name):
            contracts["{c['id']}"] = getattr(module, class_name)()
        else:
             for attr_name in dir(module):
                 attr = getattr(module, attr_name)
                 if isinstance(attr, type) and attr.__module__ == module.__name__:
                     contracts["{c['id']}"] = attr()
                     break
    except Exception as e:
        print(f"Failed to load contract {safe_name}: {{e}}")
"""
            elif c['type'] == 'solidity':
                # Register a Mock/Generic handler for Solidity
                code += f"""
    # Mock/Generic handler for Solidity contract {c['name']}
    class MockSolidityContract_{c['id']}:
        def __getattr__(self, name):
            def method(*args, **kwargs):
                # In a real implementation, this would encode ABI and send to EVM
                print(f"Executing Solidity call: {{name}} with args: {{kwargs}}")
                return {{"status": "executed (mock)", "contract": "{c['name']}", "method": name, "args": kwargs}}
            return method
    
    contracts["{c['id']}"] = MockSolidityContract_{c['id']}()
"""
        
        # Generate Endpoints
        code += """

# We need a reference to the chain to add transactions.
# This will be injected by the server when it includes the router.
chain_instance = None

def set_chain(chain):
    global chain_instance
    chain_instance = chain
    if hasattr(chain.runtime, 'contracts'):
        chain.runtime.contracts = contracts

@router.post("/execute/{contract_id}/{method}")
def execute_contract(contract_id: str, method: str, args: dict = {}, x_api_key: Optional[str] = Header(None)):
    if contract_id not in contracts:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    contract = contracts[contract_id]
    
    if not hasattr(contract, method):
        raise HTTPException(status_code=404, detail="Method not found")
        
    if chain_instance is None:
        raise HTTPException(status_code=500, detail="Blockchain instance not linked to router")

    # Instead of executing directly, we create a transaction
    tx = {
        "type": "contract_call",
        "contract_id": contract_id,
        "method": method,
        "args": args,
        "sender": "user" # Setup a real sender in production
    }
    
    chain_instance.add_transaction(tx)
    return {"status": "queued", "transaction": tx}

# Initialize on import (or handle in startup event)
load_contracts()
"""
        return code

    def _generate_server(self, has_contracts: bool):
        code = """from fastapi import FastAPI
import uvicorn
from ..core.chain import Blockchain
"""
        if has_contracts:
            code += "from . import contract_routes\n"

        code += """
def run(chain: Blockchain, port: int):
    app = FastAPI()

    @app.get("/blocks")
    def get_blocks():
        return [b.to_dict() for b in chain.chain]

    @app.get("/state")
    def get_state():
        return chain.state

    @app.post("/transactions")
    def submit_transaction(tx: dict):
        # Logic to add tx to pool
        chain.add_transaction(tx)
        return {"status": "received"}
"""
        if has_contracts:
            code += """
    contract_routes.set_chain(chain)
    app.include_router(contract_routes.router, prefix="/api/v1/contracts", tags=["Smart Contracts"])
"""
        
        code += """
    uvicorn.run(app, host="0.0.0.0", port=port)
"""
        return code
