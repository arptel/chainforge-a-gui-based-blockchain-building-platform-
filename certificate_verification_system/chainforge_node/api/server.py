from fastapi import FastAPI, HTTPException
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from core.chain import Blockchain
from api import contract_routes
from core.merkle import generate_merkle_proof, _hash_tx

network_instance = None

def set_network(network):
    global network_instance
    network_instance = network

def run(chain: Blockchain, port: int):
    app = FastAPI()

    # Enable CORS for direct browser SPV connections (React runs on 5174)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"], # In production, restrict to strictly authorized domains
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/blocks")
    def get_blocks():
        return [b.to_dict() for b in chain.chain]

    @app.get("/state")
    def get_state():
        return chain.state

    @app.post("/transactions")
    def submit_transaction(tx: dict):
        # Logic to add tx to pool
        chain.add_transaction(tx)
        return {"status": "received"}

    # --- SPV Light Node Endpoints ---

    @app.get("/headers")
    def get_headers():
        """Returns lightweight block headers for SPV clients instead of full block data."""
        return [
            {
                "index": b.index,
                "hash": b.hash,
                "previous_hash": b.previous_hash,
                "timestamp": b.timestamp,
                "merkle_root": b.merkle_root,
                "state_root": b.state_root,
                "validator": b.validator
            }
            for b in chain.chain
        ]

    @app.get("/proof/cert/{cert_id}")
    def get_cert_proof(cert_id: str):
        """
        Returns the transaction and Merkle proof for the most recent
        interaction with a specific certificate ID.
        """
        import json
        # Search backwards to find the latest tx modifying this cert_id
        for block in reversed(chain.chain):
            for i, tx in enumerate(block.transactions):
                if tx.get("type") == "contract_call":
                    raw_args = tx.get("args", {})
                    
                    # Safely parse args whether it's a dict or a JSON string (sent by certain network utilities)
                    args = {}
                    if isinstance(raw_args, dict):
                        args = raw_args
                    elif isinstance(raw_args, str):
                        try:
                            args = json.loads(raw_args)
                        except json.JSONDecodeError:
                            pass

                    # Standard check for CertificateRegistry
                    if args.get("cert_id") == cert_id:
                        proof = generate_merkle_proof(block.transactions, i)
                        return {
                            "cert_id": cert_id,
                            "tx": tx,
                            "tx_hash": _hash_tx(tx),
                            "block_index": block.index,
                            "proof": proof,
                            "merkle_root": block.merkle_root
                        }
        raise HTTPException(status_code=404, detail="Certificate transaction not found on the blockchain")

    contract_routes.set_chain(chain)
    app.include_router(contract_routes.router, prefix="/api/v1/contracts", tags=["Smart Contracts"])

    uvicorn.run(app, host="0.0.0.0", port=port)
