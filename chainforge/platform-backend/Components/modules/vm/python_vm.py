try:
    from ...interfaces.vm import VMInterface
except ImportError:
    from interfaces.vm import VMInterface
from typing import Any, Dict
import sys

class PythonVM(VMInterface):
    """
    Python Virtual Machine runtime for executing smart contracts natively.
    """
    def __init__(self, contracts_registry=None):
        print("Initializing Python VM Runtime...")
        self.contracts = contracts_registry or {}

    def execute_transaction(self, tx: Dict[str, Any], state: Any) -> Any:
        tx_type = tx.get("type")
        
        if tx_type != "contract_call":
            # Normal transfer or other transaction
            return {"status": "ignored", "reason": "not a contract call"}
            
        contract_id = tx.get("contract_id")
        method = tx.get("method")
        args = tx.get("args", {})
        
        if contract_id not in self.contracts:
            raise Exception(f"Contract {contract_id} not found")
            
        contract = self.contracts[contract_id]
        
        if not hasattr(contract, method):
            raise Exception(f"Method {method} not found in contract {contract_id}")
            
        func = getattr(contract, method)
        
        try:
            # We inject the state into the contract instance before calling
            contract.ctx = type('Context', (), {'state': state})()
            # Also inject the caller securely
            args["caller"] = tx.get("from")
            result = func(**args)
            return {"status": "success", "result": result}
        except Exception as e:
            print(f"Contract execution failed: {e}")
            raise e

    def deploy_contract(self, code: bytes, sender: str) -> str:
        # Static deployment done by generator for now
        print(f"PythonVM: Deploying contract from {sender} (Mock)")
        return "0x" + "0" * 40
