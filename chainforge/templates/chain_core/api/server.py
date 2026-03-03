from fastapi import FastAPI, BackgroundTasks, WebSocket, WebSocketDisconnect
import uvicorn
from typing import Dict, Any, List
from core.chain import Blockchain
from core.block import Block

# Legacy global ref for backwards compatibility
network_instance = None

def set_network(network):
    global network_instance
    network_instance = network

def run(chain: Blockchain, port: int, target_network=None):
    app = FastAPI()
    
    # Store references natively on the application instance
    app.state.chain = chain
    app.state.network = target_network if target_network else network_instance

    @app.get("/blocks")
    def get_blocks():
        return [b.to_dict() for b in app.state.chain.chain]

    @app.get("/mempool")
    def get_mempool():
        """Returns all pending (unconfirmed) transactions ordered by gas_price."""
        return app.state.chain.mempool.to_dict()

    @app.get("/nonce/{address}")
    def get_nonce(address: str):
        """Returns the next valid nonce the given address should use for its next transaction."""
        nonce = app.state.chain.get_nonce(address)
        return {"address": address, "next_nonce": nonce}

    @app.get("/state-root")
    def get_state_root():
        """Returns the current state root hash for state consensus checks."""
        return {"state_root": app.state.chain.current_state_root}

    @app.get("/tx-proof/{block_index}/{tx_index}")
    def get_tx_proof(block_index: int, tx_index: int):
        """Generate a Merkle inclusion proof for a transaction in a specific block."""
        _chain = app.state.chain
        if block_index < 0 or block_index >= len(_chain.chain):
            return {"status": "error", "message": "Block not found"}
            
        block = _chain.chain[block_index]
        if tx_index < 0 or tx_index >= len(block.transactions):
            return {"status": "error", "message": "Transaction index out of range"}
            
        try:
            from core.merkle import generate_merkle_proof
            proof = generate_merkle_proof(block.transactions, tx_index)
            return {
                "block_index": block_index,
                "tx_index": tx_index,
                "merkle_root": block.merkle_root,
                "proof": proof
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @app.post("/transactions")
    def submit_transaction(tx: dict, background_tasks: BackgroundTasks):
        """Called by a DApp/User directly to submit a transaction."""
        _chain = app.state.chain
        _net = app.state.network

        if _chain.role == "light":
            return {"status": "error", "message": "Light nodes cannot accept transactions. Please submit to a Full node."}

        ok = _chain.add_transaction(tx)
        if not ok:
            return {"status": "rejected", "message": "Transaction rejected. Check nonce, gas_price, and signature."}

        if _net:
            _net.broadcast_transaction(tx)

        return {"status": "received", "tx": tx}
        
    @app.websocket("/ws")
    async def websocket_peer_endpoint(websocket: WebSocket):
        """Incoming websocket connection from another peer."""
        await websocket.accept()
        print(f"[API Server {port}] Incoming peer connection accepted.")
        
        _net = app.state.network
        if _net:
            _net.add_incoming_connection(websocket)
            
            try:
                # Keep listening to this socket forever
                while True:
                    data = await websocket.receive_text()
                    response = _net._handle_incoming_message(data)
                    if response:  # e.g. SYNC_RESPONSE for a SYNC_REQUEST
                        await websocket.send_text(response)
            except WebSocketDisconnect:
                print(f"[API Server {port}] Peer disconnected.")
                _net.remove_incoming_connection(websocket)
            except Exception as e:
                print(f"[API Server {port}] WebSocket Error: {e}")
                _net.remove_incoming_connection(websocket)
        else:
            await websocket.close()

    try:
        # Pass log_config=None to prevent Uvicorn from swallowing all our logs!
        uvicorn.run(app, host="0.0.0.0", port=port, log_config=None)
    except Exception as e:
        print(f"Uvicorn Error on port {port}: {e}")
