import time
import requests
import json
import hashlib
from typing import Any, Dict, Optional
try:
    from ecdsa import SigningKey, SECP256k1
except ImportError:
    pass

class ChainForgeBaseClient:
    """
    Universal Base Client for all auto-generated ChainForge Networks.
    Handles cryptographic signing, transaction polling, and state querying automatically.
    """
    def __init__(self, base_url: str):
        self.base_url = base_url

    def _serialize_tx(self, tx_data: Dict[str, Any]) -> bytes:
        tx_copy = dict(tx_data)
        if 'signature' in tx_copy:
            del tx_copy['signature']
        tx_string = json.dumps(tx_copy, sort_keys=True)
        return tx_string.encode('utf-8')

    def execute_contract(self, user_address: str, private_key: str, contract_id: str, method_name: str, **kwargs) -> Dict[str, Any]:
        if not private_key:
            return {"error": "Private key required to cryptographically sign transaction onto the blockchain"}
            
        tx = {
            "type": "contract_call",
            "contract_id": contract_id,
            "method": method_name,
            "args": kwargs,
            "from": user_address,
            "gas_price": 0,
            "gas_limit": 100000,
            "nonce": None
        }
        
        try:
            sk = SigningKey.from_string(bytes.fromhex(private_key), curve=SECP256k1)
            message = self._serialize_tx(tx)
            signature = sk.sign_deterministic(message, hashfunc=hashlib.sha256)
            tx["signature"] = signature.hex()
        except Exception as e:
            return {"error": f"Failed to sign transaction: {e}"}
            
        try:
            response = requests.post(f"{self.base_url}/transactions", json=tx)
            response.raise_for_status()
            
            # Wait up to 15 seconds for the next block to be mined containing our tx
            for _ in range(15):
                time.sleep(1)
                try:
                    blocks_resp = requests.get(f"{self.base_url}/blocks")
                    blocks_resp.raise_for_status()
                    for block in blocks_resp.json():
                        for mined_tx in block.get("transactions", []):
                            if mined_tx.get("signature") == tx["signature"]:
                                return {"status": "success", "message": "Transaction verified on-chain", "tx": response.json()}
                except Exception:
                    pass
            
            return {"error": "Transaction queued but not mined within 15 seconds. Please check back later."}
        except requests.RequestException as e:
            return {"error": str(e), "status": "failed"}

class SmartContract:
    def __init__(self, contract_id: str, base_client: ChainForgeBaseClient):
        self.contract_id = contract_id
        self.client = base_client
        
    def execute(self, user_address: str, private_key: str, method_name: str, **kwargs):
        return self.client.execute_contract(user_address, private_key, self.contract_id, method_name, **kwargs)
