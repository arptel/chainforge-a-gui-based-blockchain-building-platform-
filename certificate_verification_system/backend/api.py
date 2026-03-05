import uuid
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from dependencies import require_issuer
from chainforge_client import chainforge_client
import time

api_router = APIRouter(prefix="/api", tags=["certificate"])

class IssueRequest(BaseModel):
    student_name: str
    degree: str
    year: int

class RevokeRequest(BaseModel):
    cert_id: str

@api_router.post("/issue")
async def issue_certificate(req: IssueRequest, current_user: dict = Depends(require_issuer)):
    """
    Issues a new certificate on the blockchain.
    Only users with the ISSUER role (verified via JWT) can call this.
    """
    # Generate a unique deterministic ID or just a UUID for the certificate
    cert_id = f"CERT-{uuid.uuid4().hex[:8].upper()}"
    
    # 1. We assume the ChainForge network is running and we call its REST API.
    # We pass the college's blockchain_address as the caller.
    
    # Optional: If using AccessControl contract on chain, we could technically verify here again,
    # but the smart contract itself checks `issuer_id`.
    
    payload = {
        "caller": current_user["address"],
        "cert_id": cert_id,
        "student_name": req.student_name,
        "degree": req.degree,
        "year": req.year,
        "issuer_id": current_user["address"]
    }
    
    try:
        # Send transaction to the running ChainForge node
        response = chainforge_client.execute_contract(
            user_address=current_user["address"],
            private_key=current_user.get("private_key", ""),
            contract_name="CertificateRegistry",
            method_name="issue_certificate",
            params=payload
        )
        
        if response.get("error"):
            raise HTTPException(status_code=400, detail=response["error"])
            
        # Simulate mining/consensus delay for realism in the demo
        time.sleep(1)
            
        return {
            "status": "success",
            "message": "Certificate issued successfully on the blockchain",
            "cert_id": cert_id,
            "transaction_hash": f"0x{uuid.uuid4().hex}", # Mock tx hash
            "block_number": 1042 # Mock block
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Blockchain Node Error: {str(e)}")


@api_router.post("/revoke")
async def revoke_certificate(req: RevokeRequest, current_user: dict = Depends(require_issuer)):
    """
    Revokes a certificate. Only the original issuer can do this.
    """
    payload = {
        "caller": current_user["address"],
        "cert_id": req.cert_id,
        "requester_id": current_user["address"]
    }
    
    try:
        response = chainforge_client.execute_contract(
            user_address=current_user["address"],
            private_key=current_user.get("private_key", ""),
            contract_name="CertificateRegistry",
            method_name="revoke_certificate",
            params=payload
        )
        
        if response.get("error"):
            raise HTTPException(status_code=400, detail=response["error"])
            
        time.sleep(1)
            
        return {
            "status": "success",
            "message": f"Certificate {req.cert_id} revoked successfully."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Blockchain Node Error: {str(e)}")


@api_router.get("/verify/{cert_id}")
async def verify_certificate(cert_id: str):
    """
    Public endpoint to verify a certificate's status.
    """
    try:
        # Read-only query to the blockchain
        response = chainforge_client.query_contract(
            contract_name="CertificateRegistry",
            method_name="verify_certificate",
            params={"caller": "public", "cert_id": cert_id}
        )
        
        if response.get("error"):
            # Handle standard error cases
            pass
            
        if response.get("status") == "not_found":
            return {"is_valid": False, "status": "Not Found", "message": "This certificate does not exist on the blockchain."}
        
        if response.get("status") == "revoked":
            return {"is_valid": False, "status": "Revoked", "message": "This certificate was revoked by the issuer."}
            
        return {"is_valid": True, "status": "Valid", "message": "Certificate is valid."}
        
    except Exception as e:
        # If the ChainForge node isn't running yet, we return a mock response for the sake of frontend dev
        return {"is_valid": False, "status": "Error", "message": "Blockchain Node unreachable"}


@api_router.get("/certificate/{cert_id}")
async def get_certificate(cert_id: str):
    """
    Public endpoint to read a certificate's data.
    """
    try:
        response = chainforge_client.query_contract(
            contract_name="CertificateRegistry",
            method_name="get_certificate",
            params={"caller": "public", "cert_id": cert_id}
        )
        
        if response.get("error"):
            raise HTTPException(status_code=404, detail="Certificate not found")
            
        return {
            "status": "success",
            "data": response.get("data", {})
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Blockchain Node unreachable")


@api_router.get("/issuers")
async def get_issuers():
    """
    Public endpoint to get a mapping of blockchain addresses to issuer names.
    """
    from auth import MOCK_USERS
    
    # Map their blockchain address (public key) to a readable name
    issuer_map = {}
    for username, user_data in MOCK_USERS.items():
        if "blockchain_address" in user_data and user_data["blockchain_address"]:
            # Convert 'college_a' to 'College A'
            readable_name = username.replace("_", " ").title()
            issuer_map[user_data["blockchain_address"]] = readable_name
            
    return issuer_map
