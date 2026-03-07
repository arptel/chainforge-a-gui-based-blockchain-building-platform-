import os
import time
import requests
import json
import hashlib
from typing import Any, Dict, Optional
try:
    from ecdsa import SigningKey, SECP256k1
except ImportError:
    pass

CHAINFORGE_API_URL = os.getenv("CHAINFORGE_API_URL", "http://localhost:8080")

class ChainForgeClient:
    """
    Client for interacting directly with the immutable ChainForge ledger.
    """
    
    def __init__(self, base_url: str = CHAINFORGE_API_URL):
        self.base_url = base_url

    def _serialize_tx(self, tx_data: Dict[str, Any]) -> bytes:
        tx_copy = dict(tx_data)
        if 'signature' in tx_copy:
            del tx_copy['signature']
        tx_string = json.dumps(tx_copy, sort_keys=True)
        return tx_string.encode('utf-8')

    def execute_contract(self, user_address: str, private_key: str, contract_name: str, method_name: str, params: Dict[str, Any], node_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Constructs a transaction, generates a deterministic cryptographic signature using
        the ECDSA private key, and submits it directly into the Blockchain's Mempool.
        """
        target_url = node_url if node_url else self.base_url
        contract_id = {"AccessControl": "1002", "CertificateRegistry": "7vjd6ku"}.get(contract_name)
        if not contract_id:
            return {"error": f"Unknown contract {contract_name}"}
            
        if not private_key:
            return {"error": "Private key required to cryptographically sign transaction onto the blockchain"}
            
        # Bind the caller natively exactly as the Smart Contract expects
        tx = {
            "type": "contract_call",
            "contract_id": contract_id,
            "method": method_name,
            "args": params,
            "from": user_address,
            "gas_price": 0,
            "gas_limit": 100000,
            "nonce": None
        }
        
        # Sign the transaction payload
        try:
            sk = SigningKey.from_string(bytes.fromhex(private_key), curve=SECP256k1)
            message = self._serialize_tx(tx)
            signature = sk.sign_deterministic(message, hashfunc=hashlib.sha256)
            tx["signature"] = signature.hex()
        except Exception as e:
            return {"error": f"Failed to sign transaction: {e}"}
            
        try:
            # Post directly to the native /transactions mempool route on the node
            response = requests.post(f"{target_url}/transactions", json=tx)
            response.raise_for_status()
            
            # ChainForge Python nodes configured with --role full mind pending transactions periodically.
            # We wait up to 15 seconds for the next block to be mined containing our tx!
            for _ in range(15):
                time.sleep(1)
                try:
                    blocks_resp = requests.get(f"{target_url}/blocks")
                    blocks_resp.raise_for_status()
                    for block in blocks_resp.json():
                        for mined_tx in block.get("transactions", []):
                            if mined_tx.get("signature") == tx["signature"]:
                                return {"status": "success", "message": "Transaction verified on-chain", "tx": response.json()}
                except Exception:
                    pass
            
            return {"error": "Transaction queued but not mined within 15 seconds. Please check back later."}
        except requests.RequestException as e:
            print(f"Error communicating with ChainForge Node: {e}")
            return {"error": str(e), "status": "failed"}

    def query_contract(self, contract_name: str, method_name: str, params: Dict[str, Any], node_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Queries the blockchain state by iterating over the blocks directly and computing 
        the CertificateRegistry immutable state dynamically. 
        This completely removes the mock database!
        """
        target_url = node_url if node_url else self.base_url

        cert_id = params.get("cert_id")
        
        # Pull the entire chain ledger to trace the true history of the certificate
        try:
            response = requests.get(f"{target_url}/blocks")
            response.raise_for_status()
            blocks = response.json()
        except Exception as e:
            return {"error": f"Failed to fetch blockchain ledger: {e}"}

        # Dynamically build state replica from the immutable ledger
        found_cert = None
        is_revoked = False
        
        for block in blocks:
            for tx in block.get("transactions", []):
                if tx.get("type") == "contract_call" and tx.get("contract_id") == "7vjd6ku":
                    args = tx.get("args", {})
                    # If this block contains an issue instruction for this cert_id
                    if tx.get("method") == "issue_certificate" and args.get("cert_id") == cert_id:
                        found_cert = args
                    # If a later block contains a revoke instruction, process the state drift
                    elif tx.get("method") == "revoke_certificate" and args.get("cert_id") == cert_id:
                        # Only apply revocation if the transaction was signed by the original issuer
                        if tx.get("from") == found_cert.get("issuer_id"):
                            is_revoked = True
                        else:
                            print(f"Ignored unauthorized revocation attempt for {cert_id} from {tx.get('from')}")

        if method_name == "verify_certificate":
            if not found_cert:
                return {"is_valid": False, "status": "not_found", "message": "This certificate does not exist on the blockchain."}
            if is_revoked:
                return {"is_valid": False, "status": "revoked", "message": "This certificate was revoked by the issuer."}
            return {"is_valid": True, "status": "valid", "message": "Certificate is cryptographically valid."}
            
        elif method_name == "get_certificate":
            if not found_cert:
                return {"error": "not found"}
            return {"status": "success", "data": found_cert}
            
        return {"error": "Unknown query endpoint"}

# Instantiate a singleton client that executes natively
chainforge_client = ChainForgeClient()
