import json
import hashlib
from ecdsa import SigningKey, VerifyingKey, SECP256k1
from typing import Tuple, Dict, Any

def generate_keypair() -> Tuple[str, str]:
    """
    Generates a new SECP256k1 keypair.
    Returns:
        (private_key_hex, public_key_hex)
    """
    sk = SigningKey.generate(curve=SECP256k1)
    vk = sk.get_verifying_key()
    
    # Return as hex strings
    return sk.to_string().hex(), vk.to_string().hex()

def _serialize_tx(tx_data: Dict[str, Any]) -> bytes:
    """
    Serializes standard transaction fields deterministically for signing and verification.
    """
    # Create a copy to remove signature field if it exists
    tx_copy = dict(tx_data)
    if 'signature' in tx_copy:
        del tx_copy['signature']
        
    # Serialize to deterministic JSON string
    tx_string = json.dumps(tx_copy, sort_keys=True)
    return tx_string.encode('utf-8')

def sign_transaction(tx_data: Dict[str, Any], private_key_hex: str) -> str:
    """
    Signs a transaction using the provided private key.
    """
    sk = SigningKey.from_string(bytes.fromhex(private_key_hex), curve=SECP256k1)
    
    message = _serialize_tx(tx_data)
    
    # Sign using deterministic ECDSA
    signature = sk.sign_deterministic(message, hashfunc=hashlib.sha256)
    
    return signature.hex()

def verify_signature(tx_data: Dict[str, Any], signature_hex: str, public_key_hex: str) -> bool:
    """
    Verifies that the transaction signature matches the data and public key.
    """
    try:
        vk = VerifyingKey.from_string(bytes.fromhex(public_key_hex), curve=SECP256k1)
        message = _serialize_tx(tx_data)
        signature = bytes.fromhex(signature_hex)
        
        return vk.verify(signature, message, hashfunc=hashlib.sha256)
    except Exception as e:
        # Catch BadSignatureError, MalformedPointError, invalid hex parsing, etc.
        print(f"Signature verification failed: {e}")
        return False
