from fastapi import FastAPI, BackgroundTasks
import uvicorn
from typing import Dict, Any, List
from core.chain import Blockchain
from core.block import Block

# Global ref to network to broadcast
network_instance = None

def set_network(network):
    global network_instance
    network_instance = network

def run(chain: Blockchain, port: int):
    app = FastAPI()

    @app.get("/blocks")
    def get_blocks():
        return [b.to_dict() for b in chain.chain]

    @app.post("/transactions")
    def submit_transaction(tx: dict, background_tasks: BackgroundTasks):
        """Called by a DApp/User directly to submit a transaction."""
        
        # Light nodes do not accept direct transactions to mine, they only read
        if chain.role == "light":
             return {"status": "error", "message": "Light nodes cannot accept transactions. Please submit to a Full node."}
             
        chain.add_transaction(tx)
        
        # Broadcast to other peers so they know about it
        if network_instance:
            background_tasks.add_task(network_instance.broadcast_transaction, tx)
            
        return {"status": "received", "tx": tx}
        
    @app.post("/transactions/sync")
    def sync_transaction(payload: dict):
        """Called by another Node (Peer) to share a transaction."""
        if chain.role == "light":
             # Light nodes ignore unconfirmed transactions
             return {"status": "ignored", "reason": "light_node"}

        tx = payload.get("tx")
        if tx and tx not in chain.pending_transactions:
            chain.add_transaction(tx)
            # Optionally further gossip to my connections
        return {"status": "synced"}

    @app.post("/blocks/sync")
    def sync_block(payload: dict):
        """Called by another Node (Peer) to share a mined block."""
        block_data = payload.get("block")
        if not block_data:
            return {"status": "ignored"}
            
        # Reconstruct block
        block = Block(
            index=block_data["index"],
            transactions=block_data["transactions"],
            timestamp=block_data["timestamp"],
            previous_hash=block_data["previous_hash"],
            validator=block_data["validator"]
        )
        block.nonce = block_data.get("nonce", 0)
        block.hash = block_data["hash"]
        
        # We try to add it. chain.add_block validates it internally!
        if chain.last_block.index < block.index:
            success = chain.add_block(block)
            if success:
                print(f"P2P SYNC: Successfully appended block {block.index} from peer network!")
                
                # Only full/miner nodes have a mempool to clean up
                if chain.role in ["full", "miner"]:
                    for b_tx in block.transactions:
                        if b_tx in chain.pending_transactions:
                            chain.pending_transactions.remove(b_tx)
            else:
                print(f"P2P SYNC: Rejected invalid block {block.index} from peer network.")
        
        return {"status": "processed"}

    uvicorn.run(app, host="0.0.0.0", port=port)
