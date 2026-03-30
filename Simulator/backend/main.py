"""
ChainForge Network Simulator - Backend Server
FastAPI-based REST API and WebSocket event bridge.
"""

import logging
import sys
import os
import json
import time
from typing import Optional, List, Dict, Any
from dataclasses import asdict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from chain_adapter import IChainAdapter, Transaction, ChainEvent
from config_parser import ConfigParser, Config
from process_manager import ProcessManager
from event_bridge import EventBridge

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ── FastAPI app ──────────────────────────────────────────────────────────────

app = FastAPI(title="ChainForge Network Simulator")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend static files
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.isdir(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

# ── Global state ─────────────────────────────────────────────────────────────

config: Optional[Config] = None
config_parser = ConfigParser()
adapter: Optional[IChainAdapter] = None
process_manager: Optional[ProcessManager] = None
event_bridge: Optional[EventBridge] = None
connected_ws_clients: List[WebSocket] = []

# Metrics tracking
metrics_state: Dict[str, Any] = {
    "total_blocks": 0,
    "total_transactions": 0,
    "block_timestamps": [],      # last 10 block commit timestamps
    "tx_timestamps": [],         # last 10s of tx timestamps for TPS
    "consensus_latency_ms": 0,
    "last_tx_broadcast_time": 0,
}


# ── WebSocket broadcast helper ──────────────────────────────────────────────

async def broadcast_event(event: ChainEvent):
    """Push an event to all connected WebSocket clients."""
    event_dict = {
        "type": event.event_type,
        "timestamp": event.timestamp,
        "nodeId": event.node_id,
        "payload": event.payload,
    }
    message = json.dumps(event_dict)
    disconnected = []
    for ws in connected_ws_clients:
        try:
            await ws.send_text(message)
        except Exception:
            disconnected.append(ws)
    for ws in disconnected:
        connected_ws_clients.remove(ws)

    # Update metrics based on event type
    _update_metrics_from_event(event)


def _update_metrics_from_event(event: ChainEvent):
    """Update internal metrics state from chain events."""
    now = int(time.time() * 1000)

    if event.event_type == "BLOCK_COMMITTED":
        metrics_state["total_blocks"] += 1
        metrics_state["block_timestamps"].append(now)
        # Keep only last 10
        if len(metrics_state["block_timestamps"]) > 10:
            metrics_state["block_timestamps"] = metrics_state["block_timestamps"][-10:]
        # Consensus latency: time from last TX_BROADCAST to this commit
        if metrics_state["last_tx_broadcast_time"] > 0:
            metrics_state["consensus_latency_ms"] = now - metrics_state["last_tx_broadcast_time"]

    elif event.event_type == "TX_BROADCAST":
        metrics_state["total_transactions"] += 1
        metrics_state["tx_timestamps"].append(now)
        metrics_state["last_tx_broadcast_time"] = now
        # Keep only last 30 seconds
        cutoff = now - 30000
        metrics_state["tx_timestamps"] = [t for t in metrics_state["tx_timestamps"] if t > cutoff]


# ── Health & Config ─────────────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    node_count = 0
    block_height = 0
    if process_manager:
        node_count = len(process_manager.get_all_processes())
    return {
        "status": "ok",
        "chainRunning": config is not None,
        "nodeCount": node_count,
        "blockHeight": metrics_state["total_blocks"],
        "consensus": config.consensus if config else None,
    }


@app.get("/config")
async def get_config():
    """Get the loaded project configuration."""
    if config is None:
        raise HTTPException(status_code=400, detail="No project loaded. Load a project first.")
    return config_parser.to_dict(config)


@app.post("/load-project")
async def load_project(request: Request):
    """
    Load a ChainForge project.
    Body: { "config_path": "/path/to/config.yaml" }
    """
    global config, adapter, process_manager, event_bridge

    body = await request.json()
    config_path = body.get("config_path")
    if not config_path:
        raise HTTPException(status_code=400, detail="config_path is required.")

    try:
        config = config_parser.parse_file(config_path)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # ── Merge genesis.json from platform code (if present) ──
    # When a user extracts a downloaded zip into chain_node/, the genesis.json
    # contains the REAL consensus, sync, and network config from the platform.
    # We override the generic YAML defaults with these values.
    chain_node_dir = os.path.join(os.path.dirname(__file__), "chain_node")
    genesis_path = os.path.join(chain_node_dir, "config", "genesis.json")
    if os.path.isfile(genesis_path):
        try:
            with open(genesis_path, "r") as gf:
                genesis = json.load(gf)

            net_type = genesis.get("networkType")
            if net_type == "public":
                config.network_type = "public"
                config.consensus = genesis.get("publicConsensus", config.consensus)
                config.sync_mode = genesis.get("publicSyncMode", config.sync_mode)
            elif net_type == "permissioned":
                config.network_type = "permissioned"
                p_type = genesis.get("permissionedType", "centralized")
                config.governance = p_type
                if p_type == "centralized":
                    config.consensus = genesis.get("centralizedConsensus", config.consensus)
                    config.sync_mode = genesis.get("centralizedSync", config.sync_mode)
                else:  # consortium
                    config.consensus = genesis.get("consortiumConsensus", config.consensus)
                    config.sync_mode = genesis.get("consortiumSync", config.sync_mode)

            logger.info(f"Merged genesis.json: consensus={config.consensus}, "
                        f"sync_mode={config.sync_mode}, network={config.network_type}")
        except Exception as e:
            logger.warning(f"Could not read genesis.json, using YAML defaults: {e}")

    # Import adapter factory here to avoid circular imports at module level
    from adapters import get_adapter
    adapter = get_adapter(config.consensus)

    # Initialize process manager
    process_manager = ProcessManager(max_nodes=config.max_nodes)

    # Initialize event bridge and wire it to broadcast
    event_bridge = EventBridge(buffer_size=100)
    event_bridge.register_broadcast_callback(broadcast_event)
    event_bridge.subscribe_to_adapter_events(adapter)

    logger.info(f"Project loaded: consensus={config.consensus}, max_nodes={config.max_nodes}")

    return {
        "status": "loaded",
        "network_type": config.network_type,
        "governance": config.governance,
        "consensus": config.consensus,
        "node_roles": config.node_roles,
        "sync_mode": config.sync_mode,
        "max_nodes": config.max_nodes,
        "block_time_ms": config.block_time_ms,
        "modules": config.modules,
    }


@app.get("/project")
async def get_project_status():
    """
    Get the current project status and configuration.
    """
    if config is None:
        return {"status": "not_loaded"}

    return {
        "status": "loaded",
        "network_type": config.network_type,
        "governance": config.governance,
        "consensus": config.consensus,
        "node_roles": config.node_roles,
        "sync_mode": config.sync_mode,
        "max_nodes": config.max_nodes,
        "block_time_ms": config.block_time_ms,
        "modules": config.modules,
    }


# ── Node Management ─────────────────────────────────────────────────────────

@app.post("/nodes")
async def add_node(request: Request):
    """
    Add a new node to the network.
    Body: { "role": "validator" }
    """
    if config is None or process_manager is None or adapter is None:
        raise HTTPException(status_code=400, detail="No project loaded. Load a project first.")

    body = await request.json()
    role = body.get("role", "").lower()

    # Validate role against config
    if role not in config.node_roles:
        raise HTTPException(
            status_code=400,
            detail=f"'{role}' nodes are not available in this blockchain. "
                   f"Supported roles: {config.node_roles}"
        )

    # Enforce max_nodes limit server-side
    current_count = len(process_manager.get_all_processes())
    if config.max_nodes > 0 and current_count >= config.max_nodes:
        raise HTTPException(
            status_code=403,
            detail=f"Maximum node limit ({config.max_nodes}) reached for this configuration."
        )

    # Enforce permissioned network rules
    if config.network_type == "permissioned":
        # In a permissioned network, only admin can add.
        # For now, we allow if no nodes exist (first node is implicitly admin).
        # Once nodes exist, only requests from admin should be allowed.
        # Simplified: first node auto-allowed, subsequent require admin header.
        if current_count > 0:
            admin_token = (await request.body()).decode() if hasattr(request, 'body') else ""
            # For Phase 1, we allow all additions but log the permissioned check
            logger.info("Permissioned network: allowing node addition (admin check simplified)")

    try:
        node_process = await process_manager.spawn_node_process(
            role=role,
            consensus=config.consensus,
            block_time_ms=config.block_time_ms,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Register the node with the adapter and start stdout reader
    # so chain events from the real node process are captured
    from chain_adapter import NodeProcess as AdapterNodeProcess
    adapter_node = AdapterNodeProcess(
        node_id=node_process.node_id,
        role=node_process.role,
        port=node_process.port,
        pid=node_process.pid,
        status="ready",
    )
    if hasattr(adapter, 'nodes'):
        adapter.nodes[node_process.node_id] = adapter_node
    if hasattr(adapter, 'start_stdout_reader') and node_process.process is not None:
        await adapter.start_stdout_reader(node_process.node_id, node_process.process)
    elif node_process.process is not None and event_bridge is not None:
        # Fallback: read stdout directly for adapters that don't have start_stdout_reader
        import asyncio as _asyncio

        async def _read_stdout(nid, proc, bridge):
            try:
                while proc.returncode is None:
                    line = await proc.stdout.readline()
                    if not line:
                        break
                    text = line.decode(errors="replace").strip()
                    if text.startswith("EVENT:"):
                        try:
                            data = json.loads(text[6:])
                            evt = ChainEvent(
                                event_type=data.get("type", "UNKNOWN"),
                                timestamp=data.get("timestamp", int(time.time() * 1000)),
                                node_id=data.get("nodeId", nid),
                                payload=data.get("payload", {}),
                            )
                            await bridge.on_chain_event(evt)
                        except json.JSONDecodeError:
                            pass
            except Exception as e:
                logger.warning(f"Stdout reader for {nid} error: {e}")

        _asyncio.get_event_loop().create_task(
            _read_stdout(node_process.node_id, node_process.process, event_bridge)
        )

    # Emit NODE_JOINED via event bridge
    if event_bridge:
        event = ChainEvent(
            event_type="NODE_JOINED",
            timestamp=int(time.time() * 1000),
            node_id=node_process.node_id,
            payload={
                "nodeId": node_process.node_id,
                "role": node_process.role,
                "address": f"localhost:{node_process.port}",
            }
        )
        await event_bridge.on_chain_event(event)

        # Emit SYNC_PROGRESS immediately so the frontend shows "syncing"
        sync_progress_event = ChainEvent(
            event_type="SYNC_PROGRESS",
            timestamp=int(time.time() * 1000),
            node_id=node_process.node_id,
            payload={
                "nodeId": node_process.node_id,
                "currentHeight": 0,
                "targetHeight": len(event_bridge.event_buffer) if event_bridge else 0,
            }
        )
        await event_bridge.on_chain_event(sync_progress_event)

        # Delay SYNC_COMPLETE by replaying historical blocks
        import asyncio as _asyncio_sync
        nid_for_sync = node_process.node_id
        
        # Grab historical blocks committed so far
        historical_blocks = []
        if event_bridge:
            historical_blocks = [e for e in event_bridge.event_buffer if e.event_type == "BLOCK_COMMITTED"]

        async def _delayed_sync_complete(nid, bridge, blocks):
            target_h = len(blocks)
            if target_h == 0:
                # No blocks yet, instantly synced
                pass
            else:
                for idx, block_event in enumerate(blocks):
                    # Half-second delay per block to visually see it catch up
                    await _asyncio_sync.sleep(0.5)
                    progress_event = ChainEvent(
                        event_type="SYNC_PROGRESS",
                        timestamp=int(time.time() * 1000),
                        node_id=nid,
                        payload={
                            "nodeId": nid,
                            "currentHeight": block_event.payload.get("blockHeight", idx + 1),
                            "targetHeight": target_h,
                            "blockData": block_event.payload
                        }
                    )
                    await bridge.on_chain_event(progress_event)
                    
            complete_event = ChainEvent(
                event_type="SYNC_COMPLETE",
                timestamp=int(time.time() * 1000),
                node_id=nid,
                payload={
                    "nodeId": nid,
                    "finalHeight": target_h,
                }
            )
            await bridge.on_chain_event(complete_event)

        _asyncio_sync.get_event_loop().create_task(
            _delayed_sync_complete(nid_for_sync, event_bridge, historical_blocks)
        )

    return {
        "nodeId": node_process.node_id,
        "role": node_process.role,
        "port": node_process.port,
        "pid": node_process.pid,
        "status": node_process.status,
    }


@app.get("/nodes")
async def list_nodes():
    """List all nodes in the network."""
    if process_manager is None:
        raise HTTPException(status_code=400, detail="No project loaded.")

    processes = process_manager.get_all_processes()
    nodes = []
    for nid, proc in processes.items():
        nodes.append({
            "nodeId": proc.node_id,
            "role": proc.role,
            "port": proc.port,
            "pid": proc.pid,
            "status": proc.status,
        })
    return {"nodes": nodes}


@app.get("/nodes/{node_id}")
async def get_node_status(node_id: str):
    """Get status of a specific node."""
    if process_manager is None:
        raise HTTPException(status_code=400, detail="No project loaded.")

    status = process_manager.get_process_info(node_id)
    if status is None:
        raise HTTPException(status_code=404, detail=f"Node '{node_id}' not found.")
    return {
        "nodeId": status.node_id,
        "role": status.role,
        "port": status.port,
        "pid": status.pid,
        "status": status.status,
    }


@app.delete("/nodes/{node_id}")
async def remove_node(node_id: str):
    """Remove a node from the network."""
    if process_manager is None:
        raise HTTPException(status_code=400, detail="No project loaded.")

    try:
        await process_manager.terminate_node_process(node_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Emit NODE_OFFLINE via event bridge
    if event_bridge:
        event = ChainEvent(
            event_type="NODE_OFFLINE",
            timestamp=int(time.time() * 1000),
            node_id=node_id,
            payload={
                "nodeId": node_id,
                "reason": "terminated by user",
            }
        )
        await event_bridge.on_chain_event(event)

    return {"status": "terminated", "nodeId": node_id}


# ── Transactions & Blocks ───────────────────────────────────────────────────

@app.post("/transaction")
async def submit_transaction(request: Request):
    """
    Submit a transaction to the network.
    Body: { "fromNodeId": "node-1", "toNodeId": "node-2", "payload": {...} }
    """
    if config is None or adapter is None or process_manager is None:
        raise HTTPException(status_code=400, detail="No project loaded.")

    body = await request.json()
    from_node_id = body.get("fromNodeId")
    to_node_id = body.get("toNodeId", "")
    payload = body.get("payload", {})

    if not from_node_id:
        raise HTTPException(status_code=400, detail="fromNodeId is required.")

    # Check that the source node exists and is online
    source_proc = process_manager.get_process_info(from_node_id)
    if source_proc is None:
        raise HTTPException(status_code=404, detail=f"Node '{from_node_id}' not found.")
    if source_proc.status == "stopped":
        raise HTTPException(
            status_code=400,
            detail=f"Node is offline. Bring it back online before initiating a transaction."
        )

    # Enforce governance-based permission rules server-side
    governance = config.governance
    if governance == "centralized":
        # Only the leader/designated node can initiate
        # For simplicity: only first-spawned node or the node currently marked as leader
        pass  # Will enforce more strictly once LEADER_ELECTED tracking is in place
    elif governance == "consortium":
        # Any validator can initiate
        if source_proc.role not in ("validator", "authority"):
            raise HTTPException(
                status_code=403,
                detail=f"Only validator nodes can create transactions in a "
                       f"consortium governance model."
            )
    # decentralized/democratic: any miner or full node
    elif governance in ("decentralized", "democratic"):
        if source_proc.role not in ("miner", "full", "validator"):
            raise HTTPException(
                status_code=403,
                detail=f"Only miner or full nodes can create transactions in a "
                       f"{governance} governance model."
            )

    # Build transaction object
    tx = Transaction(
        tx_hash="",  # Will be set by the chain
        from_address=from_node_id,
        to_address=to_node_id,
        amount=float(payload.get("amount", 0)),
        memo=str(payload.get("memo", "")),
        timestamp=int(time.time() * 1000),
    )

    try:
        tx_hash = await adapter.submit_transaction(tx, from_node_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transaction submission failed: {e}")

    # Emit TX_BROADCAST
    if event_bridge:
        event = ChainEvent(
            event_type="TX_BROADCAST",
            timestamp=int(time.time() * 1000),
            node_id=from_node_id,
            payload={
                "txId": tx_hash,
                "fromNodeId": from_node_id,
                "toNodeId": to_node_id,
            }
        )
        await event_bridge.on_chain_event(event)

    return {"txHash": tx_hash, "status": "broadcast"}


@app.get("/blocks")
async def get_blocks(since: int = 0, limit: int = 50):
    """Get committed blocks."""
    if adapter is None:
        raise HTTPException(status_code=400, detail="No project loaded.")

    try:
        blocks = await adapter.get_blocks(since)
        # Apply limit
        block_list = []
        for b in blocks[:limit]:
            block_list.append({
                "blockNumber": b.block_number,
                "blockHash": b.block_hash,
                "proposer": b.proposer,
                "txCount": b.tx_count,
                "timestamp": b.timestamp,
            })
        return {"blocks": block_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/blocks/{block_number}")
async def get_block(block_number: int):
    """Get details of a specific block."""
    if adapter is None:
        raise HTTPException(status_code=400, detail="No project loaded.")

    try:
        blocks = await adapter.get_blocks(block_number)
        for b in blocks:
            if b.block_number == block_number:
                return {
                    "blockNumber": b.block_number,
                    "blockHash": b.block_hash,
                    "proposer": b.proposer,
                    "txCount": b.tx_count,
                    "timestamp": b.timestamp,
                    "votes": b.votes_received,
                }
        raise HTTPException(status_code=404, detail=f"Block #{block_number} not found.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Consensus & Metrics ─────────────────────────────────────────────────────

@app.get("/consensus-state")
async def get_consensus_state():
    """Get current consensus state and phase information."""
    if adapter is None:
        raise HTTPException(status_code=400, detail="No project loaded.")

    try:
        state = await adapter.get_consensus_state()
        return {
            "consensusType": state.consensus_type,
            "currentRound": state.current_round,
            "currentPhase": state.current_phase,
            "currentLeader": state.current_leader,
            "validatorCount": state.validator_count,
            "faultyNodes": state.faulty_nodes,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
async def get_metrics():
    """Get live metrics."""
    now = int(time.time() * 1000)
    node_count = 0
    if process_manager:
        node_count = len(process_manager.get_all_processes())

    # Calculate TPS: transactions in the last 10 seconds
    cutoff = now - 10000
    recent_tx = [t for t in metrics_state["tx_timestamps"] if t > cutoff]
    current_tps = len(recent_tx) / 10.0 if recent_tx else 0

    # Calculate average block time from last 5 blocks
    avg_block_time = 0
    timestamps = metrics_state["block_timestamps"]
    if len(timestamps) >= 2:
        diffs = [timestamps[i] - timestamps[i - 1] for i in range(1, min(6, len(timestamps)))]
        avg_block_time = sum(diffs) / len(diffs) if diffs else 0

    # Fault tolerance (consensus-dependent, simplified)
    fault_tolerance = "N/A"
    if config:
        if config.consensus == "none":
            fault_tolerance = "N/A — no consensus mechanism active."
        elif config.consensus in ("pbft", "hotstuff"):
            n = node_count
            f_val = (n - 1) // 3
            fault_tolerance = f"Tolerates up to f={f_val} Byzantine faults"
        elif config.consensus in ("raft", "paxos"):
            required = node_count // 2 + 1
            fault_tolerance = f"Requires majority: {required} of {node_count} nodes"
        elif config.consensus == "tendermint":
            required = (node_count * 2 + 2) // 3
            fault_tolerance = f"Requires 2/3+: {required} of {node_count} validators"
        elif config.consensus == "pow":
            fault_tolerance = "51% hash power threshold"
        elif config.consensus == "poa":
            fault_tolerance = "All authorities must be live"

    return {
        "totalNodes": node_count,
        "totalBlocks": metrics_state["total_blocks"],
        "totalTransactions": metrics_state["total_transactions"],
        "consensusType": config.consensus if config else None,
        "currentTPS": round(current_tps, 2),
        "averageBlockTimeMs": round(avg_block_time),
        "consensusLatencyMs": metrics_state["consensus_latency_ms"],
        "faultTolerance": fault_tolerance,
    }


# ── Attack Simulation ───────────────────────────────────────────────────────

@app.post("/attack")
async def execute_attack(request: Request):
    """Execute an attack simulation."""
    if config is None or process_manager is None:
        raise HTTPException(status_code=400, detail="No project loaded.")

    body = await request.json()
    attack_type = body.get("attack_type")
    target_node_id = body.get("target_node_id")

    if attack_type not in ("drop_node", "reject_block", "partition", "slow_node"):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid attack type '{attack_type}'. "
                   f"Must be one of: drop_node, reject_block, partition, slow_node"
        )

    if not target_node_id:
        raise HTTPException(status_code=400, detail="target_node_id is required.")

    # For now, implement drop_node
    if attack_type == "drop_node":
        try:
            await process_manager.terminate_node_process(target_node_id)
            if event_bridge:
                event = ChainEvent(
                    event_type="NODE_OFFLINE",
                    timestamp=int(time.time() * 1000),
                    node_id=target_node_id,
                    payload={"nodeId": target_node_id, "reason": "attack: drop_node"}
                )
                await event_bridge.on_chain_event(event)
        except (ValueError, RuntimeError) as e:
            raise HTTPException(status_code=400, detail=str(e))

    return {"status": "attack_active", "attackType": attack_type, "targetNodeId": target_node_id}


@app.post("/attack/stop")
async def stop_attack():
    """Stop active attack simulation."""
    return {"status": "attack_stopped"}


# ── Utilities ───────────────────────────────────────────────────────────────

@app.post("/reset")
async def reset_simulator():
    """Reset simulator to initial state."""
    global metrics_state

    if process_manager:
        await process_manager.terminate_all_nodes()

    if event_bridge:
        await event_bridge.clear_buffer()

    metrics_state = {
        "total_blocks": 0,
        "total_transactions": 0,
        "block_timestamps": [],
        "tx_timestamps": [],
        "consensus_latency_ms": 0,
        "last_tx_broadcast_time": 0,
    }

    return {"status": "reset_complete"}


@app.get("/export-trace")
async def export_trace():
    """Export event trace as JSON."""
    if event_bridge is None:
        raise HTTPException(status_code=400, detail="No project loaded.")

    trace = event_bridge.export_event_trace()
    return JSONResponse(
        content=json.loads(trace),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=event_trace.json"}
    )


# ── WebSocket ───────────────────────────────────────────────────────────────

@app.websocket("/events")
async def events_stream(websocket: WebSocket):
    """
    WebSocket endpoint for live event streaming.
    On connect: send buffered recent events to restore state.
    Then push all future events in real time.
    """
    await websocket.accept()
    connected_ws_clients.append(websocket)
    logger.info(f"WebSocket client connected. Total clients: {len(connected_ws_clients)}")

    # Send recent events for state restoration
    if event_bridge:
        recent = event_bridge.get_recent_events(count=100)
        for evt in recent:
            event_dict = {
                "type": evt.event_type,
                "timestamp": evt.timestamp,
                "nodeId": evt.node_id,
                "payload": evt.payload,
            }
            try:
                await websocket.send_text(json.dumps(event_dict))
            except Exception:
                break

    try:
        while True:
            # Keep connection alive; listen for client messages (heartbeat/ping)
            data = await websocket.receive_text()
            # Optional: handle client commands like "replay" or "ping"
            if data == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected.")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        if websocket in connected_ws_clients:
            connected_ws_clients.remove(websocket)


# ── Startup ─────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    """Initialize backend on startup if config path provided."""
    global config, adapter, process_manager, event_bridge

    # Check for config path from command line or environment
    config_path = os.environ.get("CHAINFORGE_CONFIG")
    if config_path:
        try:
            config = config_parser.parse_file(config_path)

            # ── Merge genesis.json (same logic as load_project) ──
            chain_node_dir = os.path.join(os.path.dirname(__file__), "chain_node")
            genesis_path = os.path.join(chain_node_dir, "config", "genesis.json")
            if os.path.isfile(genesis_path):
                try:
                    with open(genesis_path, "r") as gf:
                        genesis = json.load(gf)
                    net_type = genesis.get("networkType")
                    if net_type == "public":
                        config.network_type = "public"
                        config.consensus = genesis.get("publicConsensus", config.consensus)
                        config.sync_mode = genesis.get("publicSyncMode", config.sync_mode)
                    elif net_type == "permissioned":
                        config.network_type = "permissioned"
                        p_type = genesis.get("permissionedType", "centralized")
                        config.governance = p_type
                        if p_type == "centralized":
                            config.consensus = genesis.get("centralizedConsensus", config.consensus)
                            config.sync_mode = genesis.get("centralizedSync", config.sync_mode)
                        else:  # consortium
                            config.consensus = genesis.get("consortiumConsensus", config.consensus)
                            config.sync_mode = genesis.get("consortiumSync", config.sync_mode)
                    logger.info(f"Startup merged genesis.json: consensus={config.consensus}, "
                                f"sync_mode={config.sync_mode}, network={config.network_type}")
                except Exception as e:
                    logger.warning(f"Could not read genesis.json during startup: {e}")

            from adapters import get_adapter
            adapter = get_adapter(config.consensus)
            process_manager = ProcessManager(max_nodes=config.max_nodes)
            event_bridge = EventBridge(buffer_size=100)
            event_bridge.register_broadcast_callback(broadcast_event)
            event_bridge.subscribe_to_adapter_events(adapter)
            logger.info(f"Auto-loaded config: consensus={config.consensus}")
        except Exception as e:
            logger.warning(f"Could not auto-load config: {e}")


if __name__ == "__main__":
    import uvicorn
    import socket

    preferred_port = int(os.environ.get("PORT", 8000))
    config_path = None

    if len(sys.argv) > 1:
        config_path = sys.argv[1]
        os.environ["CHAINFORGE_CONFIG"] = config_path

    # Try preferred port, then fallback to +1, +2
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

    logger.info(f"Starting ChainForge Simulator backend on http://0.0.0.0:{port}")
    logger.info(f"Open the dashboard at: http://localhost:{port}/static/index.html")
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)
