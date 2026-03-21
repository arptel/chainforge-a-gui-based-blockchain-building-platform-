"""
ChainForge Node Process — Standalone script spawned by ProcessManager.

This is a real OS process that simulates a ChainForge blockchain node.
It:
  1. Starts up and prints READY on stdout
  2. Listens on an HTTP port for RPC commands (submit_transaction, get_blocks, etc.)
  3. Runs a block production loop based on consensus type and block_time_ms
  4. Outputs chain events as JSON lines on stdout for the event bridge to consume

Usage:
  python chainforge_node.py --node-id node-1 --role validator --port 8600 \
      --consensus none --block-time-ms 3000
"""

import argparse
import asyncio
import json
import hashlib
import time
import sys
import signal
from typing import List, Dict, Any, Optional

# ── Globals ──────────────────────────────────────────────────────────────────

node_id: str = ""
role: str = ""
port: int = 0
consensus: str = "none"
block_time_ms: int = 3000

blockchain: List[Dict[str, Any]] = []   # committed blocks
mempool: List[Dict[str, Any]] = []       # pending transactions
current_height: int = 0
running: bool = True


# ── Event emission (JSON lines to stdout) ────────────────────────────────────

def emit_event(event_type: str, payload: Dict[str, Any]):
    """Emit a chain event as a JSON line on stdout."""
    event = {
        "type": event_type,
        "timestamp": int(time.time() * 1000),
        "nodeId": node_id,
        "payload": payload,
    }
    line = json.dumps(event)
    print(f"EVENT:{line}", flush=True)


# ── Block production ─────────────────────────────────────────────────────────

def compute_block_hash(block_number: int, prev_hash: str, tx_count: int, ts: int) -> str:
    """Compute a deterministic block hash."""
    data = f"{block_number}:{prev_hash}:{tx_count}:{ts}:{node_id}"
    return hashlib.sha256(data.encode()).hexdigest()


async def produce_block():
    """Produce a new block from the mempool."""
    global current_height

    prev_hash = blockchain[-1]["blockHash"] if blockchain else "0" * 64
    current_height += 1
    ts = int(time.time() * 1000)

    # Gather transactions from mempool
    txs = list(mempool)
    mempool.clear()

    block_hash = compute_block_hash(current_height, prev_hash, len(txs), ts)

    block = {
        "blockNumber": current_height,
        "blockHash": block_hash,
        "proposer": node_id,
        "txCount": len(txs),
        "timestamp": ts,
        "prevHash": prev_hash,
        "transactions": txs,
    }
    blockchain.append(block)

    # Emit BLOCK_PROPOSED
    emit_event("BLOCK_PROPOSED", {
        "blockHeight": current_height,
        "proposerNodeId": node_id,
        "txCount": len(txs),
    })

    # For "none" consensus — immediate commit, no voting
    if consensus == "none":
        # Small delay to simulate processing
        await asyncio.sleep(0.05)
        emit_event("BLOCK_COMMITTED", {
            "blockHeight": current_height,
            "hash": block_hash,
            "proposerNodeId": node_id,
            "txCount": len(txs),
            "commitTime": int(time.time() * 1000) - ts,
        })
    else:
        # For other consensus types, emit CONSENSUS_PHASE events
        # This will be expanded when implementing specific adapters
        emit_event("CONSENSUS_PHASE", {
            "phase": "propose",
            "round": current_height,
            "nodeId": node_id,
        })
        await asyncio.sleep(0.05)
        emit_event("BLOCK_COMMITTED", {
            "blockHeight": current_height,
            "hash": block_hash,
            "proposerNodeId": node_id,
            "txCount": len(txs),
            "commitTime": int(time.time() * 1000) - ts,
        })


async def block_production_loop():
    """Main loop: produce blocks at block_time_ms intervals when mempool has txs."""
    interval = block_time_ms / 1000.0

    while running:
        if len(mempool) > 0:
            await produce_block()

        await asyncio.sleep(interval)


# ── HTTP RPC server ──────────────────────────────────────────────────────────

