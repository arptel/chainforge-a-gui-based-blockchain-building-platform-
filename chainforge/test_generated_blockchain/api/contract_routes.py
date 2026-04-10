from fastapi import APIRouter, HTTPException, Header
from typing import Optional, Dict, Any
import importlib
import sys
import os

router = APIRouter()

# Helper to load contracts dynamically
contracts = {}

contract_api_keys = {
    "c1": "", # Example user contract, might not have api key mocked here
    "sys_datastore": "sys_key_datastore",
    "sys_governance": "sys_key_governance"
}

def load_contracts():
    sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

    try:
        module = importlib.import_module("modules.smart_contracts.Token")
        class_name = "Token"
        if hasattr(module, class_name):
            contracts["c1"] = getattr(module, class_name)()
        else:
             for attr_name in dir(module):
                 attr = getattr(module, attr_name)
                 if isinstance(attr, type) and attr.__module__ == module.__name__:
                     contracts["c1"] = attr()
                     break
    except Exception as e:
        print(f"Failed to load contract Token: {e}")

    # Mock/Generic handler for Solidity contract DataStore
    class MockSolidityContract_sys_datastore:
        def __getattr__(self, name):
            def method(*args, **kwargs):
                # In a real implementation, this would encode ABI and send to EVM
                print(f"Executing Solidity call: {name} with args: {kwargs}")
                return {"status": "executed (mock)", "contract": "DataStore", "method": name, "args": kwargs}
            return method
    
    contracts["sys_datastore"] = MockSolidityContract_sys_datastore()

    # Mock/Generic handler for Solidity contract Governance
    class MockSolidityContract_sys_governance:
        def __getattr__(self, name):
            def method(*args, **kwargs):
                # In a real implementation, this would encode ABI and send to EVM
                print(f"Executing Solidity call: {name} with args: {kwargs}")
                return {"status": "executed (mock)", "contract": "Governance", "method": name, "args": kwargs}
            return method
    
    contracts["sys_governance"] = MockSolidityContract_sys_governance()


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
