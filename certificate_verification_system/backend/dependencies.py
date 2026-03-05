from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from auth import SECRET_KEY, ALGORITHM

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verifies the JWT and returns the user payload including their blockchain address."""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_address: str = payload.get("address")
        role: str = payload.get("role")
        private_key: str = payload.get("private_key")
        
        if username is None or role != "ISSUER":
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        
        return {"username": username, "address": user_address, "role": role, "private_key": private_key}

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

def require_issuer(current_user: dict = Depends(get_current_user)):
    """Ensures the authenticated user is an ISSUER."""
    if current_user.get("role") != "ISSUER":
        raise HTTPException(status_code=403, detail="Not authorized to perform this action")
    return current_user
