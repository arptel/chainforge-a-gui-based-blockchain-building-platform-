"""
ChainForge Simulator — Universal Runner Backend
================================================
Auto-detects chain_node/ contents, builds an in-process node network,
and serves a REST + WebSocket API for the frontend.
"""

import os
import sys
import json
import asyncio
import logging
import time
from typing import List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("simulator")

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(title="ChainForge Simulator", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend static files
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")
if os.path.isdir(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

# ---------------------------------------------------------------------------
# Global state
# ---------------------------------------------------------------------------
node_manager = None          # NodeManager instance
chain_config = None          # normalised config dict
chain_info = None            # rich info dict for ℹ️ panel
connected_ws: List[WebSocket] = []
event_buffer: list = []      # last 200 events for reconnecting clients

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------
class AddNodeRequest(BaseModel):
    role: str

class TransactionRequest(BaseModel):
    fromNodeId: str
    text: str

class VoteRequest(BaseModel):
    voterNodeId: str
    requestId: str
    approve: bool

class ToggleRequest(BaseModel):
    online: bool

# ---------------------------------------------------------------------------
# Event broadcasting
# ---------------------------------------------------------------------------
async def _ws_broadcast(event: dict):
    """Push an event to all connected WebSocket clients."""
    data = json.dumps(event)
    dead = []
    for ws in connected_ws:
        try:
            await ws.send_text(data)
        except Exception:
            dead.append(ws)
    for ws in dead:
        connected_ws.remove(ws)


def on_node_event(event: dict):
    """
    Synchronous callback from NodeManager.
    Buffers the event and schedules async broadcast.
    """
    event_buffer.append(event)
    if len(event_buffer) > 200:
        del event_buffer[:len(event_buffer) - 200]

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(_ws_broadcast(event))
    except RuntimeError:
        pass

# ---------------------------------------------------------------------------
# Startup — auto-detect chain_node and initialise
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def startup():
    global node_manager, chain_config, chain_info

    from config_generator import detect_chain_node, load_genesis, generate_config, generate_chain_info
    from node_manager import NodeManager

    backend_dir = os.path.dirname(os.path.abspath(__file__))
    chain_node_dir = detect_chain_node(backend_dir)

    if not chain_node_dir:
        logger.warning("No chain_node/ folder detected — simulator will start without a chain.")
        return

    logger.info(f"Detected chain_node at: {chain_node_dir}")

    genesis = load_genesis(chain_node_dir)
    chain_config = generate_config(genesis)
    chain_info = generate_chain_info(genesis, chain_config)

    logger.info(f"Chain config: consensus={chain_config['consensus']}, "
                f"network={chain_config['network_type']}, "
                f"governance={chain_config['governance']}")

    node_manager = NodeManager(
        chain_node_dir=chain_node_dir,
        config=chain_config,
        chain_info=chain_info,
        event_callback=on_node_event,
    )

    # Auto-create node-0 for permissioned networks
    if chain_config["governance"] != "decentralized":
        owner_role = "validator" if chain_config["governance"] == "consortium" else "full"
        node_manager.create_node(role=owner_role, node_id="node-0")
        logger.info(f"Auto-created node-0 as {owner_role} (owner)")

    logger.info("Simulator backend ready!")

# ---------------------------------------------------------------------------
# REST Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "ok", "chain_loaded": node_manager is not None}


@app.get("/chain-info")
async def get_chain_info():
    """Return full chain description for the ℹ️ panel."""
    if chain_info is None:
        raise HTTPException(404, "No chain loaded. Place chain code in backend/chain_node/")
    return chain_info


@app.get("/nodes")
async def list_nodes():
    """List all nodes with summary info."""
    if node_manager is None:
        raise HTTPException(503, "No chain loaded")
    return {"nodes": node_manager.get_all_nodes_summary()}


@app.get("/nodes/{node_id}")
async def get_node(node_id: str):
    """Get summary for a specific node."""
    if node_manager is None:
        raise HTTPException(503, "No chain loaded")
    try:
        data = node_manager.get_node_data(node_id)
        return data
    except ValueError as e:
        raise HTTPException(404, str(e))


@app.get("/nodes/{node_id}/data")
async def get_node_data(node_id: str):
    """Get detailed node data (blocks, state, logs) for the detail panel."""
    if node_manager is None:
        raise HTTPException(503, "No chain loaded")
    try:
        return node_manager.get_node_data(node_id)
    except ValueError as e:
        raise HTTPException(404, str(e))


@app.post("/nodes")
async def add_node(req: AddNodeRequest):
    """
    Add a node to the network.
    - Public: creates immediately.
    - Permissioned: creates a pending join request.
    """
    if node_manager is None:
        raise HTTPException(503, "No chain loaded")

    if req.role not in chain_config["node_roles"]:
        raise HTTPException(400, f"Invalid role '{req.role}'. Allowed: {chain_config['node_roles']}")

    try:
        result = node_manager.request_join(req.role)
        return result
    except Exception as e:
        raise HTTPException(500, str(e))


@app.delete("/nodes/{node_id}")
async def remove_node(node_id: str):
    """Remove a node from the network."""
    if node_manager is None:
        raise HTTPException(503, "No chain loaded")
    try:
        node_manager.remove_node(node_id)
        return {"status": "removed", "node_id": node_id}
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/nodes/vote")
async def vote_on_join(req: VoteRequest):
    """Cast a vote on a pending join request."""
    if node_manager is None:
        raise HTTPException(503, "No chain loaded")
    try:
        result = node_manager.vote_on_join(req.voterNodeId, req.requestId, req.approve)
        return result
    except ValueError as e:
        raise HTTPException(400, str(e))

@app.post("/nodes/{node_id}/toggle")
async def toggle_node(node_id: str, req: ToggleRequest):
    """Toggle a node ON or OFF."""
    if node_manager is None:
        raise HTTPException(503, "No chain loaded")
    try:
        node_manager.toggle_node(node_id, req.online)
        return {"status": "ok", "node_id": node_id, "online": req.online}
    except ValueError as e:
        raise HTTPException(404, str(e))

@app.get("/pending-joins")
async def get_pending_joins():
    """Get all pending join requests."""
    if node_manager is None:
        raise HTTPException(503, "No chain loaded")
    return {"pending": node_manager.get_pending_joins()}


@app.post("/transaction")
async def submit_transaction(req: TransactionRequest):
    """Submit a data transaction (text statement)."""
    if node_manager is None:
        raise HTTPException(503, "No chain loaded")
    try:
        result = node_manager.submit_transaction(req.fromNodeId, req.text)
        return result
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/reset")
async def reset_network():
    """Reset the entire network — remove all nodes, delete all DBs."""
    if node_manager is None:
        raise HTTPException(503, "No chain loaded")

    node_manager.reset()
    event_buffer.clear()

    # Re-create node-0 for permissioned networks
    if chain_config["governance"] != "decentralized":
        owner_role = "validator" if chain_config["governance"] == "consortium" else "full"
        node_manager.create_node(role=owner_role, node_id="node-0")

    return {"status": "reset"}


# ---------------------------------------------------------------------------
# WebSocket
# ---------------------------------------------------------------------------

@app.websocket("/events")
async def websocket_events(websocket: WebSocket):
    await websocket.accept()
    connected_ws.append(websocket)
    logger.info("WebSocket client connected")

    # Send buffered events for reconnection
    for ev in event_buffer[-50:]:
        try:
            await websocket.send_text(json.dumps(ev))
        except Exception:
            break

    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        if websocket in connected_ws:
            connected_ws.remove(websocket)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    import socket

    preferred_port = int(os.environ.get("PORT", 8000))

    port = preferred_port
    for attempt_port in [preferred_port, preferred_port + 1, preferred_port + 2]:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(("0.0.0.0", attempt_port))
            sock.close()
            port = attempt_port
            break
        except OSError:
            logger.warning(f"Port {attempt_port} is in use, trying next...")
            continue

    logger.info(f"Starting ChainForge Simulator on http://0.0.0.0:{port}")
    logger.info(f"Open the dashboard at: http://localhost:{port}/static/index.html")
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)
