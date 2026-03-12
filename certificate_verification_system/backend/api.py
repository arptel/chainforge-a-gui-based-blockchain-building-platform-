import uuid
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from dependencies import require_issuer
from chainforge_sdk import Client as ChainForgeClient
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
        # Instantiate the auto-generated SDK client
        client = ChainForgeClient(current_user.get("node_url"))
        
        # The beautiful 1-line auto-SDK call!
        response = client.CertificateRegistry.issue_certificate(
            user_address=current_user["address"],
            private_key=current_user.get("private_key", ""),
            cert_id=cert_id,
            student_name=req.student_name,
            degree=req.degree,
            year=req.year,
            issuer_id=current_user["address"]
        )
        
        if response.get("error"):
            raise HTTPException(status_code=400, detail=response["error"])
            
        return {
            "status": "success",
            "message": "Certificate issued successfully on the blockchain",
            "cert_id": cert_id,
            "transaction": response.get("tx")
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
        client = ChainForgeClient(current_user.get("node_url"))
        
        response = client.CertificateRegistry.revoke_certificate(
            user_address=current_user["address"],
            private_key=current_user.get("private_key", ""),
            cert_id=req.cert_id,
            requester_id=current_user["address"]
        )
        
        if response.get("error"):
            raise HTTPException(status_code=400, detail=response["error"])
            
        return {
            "status": "success",
            "message": f"Certificate {req.cert_id} revoked successfully."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Blockchain Node Error: {str(e)}")




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
