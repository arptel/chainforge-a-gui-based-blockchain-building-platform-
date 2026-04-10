import sys
import os

try:
    from core.merkle import verify_merkle_proof
except ImportError:
    # Handle dynamic loading paths
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
    from core.merkle import verify_merkle_proof

class ProofVerifier:
    def __init__(self):
        pass

    def verifyProof(self, caller=None, state=None, leaf=None, proof=None, root=None, **kwargs):
        if not leaf or not proof or not root:
            return {"error": "Missing verification parameters"}
            
        try:
            val = verify_merkle_proof(leaf, proof, root)
            if not val:
                 print(f"[ProofVerifier] Verification failed for {leaf}")
            return val
        except Exception as e:
            print(f"[ProofVerifier] Verification Exception: {e}")
            return False

    def getMerkleProof(self, caller=None, state=None, key=None, **kwargs):
        # We don't implement full chain querying from within the contract sandbox 
        # Usually SPVs call the API endpoint for proofs.
        return {"error": "Use the /proof API endpoint to retrieve Merkle proofs"}

