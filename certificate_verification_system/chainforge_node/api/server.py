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

    # --- Visualizer WebSocket Endpoint ---
    visualizer_clients = set()

    @app.websocket("/visualize")
    async def websocket_visualizer(websocket: WebSocket):
        await websocket.accept()
        visualizer_clients.add(websocket)
        
        # 1. Send initial state
        initial_event = {
            "type": "NODE_JOINED",
            "timestamp": time.time(),
            "payload": {
                "nodeId": chain.node_id,
                "role": chain.role,
                "address": "Local Node",
                "balance": 100.0 # Default starting
            }
        }
        await websocket.send_json(initial_event)
        
        try:
            while True:
                # Keep connection alive
                await websocket.receive_text()
        except Exception:
            pass
        finally:
            visualizer_clients.remove(websocket)

    def broadcast_block(event_data):
        import asyncio
        import json
        
        message = {
            "type": "BLOCK_COMMITTED",
            "timestamp": time.time(),
            "payload": event_data
        }
        
        # Run async broadcast from sync callback
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                for client in list(visualizer_clients):
                    loop.create_task(client.send_json(message))
        except Exception:
            pass

    # Register the callback with the chain
    chain.on_block_committed.append(broadcast_block)

    # --- P2P WebSocket Endpoint ---
    @app.websocket("/ws")
    async def websocket_peer_endpoint(websocket: WebSocket):
        await websocket.accept()
        if network_instance:
            network_instance.add_incoming_connection(websocket)
            try:
                while True:
                    data = await websocket.receive_text()
                    response = await network_instance._handle_incoming_message(data, websocket)
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

    @app.get("/proof/cert/{cert_id}")
    def get_cert_proof(cert_id: str):
        """
        Custom SPV endpoint: Find the most recent transaction involving a certificate and return its Merkle proof.
        """
        for b in reversed(chain.chain):
            for i, tx in enumerate(b.transactions):
                args = tx.get("args", {})
                if isinstance(args, dict) and args.get("cert_id") == cert_id:
                    try:
                        proof = generate_merkle_proof(b.transactions, i)
                        return {
                            "block_index": b.index,
                            "merkle_root": b.merkle_root,
                            "tx": tx,
                            "proof": proof
                        }
                    except Exception as e:
                        continue
        raise HTTPException(status_code=404, detail="Certificate transaction not found")

    contract_routes.set_chain(chain)
    app.include_router(contract_routes.router, prefix="/api/v1/contracts", tags=["Smart Contracts"])

    uvicorn.run(app, host="0.0.0.0", port=port)
