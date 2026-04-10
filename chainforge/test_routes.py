from fastapi import APIRouter, HTTPException, Header
from typing import Optional, Dict, Any
import importlib
import sys
import os

router = APIRouter()

# Helper to load contracts dynamically
contracts = {}
contract_api_keys = {
    "1000": "sys_key_datastore",
    "1001": "sys_key_validation",
    "1002": "sys_key_accesscontrol",
    "1003": "sys_key_identityregistry",
    "1004": "sys_key_auditlog",
    "1005": "sys_key_participation",
    "1006": "sys_key_authoritymanagement",
    "user_contract": "test_key",
}

def load_contracts():
    sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

    try:
        module = importlib.import_module("modules.smart_contracts.DataStore")
        class_name = "DataStore"
        if hasattr(module, class_name):
            contracts["1000"] = getattr(module, class_name)()
        else:
             for attr_name in dir(module):
                 attr = getattr(module, attr_name)
                 if isinstance(attr, type) and attr.__module__ == module.__name__:
                     contracts["1000"] = attr()
                     break
    except Exception as e:
        print(f"Failed to load contract DataStore: {e}")

    try:
        module = importlib.import_module("modules.smart_contracts.Validation")
        class_name = "Validation"
        if hasattr(module, class_name):
            contracts["1001"] = getattr(module, class_name)()
        else:
             for attr_name in dir(module):
                 attr = getattr(module, attr_name)
                 if isinstance(attr, type) and attr.__module__ == module.__name__:
                     contracts["1001"] = attr()
                     break
    except Exception as e:
        print(f"Failed to load contract Validation: {e}")

    try:
        module = importlib.import_module("modules.smart_contracts.AccessControl")
        class_name = "AccessControl"
        if hasattr(module, class_name):
            contracts["1002"] = getattr(module, class_name)()
        else:
             for attr_name in dir(module):
                 attr = getattr(module, attr_name)
                 if isinstance(attr, type) and attr.__module__ == module.__name__:
                     contracts["1002"] = attr()
                     break
    except Exception as e:
        print(f"Failed to load contract AccessControl: {e}")

    try:
        module = importlib.import_module("modules.smart_contracts.IdentityRegistry")
        class_name = "IdentityRegistry"
        if hasattr(module, class_name):
            contracts["1003"] = getattr(module, class_name)()
        else:
             for attr_name in dir(module):
                 attr = getattr(module, attr_name)
                 if isinstance(attr, type) and attr.__module__ == module.__name__:
                     contracts["1003"] = attr()
                     break
    except Exception as e:
        print(f"Failed to load contract IdentityRegistry: {e}")

    try:
        module = importlib.import_module("modules.smart_contracts.AuditLog")
        class_name = "AuditLog"
        if hasattr(module, class_name):
            contracts["1004"] = getattr(module, class_name)()
        else:
             for attr_name in dir(module):
                 attr = getattr(module, attr_name)
                 if isinstance(attr, type) and attr.__module__ == module.__name__:
                     contracts["1004"] = attr()
                     break
    except Exception as e:
        print(f"Failed to load contract AuditLog: {e}")

    try:
        module = importlib.import_module("modules.smart_contracts.Participation")
        class_name = "Participation"
        if hasattr(module, class_name):
            contracts["1005"] = getattr(module, class_name)()
        else:
             for attr_name in dir(module):
                 attr = getattr(module, attr_name)
                 if isinstance(attr, type) and attr.__module__ == module.__name__:
                     contracts["1005"] = attr()
                     break
    except Exception as e:
        print(f"Failed to load contract Participation: {e}")

    try:
        module = importlib.import_module("modules.smart_contracts.AuthorityManagement")
        class_name = "AuthorityManagement"
        if hasattr(module, class_name):
            contracts["1006"] = getattr(module, class_name)()
        else:
             for attr_name in dir(module):
                 attr = getattr(module, attr_name)
                 if isinstance(attr, type) and attr.__module__ == module.__name__:
                     contracts["1006"] = attr()
                     break
    except Exception as e:
        print(f"Failed to load contract AuthorityManagement: {e}")

    try:
        module = importlib.import_module("modules.smart_contracts.MyContract")
        class_name = "MyContract"
        if hasattr(module, class_name):
            contracts["user_contract"] = getattr(module, class_name)()
        else:
             for attr_name in dir(module):
                 attr = getattr(module, attr_name)
                 if isinstance(attr, type) and attr.__module__ == module.__name__:
                     contracts["user_contract"] = attr()
                     break
    except Exception as e:
        print(f"Failed to load contract MyContract: {e}")


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
