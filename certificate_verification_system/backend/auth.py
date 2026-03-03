from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt

# Secret key to sign JWTs (In production, load this from environment variables)
SECRET_KEY = "dummy_secret_key_for_demo_purposes_only_do_not_use_in_prod"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

auth_router = APIRouter(prefix="/auth", tags=["auth"])

class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# Dummy database of colleges (In reality this is a DB or ChainForge AccessControl check)
# We assume 'college_a' exists and its matching blockchain address is '0xCollegeA_Auth'
MOCK_USERS = {
    "college_a": {
        "password": "password123",
        "blockchain_address": "college_a_address", # The identity that has the ISSUER role on chain
        "role": "ISSUER"
    },
    "college_b": {
        "password": "password123",
        "blockchain_address": "college_b_address",
        "role": "ISSUER"
    }
}

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@auth_router.post("/login", response_model=Token)
async def login(req: LoginRequest):
    user = MOCK_USERS.get(req.username)
    if not user or user["password"] != req.password:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    # Generate JWT containing their blockchain address identity
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": req.username, "address": user["blockchain_address"], "role": user["role"]}, 
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}
