import sys
import os

try:
    from core.crypto import verify_signature
except ImportError:
    # Handle dynamic loading paths
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
    from core.crypto import verify_signature

class Validation:
    def __init__(self):
        pass

    def validate(self, caller=None, state=None, payload=None, **kwargs):
        if not isinstance(payload, dict):
            return False
        return True

    def validateSignature(self, caller=None, state=None, payload=None, signature=None, pub_key=None, **kwargs):
        if not payload or not signature or not pub_key:
            return {"error": "Missing signature parameters"}
        
        is_valid = verify_signature(payload, signature, pub_key)
        if not is_valid:
            print(f"[Validation Contract] Invalid signature for payload: {payload}")
        return is_valid
