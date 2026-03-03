from fastapi import APIRouter, HTTPException, Header
from typing import Optional, Dict, Any
import importlib
import sys
import os

router = APIRouter()

# Helper to load contracts dynamically
contracts = {}

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
        module = importlib.import_module("modules.smart_contracts.ValidatorCouncil")
        class_name = "ValidatorCouncil"
        if hasattr(module, class_name):
            contracts["1005"] = getattr(module, class_name)()
        else:
             for attr_name in dir(module):
                 attr = getattr(module, attr_name)
                 if isinstance(attr, type) and attr.__module__ == module.__name__:
                     contracts["1005"] = attr()
                     break
    except Exception as e:
        print(f"Failed to load contract ValidatorCouncil: {e}")

    try:
        module = importlib.import_module("modules.smart_contracts.MultiSig")
        class_name = "MultiSig"
        if hasattr(module, class_name):
            contracts["1006"] = getattr(module, class_name)()
        else:
             for attr_name in dir(module):
                 attr = getattr(module, attr_name)
                 if isinstance(attr, type) and attr.__module__ == module.__name__:
                     contracts["1006"] = attr()
                     break
    except Exception as e:
        print(f"Failed to load contract MultiSig: {e}")

    try:
        module = importlib.import_module("modules.smart_contracts.CertificateAuthority")
        class_name = "CertificateAuthority"
        if hasattr(module, class_name):
            contracts["1007"] = getattr(module, class_name)()
        else:
             for attr_name in dir(module):
                 attr = getattr(module, attr_name)
                 if isinstance(attr, type) and attr.__module__ == module.__name__:
                     contracts["1007"] = attr()
                     break
    except Exception as e:
        print(f"Failed to load contract CertificateAuthority: {e}")

    try:
        module = importlib.import_module("modules.smart_contracts.AccessControl")
        class_name = "AccessControl"
        if hasattr(module, class_name):
            contracts["h4hscfu"] = getattr(module, class_name)()
        else:
             for attr_name in dir(module):
                 attr = getattr(module, attr_name)
                 if isinstance(attr, type) and attr.__module__ == module.__name__:
                     contracts["h4hscfu"] = attr()
                     break
    except Exception as e:
        print(f"Failed to load contract AccessControl: {e}")

    try:
        module = importlib.import_module("modules.smart_contracts.CertificateRegistry")
        class_name = "CertificateRegistry"
        if hasattr(module, class_name):
            contracts["7vjd6ku"] = getattr(module, class_name)()
        else:
             for attr_name in dir(module):
                 attr = getattr(module, attr_name)
                 if isinstance(attr, type) and attr.__module__ == module.__name__:
                     contracts["7vjd6ku"] = attr()
                     break
    except Exception as e:
        print(f"Failed to load contract CertificateRegistry: {e}")


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
