from fastapi import FastAPI
import uvicorn
from core.chain import Blockchain
from . import contract_routes
network_instance = None

def set_network(network):
    global network_instance
    network_instance = network

def run(chain: Blockchain, port: int):
    app = FastAPI()

    @app.get("/blocks")
    def get_blocks():
        return [b.to_dict() for b in chain.chain]

    @app.get("/state")
    def get_state():
        return chain.state

    @app.get("/headers")
    def get_headers():
        # Strategy B: Return full payload sufficient for reconstruction
        # (Aliasing /blocks logic since sync modules expect full blocks to do Block.from_dict)
        return [b.to_dict() for b in chain.chain]


    @app.post("/transactions")
    def submit_transaction(tx: dict):
        # Logic to add tx to pool
        chain.add_transaction(tx)
        return {"status": "received"}

    @app.post("/transactions/sync")
    def sync_transaction(data: dict):
        tx = data.get("tx")
        if tx:
            chain.add_transaction(tx)
        return {"status": "synced"}

    @app.post("/blocks/sync")
    def sync_block(data: dict):
        from core.block import Block
        block_data = data.get("block")
        if block_data:
            block = Block.from_dict(block_data)
            if block.index > chain.last_block.index:
                chain.add_block(block)
        return {"status": "synced"}


    contract_routes.set_chain(chain)
    app.include_router(contract_routes.router, prefix="/api/v1/contracts", tags=["Smart Contracts"])

    uvicorn.run(app, host="0.0.0.0", port=port)
