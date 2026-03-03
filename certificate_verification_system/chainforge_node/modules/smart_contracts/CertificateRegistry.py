class  CertificateRegistry:
    def __init__(self):
        # Maps cert_id -> { 'student_name': str, 'degree': str, 'year': int, 'issuer_id': str, 'is_revoked': bool }
        self.certificates = {}

    def issue_certificate(self, caller: str, cert_id: str, student_name: str, degree: str, year: int, issuer_id: str) -> dict:
        """
        Issues a new certificate. 
        Note: The FastAPI backend MUST verify that 'issuer_id' has the 'ISSUER' role 
        via the AccessControl contract before calling this method.
        """
        if cert_id in self.certificates:
            return {"error": "Certificate ID already exists"}
            
        self.certificates[cert_id] = {
            "student_name": student_name,
            "degree": degree,
            "year": year,
            "issuer_id": issuer_id,
            "is_revoked": False
        }
        
        return {"status": "success", "cert_id": cert_id}

    def revoke_certificate(self, caller: str, cert_id: str, requester_id: str) -> dict:
        """
        Revokes a certificate. 
        The requester_id must be the original issuer or an authorized party.
        """
        if cert_id not in self.certificates:
            return {"error": "Certificate not found"}
            
        cert = self.certificates[cert_id]
        
        # Only the original issuer can revoke it
        if cert["issuer_id"] != requester_id:
            return {"error": "Unauthorized: Only the original issuer can revoke this certificate"}
            
        if cert["is_revoked"]:
            return {"error": "Certificate is already revoked"}
            
        cert["is_revoked"] = True
        return {"status": "success", "message": "Certificate revoked"}

    def verify_certificate(self, caller: str, cert_id: str) -> dict:
        """Verifies if a certificate is valid and not revoked."""
        if cert_id not in self.certificates:
            return {"status": "not_found", "is_valid": False}
            
        cert = self.certificates[cert_id]
        if cert["is_revoked"]:
            return {"status": "revoked", "is_valid": False}
            
        return {"status": "valid", "is_valid": True}

    def get_certificate(self, caller: str, cert_id: str) -> dict:
        """Returns the full details of a certificate."""
        if cert_id not in self.certificates:
            return {"error": "Certificate not found"}
            
        return {"status": "success", "data": self.certificates[cert_id]}
