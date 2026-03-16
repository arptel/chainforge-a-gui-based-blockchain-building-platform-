import sys
import os
# Ensure the root of the project is in sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import auth, projects, generate
import models, database

models.Base.metadata.create_all(bind=models.engine)

app = FastAPI(
    title="ChainForge Platform API",
    description="Backend for ChainForge: Blockchain Creation Platform",
    version="0.1.0",
)

# CORS Setup
origins = [
    "http://localhost:3000",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(generate.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to ChainForge Platform API"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
