class CertificateRegistry:
    def _get_key(self, cert_id: str) -> str:
        return f"cert_{cert_id}"

    def issue_certificate(self, caller: str, cert_id: str, student_name: str, degree: str, year: int, issuer_id: str, state: dict = None) -> dict:
        """
        Issues a new certificate. 
        Note: The FastAPI backend MUST verify that 'issuer_id' has the 'ISSUER' role 
        via the AccessControl contract before calling this method.
        """
        if state is None: return {"error": "Blockchain state not provided"}
        key = self._get_key(cert_id)
        if key in state:
            return {"error": "Certificate ID already exists"}
            
        state[key] = {
            "student_name": student_name,
            "degree": degree,
            "year": year,
            "issuer_id": issuer_id,
            "is_revoked": False
        }
        
        return {"status": "success", "cert_id": cert_id}

    def revoke_certificate(self, caller: str, cert_id: str, requester_id: str, state: dict = None) -> dict:
        """
        Revokes a certificate. 
        The requester_id must be the original issuer or an authorized party.
        """
        if state is None: return {"error": "Blockchain state not provided"}
        key = self._get_key(cert_id)
        if key not in state:
            return {"error": "Certificate not found"}
            
        cert = state[key]
        
        # Only the original issuer can revoke it
        if cert["issuer_id"] != requester_id:
            return {"error": "Unauthorized: Only the original issuer can revoke this certificate"}
            
        if cert["is_revoked"]:
            return {"error": "Certificate is already revoked"}
            
        cert["is_revoked"] = True
        state[key] = cert # Explicitly update the dictionary reference if needed
        return {"status": "success", "message": "Certificate revoked"}

    def verify_certificate(self, caller: str, cert_id: str, state: dict = None) -> dict:
        """Verifies if a certificate is valid and not revoked."""
        if state is None: return {"error": "Blockchain state not provided"}
        key = self._get_key(cert_id)
        if key not in state:
            return {"status": "not_found", "is_valid": False}
            
        cert = state[key]
        if cert["is_revoked"]:
            return {"status": "revoked", "is_valid": False}
            
        return {"status": "valid", "is_valid": True}

    def get_certificate(self, caller: str, cert_id: str, state: dict = None) -> dict:
        """Returns the full details of a certificate."""
        if state is None: return {"error": "Blockchain state not provided"}
        key = self._get_key(cert_id)
        if key not in state:
            return {"error": "Certificate not found"}
            
        return {"status": "success", "data": state[key]}
