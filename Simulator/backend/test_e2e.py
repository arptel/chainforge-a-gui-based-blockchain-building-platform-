"""
E2E Test: ChainForge Simulator - None Consensus
Tests the full pipeline: load project → spawn node → submit tx → verify events

Run while the FastAPI server is running on port 8000.
"""

import asyncio
import json
import time
import os
import sys

import httpx
import websockets

API = "http://localhost:8000"
WS_URL = "ws://localhost:8000/events"

PASS = "\u2705"
FAIL = "\u274c"
results = []


def log(msg):
    print(f"  {msg}")


def check(name, condition, detail=""):
    if condition:
        results.append((name, True))
        print(f"{PASS} {name}")
    else:
        results.append((name, False))
        print(f"{FAIL} {name}: {detail}")


async def run_test():
    print("=" * 60)
    print("ChainForge Simulator E2E Test - None Consensus")
    print("=" * 60)

    # Determine config path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "..", "sample", "config_none.yaml")
    config_path = os.path.normpath(config_path)

    async with httpx.AsyncClient(timeout=15.0) as client:

        # ── Step 1: Health check ──────────────────────────────
        print("\n--- Step 1: Health Check ---")
        r = await client.get(f"{API}/health")
        check("Health endpoint responds", r.status_code == 200)
        data = r.json()
        log(f"Response: {data}")

        # ── Step 2: Load project ──────────────────────────────
        print("\n--- Step 2: Load Project ---")
        r = await client.post(
            f"{API}/load-project",
            json={"config_path": config_path}
        )
        check("Load project succeeds", r.status_code == 200, f"status={r.status_code} body={r.text}")
        if r.status_code == 200:
            data = r.json()
            check("Consensus is 'none'", data.get("consensus") == "none", f"got {data.get('consensus')}")
            check("Network type is 'permissioned'", data.get("network_type") == "permissioned")
            log(f"Config: {json.dumps(data, indent=2)}")

        # ── Step 3: Connect WebSocket ─────────────────────────
        print("\n--- Step 3: Connect WebSocket ---")
        ws_events = []
        try:
            ws = await websockets.connect(WS_URL)
            check("WebSocket connects", True)
        except Exception as e:
            check("WebSocket connects", False, str(e))
            ws = None

        # ── Step 4: Spawn a node ──────────────────────────────
        print("\n--- Step 4: Spawn Node ---")
        r = await client.post(
            f"{API}/nodes",
            json={"role": "full"}
        )
        check("POST /nodes succeeds", r.status_code == 200, f"status={r.status_code} body={r.text}")
        node_data = None
        if r.status_code == 200:
            node_data = r.json()
            check("Node has ID", "nodeId" in node_data, str(node_data))
            check("Node has PID", node_data.get("pid") is not None, str(node_data))
            check("Node has port", node_data.get("port") is not None, str(node_data))
            check("Node status is 'running'", node_data.get("status") == "running", f"got {node_data.get('status')}")
            log(f"Node: {json.dumps(node_data, indent=2)}")

        # ── Step 5: Verify NODE_JOINED over WebSocket ─────────
        print("\n--- Step 5: Verify NODE_JOINED Event ---")
        if ws:
            try:
                # Read events from WebSocket (with timeout)
                for _ in range(10):
                    msg = await asyncio.wait_for(ws.recv(), timeout=3.0)
                    event = json.loads(msg)
                    ws_events.append(event)
                    log(f"WS Event: {event['type']} | nodeId={event.get('nodeId', 'n/a')}")
                    if event["type"] == "NODE_JOINED":
                        break
            except asyncio.TimeoutError:
                log("(No more events within timeout)")

            node_joined = [e for e in ws_events if e["type"] == "NODE_JOINED"]
            check("NODE_JOINED event received", len(node_joined) > 0,
                  f"events received: {[e['type'] for e in ws_events]}")

        # ── Step 6: List nodes ────────────────────────────────
        print("\n--- Step 6: List Nodes ---")
        r = await client.get(f"{API}/nodes")
        check("GET /nodes succeeds", r.status_code == 200)
        if r.status_code == 200:
            nodes = r.json().get("nodes", [])
            check("One node exists", len(nodes) == 1, f"got {len(nodes)}")
            log(f"Nodes: {json.dumps(nodes, indent=2)}")

        # ── Step 7: Submit transaction ────────────────────────
        print("\n--- Step 7: Submit Transaction ---")
        if node_data:
            from_node = node_data["nodeId"]
            r = await client.post(
                f"{API}/transaction",
                json={
                    "fromNodeId": from_node,
                    "toNodeId": "external-addr",
                    "payload": {"amount": 100, "memo": "test tx"}
                }
            )
            check("POST /transaction succeeds", r.status_code == 200,
                  f"status={r.status_code} body={r.text}")
            if r.status_code == 200:
                tx_data = r.json()
                check("Transaction has hash", "txHash" in tx_data, str(tx_data))
                log(f"Tx: {json.dumps(tx_data, indent=2)}")

        # ── Step 8: Wait for block events ─────────────────────
        print("\n--- Step 8: Wait for Block Events ---")
        if ws:
            try:
                # Wait for TX_BROADCAST, BLOCK_PROPOSED, BLOCK_COMMITTED
                deadline = time.time() + 15  # 15 second timeout
                while time.time() < deadline:
                    try:
                        msg = await asyncio.wait_for(ws.recv(), timeout=2.0)
                        event = json.loads(msg)
                        ws_events.append(event)
                        log(f"WS Event: {event['type']} | {json.dumps(event.get('payload', {}))[:80]}")
                        if event["type"] == "BLOCK_COMMITTED":
                            break
                    except asyncio.TimeoutError:
                        continue
            except Exception as e:
                log(f"WS error: {e}")

            event_types = [e["type"] for e in ws_events]
            check("TX_BROADCAST received", "TX_BROADCAST" in event_types,
                  f"types: {event_types}")
            check("BLOCK_PROPOSED received", "BLOCK_PROPOSED" in event_types,
                  f"types: {event_types}")
            check("BLOCK_COMMITTED received", "BLOCK_COMMITTED" in event_types,
                  f"types: {event_types}")

            # Verify BLOCK_COMMITTED has real data
            committed = [e for e in ws_events if e["type"] == "BLOCK_COMMITTED"]
            if committed:
                payload = committed[0].get("payload", {})
                check("Block has hash", bool(payload.get("hash")),
                      f"payload: {payload}")
                check("Block has height", payload.get("blockHeight", 0) > 0,
                      f"height: {payload.get('blockHeight')}")

        # ── Step 9: Check metrics ─────────────────────────────
        print("\n--- Step 9: Check Metrics ---")
        r = await client.get(f"{API}/metrics")
        check("GET /metrics succeeds", r.status_code == 200)
        if r.status_code == 200:
            metrics = r.json()
            check("Metrics has totalNodes > 0", metrics.get("totalNodes", 0) > 0,
                  f"totalNodes={metrics.get('totalNodes')}")
            check("Metrics has totalBlocks", "totalBlocks" in metrics)
            check("Metrics has totalTransactions", "totalTransactions" in metrics)
            check("Metrics has averageBlockTimeMs", "averageBlockTimeMs" in metrics)
            check("Metrics has consensusLatencyMs", "consensusLatencyMs" in metrics)
            check("Metrics has faultTolerance", "faultTolerance" in metrics)
            log(f"Metrics: {json.dumps(metrics, indent=2)}")

        # ── Step 10: Export trace ─────────────────────────────
        print("\n--- Step 10: Export Trace ---")
        r = await client.get(f"{API}/export-trace")
        check("GET /export-trace succeeds", r.status_code == 200)
        if r.status_code == 200:
            trace = r.json()
            check("Trace is non-empty", len(trace) > 0, f"trace length={len(trace)}")

        # Close WebSocket
        if ws:
            await ws.close()

    # ── Summary ───────────────────────────────────────────────
    print("\n" + "=" * 60)
    passed = sum(1 for _, ok in results if ok)
    failed = sum(1 for _, ok in results if not ok)
    print(f"Results: {passed} passed, {failed} failed out of {len(results)} checks")
    if failed == 0:
        print(f"{PASS} ALL TESTS PASSED")
    else:
        print(f"\n{FAIL} Failed tests:")
        for name, ok in results:
            if not ok:
                print(f"  - {name}")
    print("=" * 60)
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_test())
    sys.exit(0 if success else 1)
