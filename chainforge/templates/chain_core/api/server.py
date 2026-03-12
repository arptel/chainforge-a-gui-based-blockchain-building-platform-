from fastapi import FastAPI, HTTPException, WebSocket
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

    # --- P2P WebSocket Endpoint ---
    @app.websocket("/ws")
    async def websocket_peer_endpoint(websocket: WebSocket):
        await websocket.accept()
        if network_instance:
            network_instance.add_incoming_connection(websocket)
            try:
                while True:
                    data = await websocket.receive_text()
                    response = network_instance._handle_incoming_message(data, sender_ws=websocket)
                    if response:
                        await websocket.send_text(response)
            except Exception:
                pass
            finally:
                network_instance.remove_incoming_connection(websocket)

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

    @app.get("/proof/tx/{tx_hash}")
    def get_tx_proof(tx_hash: str):
        """
        Returns the transaction and Merkle proof for any successfully mined transaction hash.
        """
        for block in reversed(chain.chain):
            for i, tx in enumerate(block.transactions):
                if _hash_tx(tx) == tx_hash:
                    proof = generate_merkle_proof(block.transactions, i)
                    return {
                        "tx": tx,
                        "tx_hash": tx_hash,
                        "block_index": block.index,
                        "proof": proof,
                        "merkle_root": block.merkle_root
                    }
        raise HTTPException(status_code=404, detail="Transaction hash not found on the blockchain")

    contract_routes.set_chain(chain)
    app.include_router(contract_routes.router, prefix="/api/v1/contracts", tags=["Smart Contracts"])

    uvicorn.run(app, host="0.0.0.0", port=port)
