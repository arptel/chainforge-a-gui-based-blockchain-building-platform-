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

    @staticmethod
    def get_default_contracts(config: dict) -> list:
        import sys
        import os
        
        core_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "templates", "chain_core"))
        if core_dir not in sys.path:
            sys.path.append(core_dir)
            
        from modules.smart_contracts.Contract_registry import SYSTEM_CONTRACTS
        
        def generate_dummy_code(name, methods, is_wasm=False):
            if is_wasm:
                methods_code = "\n".join([f"    void {m}() {{}}" for m in methods])
                return f'extern "C" {{\n{methods_code}\n}}'
                
            contract_file_path = os.path.join(core_dir, "modules", "smart_contracts", f"{name}.py")
            if os.path.exists(contract_file_path):
                with open(contract_file_path, "r", encoding="utf-8") as f:
                    return f.read()
                    
            methods_code = "\n".join([f"    def {m}(self, caller=None, state=None, **kwargs):\n        pass" for m in methods])
            if not methods_code:
                methods_code = "    pass"
            return f"class {name}:\n    def __init__(self):\n        pass\n\n{methods_code}\n"
            
        default_contracts = []
        contract_id_counter = 1000
        
        is_wasm = config.get("networkType") == "public" and config.get("publicRuntime") == "wasm"
        
        # ALWAYS INCLUDE BASE
        for c_name, c_data in SYSTEM_CONTRACTS.get("base", {}).items():
            default_contracts.append({
                "id": str(contract_id_counter),
                "name": c_name,
                "type": "c++" if is_wasm else "python",
                "code": generate_dummy_code(c_name, c_data.get("methods", []), is_wasm),
                "apiKey": f"sys_key_{c_name.lower()}",
                "isSystem": True
            })
            contract_id_counter += 1
            
        # Map config keys to registry
        registry_keys_to_check = [
            config.get("networkType"),
            config.get("publicConsensus"),
            config.get("centralizedConsensus"),
            config.get("consortiumConsensus"),
            config.get("publicSyncMode"),
            config.get("centralizedSync"),
            config.get("consortiumSync"),
            config.get("permissionedType"),
            config.get("publicToken")
        ]
        
        for key in registry_keys_to_check:
            if not key: continue
            if key == "native": key = "token"
            if key == "light": key = "light_sync"
            
            if key in SYSTEM_CONTRACTS:
                for c_name, c_data in SYSTEM_CONTRACTS[key].items():
                    default_contracts.append({
                        "id": str(contract_id_counter),
                        "name": c_name,
                        "type": "c++" if is_wasm else "python",
                        "code": generate_dummy_code(c_name, c_data.get("methods", []), is_wasm),
                        "apiKey": f"sys_key_{c_name.lower()}",
                        "isSystem": True
                    })
                    contract_id_counter += 1
                    
        return default_contracts

    def build_package(self) -> bytes:
        """
        Generates the blockchain source code and returns a ZIP file as bytes.
        """
        # Determine allowed files per module based on config
        allowed_consensus = set()
        allowed_sync = set()
        allowed_vm = set()
        
        network_type = self.config.get("networkType")
        if network_type == "public":
            allowed_consensus.add(self.config.get("publicConsensus"))
            allowed_sync.add(self.config.get("publicSyncMode"))
            allowed_vm.add(self.config.get("publicRuntime"))
        elif network_type == "permissioned":
            p_type = self.config.get("permissionedType")
            if p_type == "centralized":
                allowed_consensus.add(self.config.get("centralizedConsensus"))
                allowed_sync.add(self.config.get("centralizedSync"))
            elif p_type == "consortium":
                allowed_consensus.add(self.config.get("consortiumConsensus"))
                allowed_sync.add(self.config.get("consortiumSync"))
        
        # Format names to match module files, assuming they end in .py
        # Handle 'none' consensus safely, handle 'light' sync if it goes by another name, etc.
        allowed_consensus_files = {f"{c}.py" for c in allowed_consensus if c}
        allowed_consensus_files.add("__init__.py")
        
        allowed_sync_files = {f"{s}.py" for s in allowed_sync if s}
        allowed_sync_files.add("__init__.py")
        
        allowed_vm_files = {f"{v}.py" for v in allowed_vm if v}
        allowed_vm_files.add("__init__.py")
        # Ensure python_vm is always available as fallback/dependency
        allowed_vm_files.add("python_vm.py") 

        bio = io.BytesIO()
        with zipfile.ZipFile(bio, "w", zipfile.ZIP_DEFLATED) as zip_file:
             for root, dirs, files in os.walk(TEMPLATE_DIR):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, TEMPLATE_DIR)
                    arcname_forward = arcname.replace("\\", "/")
                    
                    # Skip files we want to overwrite explicitly
                    if arcname_forward == "api/server.py":
                        continue
                        
                    # Filtering Logic for modules/
                    if arcname_forward.startswith("modules/consensus/"):
                        if file not in allowed_consensus_files:
                            continue
                    elif arcname_forward.startswith("modules/sync/"):
                        if file not in allowed_sync_files:
                            continue
                    elif arcname_forward.startswith("modules/vm/"):
                        if file not in allowed_vm_files:
                            continue
                            
                    zip_file.write(file_path, arcname)
                    
             # Add a specific config file
             config_json = json.dumps(self.config, indent=4)
             zip_file.writestr("config/genesis.json", config_json)

             # Smart Contracts
             user_contracts = self.config.get('smartContracts', [])
             default_contracts = self.get_default_contracts(self.config)
             
             # Prevent duplicates if user_contracts already contains the defaults (added during project creation)
             user_contract_names = {c.get("name") for c in user_contracts}
             filtered_defaults = [c for c in default_contracts if c.get("name") not in user_contract_names]
             
             contracts = filtered_defaults + user_contracts
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
                     elif c['type'] == 'c++':
                         zip_file.writestr(f"smart_contracts/{safe_name}.cpp", c['code'])
                     else:
                         zip_file.writestr(f"smart_contracts/{safe_name}.sol", c['code'])
                 
                 # Generate Routes
                 routes_code = self._generate_routes(contracts)
                 zip_file.writestr("api/contract_routes.py", routes_code)
                 
                 # Generate SDK
                 zip_file.writestr("sdk/__init__.py", "")
                 api_base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
                 zip_file.writestr("sdk/config.py", f'API_BASE_URL = "{api_base_url}"\n')
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
        code = """from .base_client import ChainForgeBaseClient, SmartContract
from .config import API_BASE_URL

"""
        # Generate wrapper classes for each contract
        for c in contracts:
            if c['type'] == 'python':
                safe_name = "".join(x for x in c['name'] if x.isalnum() or x == "_")
                code += f"""
class {safe_name}Wrapper(SmartContract):
    def __init__(self, base_client):
        super().__init__("{c['id']}", base_client)

    def __getattr__(self, name):
        def method(user_address: str, private_key: str, **kwargs):
            return self.execute(user_address, private_key, name, **kwargs)
        return method
"""

        code += """
class Client(ChainForgeBaseClient):
    def __init__(self, base_url=None):
        super().__init__(base_url if base_url else API_BASE_URL)
"""
        for c in contracts:
            safe_name = "".join(x for x in c['name'] if x.isalnum() or x == "_")
            if c['type'] == 'python':
                code += f"        self.{safe_name} = {safe_name}Wrapper(self)\n"
            elif c['type'] == 'solidity':
                code += f"        self.{safe_name} = SmartContract('{c['id']}', self)\n"

        return code

    def _generate_js_sdk_client(self, contracts):
        code = """import { SPVLightClient } from './base_client.js';

class SmartContract {
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

export class ChainForgeClient extends SPVLightClient {
    const apiBaseUrl = os.getenv("API_BASE_URL", "http://localhost:8000");
    constructor(spvNodeUrls = ["http://localhost:8080"], restBaseUrl = apiBaseUrl) {
        super(spvNodeUrls);
        this.restBaseUrl = restBaseUrl;
"""
        for c in contracts:
            safe_name = "".join(x for x in c['name'] if x.isalnum() or x == "_")
            code += f'        this.{safe_name} = createContractProxy("{c["id"]}", "{c["apiKey"]}", this.restBaseUrl);\n'
        
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
contract_api_keys = {
"""
        for c in contracts:
            code += f'    "{c["id"]}": "{c.get("apiKey", "")}",\n'
            
        code += """}

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
        
    expected_key = contract_api_keys.get(contract_id)
    if expected_key and x_api_key != expected_key:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    
    contract = contracts[contract_id]
    
    if not hasattr(contract, method):
        raise HTTPException(status_code=404, detail="Method not found")
        
    if chain_instance is None:
        raise HTTPException(status_code=500, detail="Blockchain instance not linked to router")

    # Preserve backward compatibility by tolerating both sender and from
    # Use args.get so we don't fully remove it if it's somehow required by the contract
    sender = args.get("from", args.get("sender", "user"))

    # Instead of executing directly, we create a transaction
    tx = {
        "type": "contract_call",
        "contract_id": contract_id,
        "method": method,
        "args": args,
        "sender": sender,
        "from": sender
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
from core.chain import Blockchain
from api import contract_routes

network_instance = None

def set_network(network):
    global network_instance
    network_instance = network
"""
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