async def handle_rpc_request(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    """Handle a single HTTP RPC request."""
    try:
        # Read the HTTP request
        request_line = await asyncio.wait_for(reader.readline(), timeout=5.0)
        if not request_line:
            writer.close()
            return

        request_str = request_line.decode().strip()
        parts = request_str.split(" ")
        method = parts[0] if len(parts) > 0 else "GET"
        path = parts[1] if len(parts) > 1 else "/"

        # Read headers
        content_length = 0
        while True:
            header_line = await asyncio.wait_for(reader.readline(), timeout=5.0)
            if header_line == b"\r\n" or header_line == b"\n" or not header_line:
                break
            header = header_line.decode().strip()
            if header.lower().startswith("content-length:"):
                content_length = int(header.split(":")[1].strip())

        # Read body if present
        body = b""
        if content_length > 0:
            body = await asyncio.wait_for(reader.readexactly(content_length), timeout=5.0)

        # Route the request
        status = 200
        response_body = {}

        if path == "/health":
            response_body = {"status": "ok", "nodeId": node_id, "height": current_height}

        elif path == "/submit_transaction" and method == "POST":
            try:
                tx_data = json.loads(body.decode()) if body else {}
                tx_id = hashlib.sha256(
                    f"{time.time()}:{node_id}:{json.dumps(tx_data)}".encode()
                ).hexdigest()[:16]

                tx_entry = {
                    "txId": tx_id,
                    "from": tx_data.get("from_address", node_id),
                    "to": tx_data.get("to_address", ""),
                    "amount": tx_data.get("amount", 0),
                    "memo": tx_data.get("memo", ""),
                    "timestamp": int(time.time() * 1000),
                }
                mempool.append(tx_entry)

                emit_event("TX_BROADCAST", {
                    "txId": tx_id,
                    "fromNodeId": node_id,
                    "toNodeId": tx_data.get("to_address", ""),
                })

                response_body = {"txHash": tx_id, "status": "accepted"}
            except Exception as e:
                status = 400
                response_body = {"error": str(e)}

        elif path == "/get_blocks":
            since = 0
            if b"since=" in body:
                try:
                    since = int(body.decode().split("since=")[1])
                except (ValueError, IndexError):
                    pass
            blocks_since = [b for b in blockchain if b["blockNumber"] >= since]
            response_body = {"blocks": blocks_since}

        elif path == "/get_consensus_state":
            response_body = {
                "consensusType": consensus,
                "currentRound": current_height,
                "currentPhase": "idle",
                "currentLeader": node_id if consensus == "none" else None,
                "validatorCount": 1,
                "faultyNodes": 0,
            }

        elif path == "/get_height":
            response_body = {"height": current_height}

        else:
            status = 404
            response_body = {"error": f"Unknown endpoint: {path}"}

        # Send HTTP response
        response_json = json.dumps(response_body)
        http_response = (
            f"HTTP/1.1 {status} {'OK' if status == 200 else 'Error'}\r\n"
            f"Content-Type: application/json\r\n"
            f"Content-Length: {len(response_json)}\r\n"
            f"Connection: close\r\n"
            f"\r\n"
            f"{response_json}"
        )
        writer.write(http_response.encode())
        await writer.drain()
    except (asyncio.TimeoutError, ConnectionResetError, BrokenPipeError):
        pass
    except Exception as e:
        print(f"RPC error: {e}", file=sys.stderr, flush=True)
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass


async def start_rpc_server():
    """Start the HTTP RPC server on the assigned port."""
    server = await asyncio.start_server(handle_rpc_request, "127.0.0.1", port)
    addr = server.sockets[0].getsockname()
    print(f"NODE {node_id} RPC server listening on {addr[0]}:{addr[1]}", flush=True)
    print(f"READY", flush=True)  # Signal to process manager

    async with server:
        await server.serve_forever()


# ── Main ─────────────────────────────────────────────────────────────────────

async def main():
    global running

    # Handle termination signals gracefully
    loop = asyncio.get_event_loop()

    def signal_handler():
        global running
        running = False
        emit_event("NODE_OFFLINE", {"nodeId": node_id, "reason": "shutdown signal"})

    try:
        loop.add_signal_handler(signal.SIGTERM, signal_handler)
        loop.add_signal_handler(signal.SIGINT, signal_handler)
    except NotImplementedError:
        # Windows doesn't support add_signal_handler for all signals
        pass

    # Emit sync events (for "none" consensus, sync is instant)
    emit_event("SYNC_PROGRESS", {
        "nodeId": node_id,
        "currentHeight": 0,
        "targetHeight": 0,
        "syncMode": "realtime",
    })
    emit_event("SYNC_COMPLETE", {
        "nodeId": node_id,
        "finalHeight": 0,
    })

    # Start RPC server and block production concurrently
    await asyncio.gather(
        start_rpc_server(),
        block_production_loop(),
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ChainForge Node Process")
    parser.add_argument("--node-id", required=True, help="Unique node identifier")
    parser.add_argument("--role", required=True, help="Node role")
    parser.add_argument("--port", type=int, required=True, help="RPC port")
    parser.add_argument("--consensus", default="none", help="Consensus algorithm")
    parser.add_argument("--block-time-ms", type=int, default=3000, help="Block time in ms")

    args = parser.parse_args()
    node_id = args.node_id
    role = args.role
    port = args.port
    consensus = args.consensus
    block_time_ms = args.block_time_ms

    print(f"Starting ChainForge node: id={node_id}, role={role}, port={port}, "
          f"consensus={consensus}", flush=True)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"Node {node_id} shutting down.", flush=True)
