from fastapi import FastAPI
import uvicorn
from core.chain import Blockchain
from api import contract_routes

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

    @app.post("/transactions")
    def submit_transaction(tx: dict):
        # Logic to add tx to pool
        chain.add_transaction(tx)
        return {"status": "received"}

    contract_routes.set_chain(chain)
    app.include_router(contract_routes.router, prefix="/api/v1/contracts", tags=["Smart Contracts"])

    uvicorn.run(app, host="0.0.0.0", port=port)
