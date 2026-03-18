import uuid
import requests
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
    node_id = uuid.uuid4().hex
    cert_id = f"CERT-{node_id[:8].upper()}"
    
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
    try:
        client = ChainForgeClient(current_user.get("node_url"))
        
        # Pre-check: Read the blockchain state to verify the caller is the original issuer
        # This avoids waiting 15 seconds for a mining timeout when the smart contract would reject it anyway.
        try:
            state_resp = requests.get(f"{current_user.get('node_url')}/state")
            state_resp.raise_for_status()
            state = state_resp.json()
            
            cert_key = f"cert_{req.cert_id}"
            if cert_key not in state:
                raise HTTPException(status_code=404, detail="Certificate not found on the blockchain")
            
            cert = state[cert_key]
            if cert.get("is_revoked"):
                raise HTTPException(status_code=400, detail="Certificate is already revoked")
            
            if cert.get("issuer_id") != current_user["address"]:
                raise HTTPException(
                    status_code=403, 
                    detail="Unauthorized: Only the original issuing authority can revoke this certificate"
                )
        except HTTPException:
            raise
        except Exception as e:
            # If we can't pre-check, fall through and let the blockchain handle it
            pass
        
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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Blockchain Node Error: {str(e)}")




@api_router.get("/issuers")
async def get_issuers():
    """
    Public endpoint to get a mapping of blockchain addresses to issuer names.
    Now reads from the persistent SQLite database instead of the old MOCK_USERS dict.
    """
    import sqlite3
    from auth import DB_PATH
    
    issuer_map = {}
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT username, blockchain_address, node_url FROM users WHERE role = "ISSUER"')
        for row in cursor.fetchall():
            username, address, node_url = row
            if address:
                readable_name = username.replace("_", " ").title()
                issuer_map[address] = {
                    "name": readable_name,
                    "url": node_url
                }
        conn.close()
    except Exception as e:
        print(f"[API] Error loading issuers: {e}")
        
    return issuer_map


@api_router.get("/history")
async def get_certificate_history(current_user: dict = Depends(require_issuer)):
    """
    Returns all certificates issued by the authenticated college.
    """
    try:
        node_url = current_user.get("node_url")
        if not node_url:
            raise HTTPException(status_code=500, detail="Node URL not configured for user")
            
        resp = requests.get(f"{node_url}/state")
        resp.raise_for_status()
        state = resp.json()
        
        issued_certs = []
        for key, value in state.items():
            if key.startswith("cert_") and isinstance(value, dict):
                # Only include if this user is the issuer
                if value.get("issuer_id") == current_user["address"]:
                    # Correctly extract cert_id from key if not in value
                    raw_id = value.get("cert_id") or key.replace("cert_", "")
                    
                    # Flatten the data structure for frontend
                    issued_certs.append({
                        "certId": raw_id,
                        "studentName": value.get("student_name"),
                        "degree": value.get("degree"),
                        "year": value.get("year"),
                        "isRevoked": value.get("is_revoked", False),
                        "timestamp": "On-Chain"
                    })
        
        return issued_certs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch history: {str(e)}")
@api_router.get("/browse-folder")
async def browse_folder():
    """
    Opens a directory picker on the host machine and returns the selected path.
    Useful for local installations where the user needs to select a DB storage path.
    """
    try:
        import tkinter as tk
        from tkinter import filedialog
        
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        root.attributes('-topmost', True)  # Bring to front
        
        directory = filedialog.askdirectory(title="Select Database Storage Directory")
        root.destroy()
        
        if not directory:
            return {"path": ""}
            
        return {"path": directory.replace("\\", "/")}
    except Exception as e:
        print(f"[API] Error opening directory picker: {e}")
        raise HTTPException(status_code=500, detail="Could not open directory picker. Please enter path manually.")
