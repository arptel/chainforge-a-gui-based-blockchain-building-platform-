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

class RegisterRequest(BaseModel):
    username: str
    password: str
    db_path: str = ""

class Token(BaseModel):
    access_token: str
    token_type: str

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "users.sqlite")

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            blockchain_address TEXT,
            private_key TEXT,
            role TEXT,
            node_url TEXT,
            db_path TEXT DEFAULT ""
        )
    ''')
    
    # Migration: Add db_path column if it doesn't exist
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN db_path TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass  # already exists
    
    # Check if empty
    cursor.execute('SELECT COUNT(*) FROM users')
    if cursor.fetchone()[0] == 0:
        # Seed default users
        users_to_seed = [
            ("college_a", "password123", "ISSUER", "http://127.0.0.1:8080"),
            ("college_b", "password123", "ISSUER", "http://127.0.0.1:8081")
        ]
        
        try:
            from ecdsa import SigningKey, SECP256k1
            def generate_keypair():
                sk = SigningKey.generate(curve=SECP256k1)
                return sk.to_string().hex(), sk.get_verifying_key().to_string().hex()
        except ImportError:
            def generate_keypair():
                return "", ""
                
        for u, p, r, n in users_to_seed:
            priv, pub = generate_keypair()
            cursor.execute('''
                INSERT INTO users (username, password, blockchain_address, private_key, role, node_url)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (u, p, pub if pub else f"{u}_address", priv, r, n))
            
    conn.commit()
    conn.close()

# Initialize database on module load
init_db()

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
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT password, blockchain_address, private_key, role, node_url, db_path FROM users WHERE username = ?', (req.username,))
    row = cursor.fetchone()
    conn.close()
    
    if not row or row[0] != req.password:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    # Generate JWT containing their blockchain address identity
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": req.username, 
            "address": row[1], 
            "role": row[3], 
            "private_key": row[2],
            "node_url": row[4]
        }, 
        expires_delta=access_token_expires
    )
    
    # Ensure their node is running!
    from node_manager import ensure_node_running
    ensure_node_running(req.username, row[4], row[5])
    
    return {"access_token": access_token, "token_type": "bearer"}

@auth_router.post("/register", response_model=Token)
async def register(req: RegisterRequest):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT username FROM users WHERE username = ?', (req.username,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Username already registered")
        
    try:
        from ecdsa import SigningKey, SECP256k1
        sk = SigningKey.generate(curve=SECP256k1)
        private_key = sk.to_string().hex()
        blockchain_address = sk.get_verifying_key().to_string().hex()
    except ImportError:
        private_key = ""
        blockchain_address = f"{req.username}_address"
        
    # Dynamically spawn a new node!
    from node_manager import spawn_node
    try:
        node_url = spawn_node(req.username, req.db_path)
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"Failed to spawn node: {str(e)}")
        
    role = "ISSUER"
    
    cursor.execute('''
        INSERT INTO users (username, password, blockchain_address, private_key, role, node_url, db_path)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (req.username, req.password, blockchain_address, private_key, role, node_url, req.db_path))
    
    conn.commit()
    conn.close()
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": req.username, 
            "address": blockchain_address, 
            "role": role, 
            "private_key": private_key,
            "node_url": node_url
        }, 
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}
