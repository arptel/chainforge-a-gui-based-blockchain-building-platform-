"""
ChainForge Node Process — Universal Bridge Script

This script is spawned by the ProcessManager as an OS subprocess.
It automatically detects if real platform-generated blockchain code
exists in the `chain_node/` subdirectory and uses it. Otherwise,
it falls back to a built-in simulation mode.

Protocol:
  1. Prints "READY" on stdout when the node is operational
  2. Emits EVENT:{json} lines on stdout for the dashboard
  3. Listens on an HTTP port for RPC commands from the adapter

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
import os
import signal
from typing import List, Dict, Any, Optional


# ── Globals ──────────────────────────────────────────────────────────────────

node_id: str = ""
role: str = ""
port: int = 0
consensus: str = "none"
block_time_ms: int = 3000
running: bool = True

# Real chain integration
real_chain = None
using_real_chain: bool = False

# Simulation mode state (fallback)
blockchain: List[Dict[str, Any]] = []
mempool: List[Dict[str, Any]] = []
current_height: int = 0
sim_state: Dict[str, float] = {}  # address -> balance


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


# ══════════════════════════════════════════════════════════════════════════════
# REAL CHAIN MODE — Uses the platform-generated code from chain_node/
# ══════════════════════════════════════════════════════════════════════════════

def try_init_real_chain() -> bool:
    """
    Attempt to import and initialize the real platform blockchain from
    the chain_node/ directory. Returns True if successful.
    
    This works for ANY zip downloaded from the platform because:
    - The DependencyInjector auto-detects available consensus/sync/VM modules
    - The genesis.json stores the full config from the platform UI
    - Smart contracts are embedded in genesis.json and auto-deployed by the VM
    """
    global real_chain, using_real_chain

    script_dir = os.path.dirname(os.path.abspath(__file__))
    chain_node_dir = os.path.join(script_dir, "chain_node")

    if not os.path.isdir(chain_node_dir):
        return False

    # Check for the platform's signature files
    if not os.path.isfile(os.path.join(chain_node_dir, "di.py")):
        return False

    try:
        # Add chain_node to the import path so platform code resolves correctly
        sys.path.insert(0, chain_node_dir)

        from di import DependencyInjector
        from core.chain import Blockchain

        # ── Build config from genesis.json ──
        config = {
            "consensus": consensus,
            "port": port + 1000,   # P2P port (not used in simulator, but DI needs it)
            "api_port": port,
        }

        genesis_path = os.path.join(chain_node_dir, "config", "genesis.json")
        if os.path.exists(genesis_path):
            with open(genesis_path, "r") as f:
                genesis = json.load(f)

            # Map the platform's frontend config to the DI config
            # (same logic as the platform's own main.py)
            net_type = genesis.get("networkType")
            if net_type == "public":
                config["consensus"] = genesis.get("publicConsensus", "pow")
                config["syncMode"] = genesis.get("publicSyncMode", "full")
                config["runtime"] = genesis.get("publicRuntime", "evm")
            elif net_type == "permissioned":
                p_type = genesis.get("permissionedType", "centralized")
                if p_type == "centralized":
                    config["consensus"] = genesis.get("centralizedConsensus", "raft")
                    config["syncMode"] = genesis.get("centralizedSync", "realtime")
                    config["runtime"] = "evm"
                else:  # consortium
                    config["consensus"] = genesis.get("consortiumConsensus", "pbft")
                    config["syncMode"] = genesis.get("consortiumSync", "full")
                    config["runtime"] = "evm"

            # Direct consensus override (legacy / explicit)
            if "consensus" in genesis:
                config["consensus"] = genesis["consensus"]

            # Gas config
            enable_gas = genesis.get("enableGas", True)
            config["min_gas_price"] = genesis.get("minGasPrice", 0) if enable_gas else 0
            config["default_gas_limit"] = genesis.get("defaultGasLimit", 100000)

        # ── Initialize the DI container ──
        di = DependencyInjector(config)

        # ── Robust consensus initialization ──
        # The DI's get_consensus() can fail if:
        #   1. The consensus class needs constructor args (node_id, peers)
        #   2. The consensus class has unimplemented abstract methods
        # We handle both cases gracefully without modifying platform code.
        consensus_module = None
        try:
            consensus_module = di.get_consensus()
        except TypeError:
            # Constructor needs args or has missing abstract methods
            algo = config.get("consensus", "none")
            cls = di._consensus_map.get(algo)
            if cls is not None:
                # Patch any missing abstract methods with no-ops
                import inspect
                for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
                    pass  # just inspecting
                # Check if there are unimplemented abstract methods
                if hasattr(cls, '__abstractmethods__') and cls.__abstractmethods__:
                    for method_name in list(cls.__abstractmethods__):
                        if not hasattr(cls, method_name) or getattr(cls, method_name) is None:
                            pass
                    # Create a concrete subclass that fills in missing methods
                    missing = cls.__abstractmethods__
                    patches = {}
                    for m in missing:
                        if m == "commit_block":
                            patches[m] = lambda self, block: True
                        else:
                            patches[m] = lambda self, *args, **kwargs: None
                    ConcreteClass = type(f"Bridge{cls.__name__}", (cls,), patches)
                else:
                    ConcreteClass = cls

                # Try different constructor signatures
                try:
                    consensus_module = ConcreteClass(node_id=node_id, peers=[])
                except TypeError:
                    try:
                        consensus_module = ConcreteClass()
                    except TypeError:
                        consensus_module = None

        if consensus_module is None:
            print(f"Warning: Could not initialize consensus, using no-op", flush=True)

        runtime = di.get_runtime()

        if hasattr(runtime, 'default_gas_limit'):
            runtime.default_gas_limit = config.get("default_gas_limit", 100000)

        # Deploy smart contracts from genesis if the runtime supports it
        if os.path.exists(genesis_path):
            with open(genesis_path, "r") as f:
                genesis = json.load(f)
            contracts = genesis.get("smartContracts", [])
            if contracts and hasattr(runtime, 'contracts'):
                for sc in contracts:
                    try:
                        code = sc.get("code", "")
                        contract_id = sc.get("id", "")
                        contract_name = sc.get("name", "")
                        if code and contract_id:
                            # Execute the class definition to create the class
                            sandbox = {"__builtins__": __builtins__}
                            exec(code, sandbox)
                            # Find the class object in sandbox
                            cls_obj = None
                            for v in sandbox.values():
                                if isinstance(v, type) and v.__name__ == contract_name:
                                    cls_obj = v
                                    break
                            if cls_obj:
                                runtime.contracts[contract_id] = cls_obj()
                                print(f"Deployed contract: {contract_name} (id={contract_id})", flush=True)
                    except Exception as e:
                        print(f"Warning: Could not deploy contract {sc.get('name')}: {e}",
                              file=sys.stderr, flush=True)

        chain = Blockchain(
            consensus=consensus_module,
            runtime=runtime,
            role=role,
            require_signature=False,  # Simulator sends unsigned test transactions
            min_gas_price=0,
            db_path=None,             # In-memory for simulator (no persistence needed)
        )

        # ── Monkey-patch add_block to emit dashboard events ──
        original_add_block = chain.add_block

        def patched_add_block(block):
            emit_event("BLOCK_PROPOSED", {
                "blockHeight": block.index,
                "proposerNodeId": node_id,
                "txCount": len(block.transactions),
            })
            result = original_add_block(block)
            if result:
                commit_time = 0
                if block.timestamp > 1000:
                    commit_time = int((time.time() - block.timestamp) * 1000)
                emit_event("BLOCK_COMMITTED", {
                    "blockHeight": block.index,
                    "hash": block.hash,
                    "proposerNodeId": node_id,
                    "txCount": len(block.transactions),
                    "commitTime": commit_time,
                })
            return result

        chain.add_block = patched_add_block

        # ── Monkey-patch add_transaction to emit dashboard events ──
        original_add_tx = chain.add_transaction

        def patched_add_transaction(tx):
            result = original_add_tx(tx)
            if result:
                tx_id = hashlib.sha256(
                    json.dumps(tx, sort_keys=True, default=str).encode()
                ).hexdigest()[:16]
                emit_event("TX_BROADCAST", {
                    "txId": tx_id,
                    "fromNodeId": node_id,
                    "toNodeId": tx.get("to", ""),
                })
            return result

        chain.add_transaction = patched_add_transaction

        # ── Monkey-patch add_block to include state/balances in events ──
        original_add_block = chain.add_block
        def patched_add_block(block):
            result = original_add_block(block)
            # Emit event with current balances
            emit_event("BLOCK_COMMITTED", {
                "blockHeight": block.block_number,
                "hash": block.block_hash,
                "proposerNodeId": block.proposer,
                "txCount": len(block.transactions),
                "commitTime": 50, # Mock commit time for dashboard
                "balances": chain.state
            })
            return result
        chain.add_block = patched_add_block

        real_chain = chain
        using_real_chain = True

        actual_consensus = config.get("consensus", "unknown")
        print(f"REAL CHAIN MODE: Loaded platform blockchain "
              f"(consensus={actual_consensus}, role={role})", flush=True)
        return True

    except Exception as e:
        import traceback
        print(f"Failed to load real chain, falling back to simulation: {e}",
              file=sys.stderr, flush=True)
        traceback.print_exc(file=sys.stderr)
        return False


# ══════════════════════════════════════════════════════════════════════════════
# SIMULATION MODE — Built-in fallback when no platform code is present
# ══════════════════════════════════════════════════════════════════════════════

def compute_block_hash(block_number: int, prev_hash: str, tx_count: int, ts: int) -> str:
    """Compute a deterministic block hash."""
    data = f"{block_number}:{prev_hash}:{tx_count}:{ts}:{node_id}"
    return hashlib.sha256(data.encode()).hexdigest()


async def sim_produce_block():
    """Produce a new block from the mempool (simulation mode)."""
    global current_height
    
    # Initialize this node's balance if not present
    if node_id not in sim_state:
        sim_state[node_id] = 100.0

    prev_hash = blockchain[-1]["blockHash"] if blockchain else "0" * 64
    current_height += 1
    ts = int(time.time() * 1000)

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

    emit_event("BLOCK_PROPOSED", {
        "blockHeight": current_height,
        "proposerNodeId": node_id,
        "txCount": len(txs),
    })

    # Apply transactions to sim_state
    for tx in txs:
        sender = tx.get("from")
        receiver = tx.get("to")
        amount = float(tx.get("amount", 0))
        
        # Ensure sender has balance (init to 100 if unknown)
        if sender not in sim_state: sim_state[sender] = 100.0
        if receiver not in sim_state: sim_state[receiver] = 100.0
        
        if sim_state[sender] >= amount:
            sim_state[sender] -= amount
            sim_state[receiver] += amount

    await asyncio.sleep(0.05)
    emit_event("BLOCK_COMMITTED", {
        "blockHeight": current_height,
        "hash": block_hash,
        "proposerNodeId": node_id,
        "txCount": len(txs),
        "commitTime": int(time.time() * 1000) - ts,
        "balances": sim_state
    })


# ══════════════════════════════════════════════════════════════════════════════
# UNIFIED BLOCK PRODUCTION LOOP
# ══════════════════════════════════════════════════════════════════════════════

async def block_production_loop():
    """Main loop: produce blocks at block_time_ms intervals when mempool has txs."""
    interval = block_time_ms / 1000.0

    while running:
        if using_real_chain:
            # Real chain: use the platform's mine_pending_transactions
            if real_chain.pending_transactions:
                try:
                    real_chain.mine_pending_transactions(f"miner_{node_id}")
                except Exception as e:
                    print(f"Mining error: {e}", file=sys.stderr, flush=True)
        else:
            # Simulation mode
            if len(mempool) > 0:
                await sim_produce_block()

        await asyncio.sleep(interval)


# ══════════════════════════════════════════════════════════════════════════════
# UNIFIED HTTP RPC SERVER
# ══════════════════════════════════════════════════════════════════════════════

async def handle_rpc_request(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    """Handle a single HTTP RPC request."""
    try:
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

        # ── Route the request ──
        status = 200
        response_body = {}

        if path == "/health":
            if using_real_chain:
                response_body = {
                    "status": "ok",
                    "nodeId": node_id,
                    "height": len(real_chain.chain) - 1,
                    "mode": "real",
                }
            else:
                response_body = {
                    "status": "ok",
                    "nodeId": node_id,
                    "height": current_height,
                    "mode": "simulation",
                }

        elif path == "/submit_transaction" and method == "POST":
            try:
                tx_data = json.loads(body.decode()) if body else {}

                if using_real_chain:
                    # Translate adapter format → platform chain format
                    tx_entry = {
                        "from": tx_data.get("from_address", node_id),
                        "to": tx_data.get("to_address", ""),
                        "amount": tx_data.get("amount", 0),
                        "type": tx_data.get("type", "transfer"),
                        "memo": tx_data.get("memo", ""),
                    }
                    ok = real_chain.add_transaction(tx_entry)
                    if ok:
                        tx_id = hashlib.sha256(
                            json.dumps(tx_entry, sort_keys=True).encode()
                        ).hexdigest()[:16]
                        response_body = {"txHash": tx_id, "status": "accepted"}
                    else:
                        status = 400
                        response_body = {"error": "Transaction rejected by chain"}
                else:
                    # Simulation mode
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
            if using_real_chain:
                response_body = {
                    "blocks": [b.to_dict() for b in real_chain.chain]
                }
            else:
                response_body = {"blocks": blockchain}

        elif path == "/get_consensus_state":
            if using_real_chain:
                response_body = {
                    "consensusType": consensus,
                    "currentRound": len(real_chain.chain) - 1,
                    "currentPhase": "idle",
                    "currentLeader": node_id,
                    "validatorCount": 1,
                    "faultyNodes": 0,
                }
            else:
                response_body = {
                    "consensusType": consensus,
                    "currentRound": current_height,
                    "currentPhase": "idle",
                    "currentLeader": node_id,
                    "validatorCount": 1,
                    "faultyNodes": 0,
                }

        elif path == "/get_height":
            if using_real_chain:
                response_body = {"height": len(real_chain.chain) - 1}
            else:
                response_body = {"height": current_height}

        else:
            status = 404
            response_body = {"error": f"Unknown endpoint: {path}"}

        # Send HTTP response
        response_json = json.dumps(response_body, default=str)
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

    loop = asyncio.get_event_loop()

    def signal_handler():
        global running
        running = False
        emit_event("NODE_OFFLINE", {"nodeId": node_id, "reason": "shutdown signal"})

    try:
        loop.add_signal_handler(signal.SIGTERM, signal_handler)
        loop.add_signal_handler(signal.SIGINT, signal_handler)
    except NotImplementedError:
        pass  # Windows doesn't support add_signal_handler for all signals

    # Emit sync events
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

    # ── Try to load real platform chain ──
    loaded = try_init_real_chain()
    mode = "REAL CHAIN" if loaded else "SIMULATION"

    print(f"Starting ChainForge node: id={node_id}, role={role}, port={port}, "
          f"consensus={consensus}, mode={mode}", flush=True)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"Node {node_id} shutting down.", flush=True)
