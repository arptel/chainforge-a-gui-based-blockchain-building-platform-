import sys
import os
import asyncio
import threading
import time
import websockets
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.chain import Blockchain
from core.block import Block
from modules.consensus.pow import PoWConsensus
from modules.vm.python_vm import PythonVM
from modules.network.p2p import P2PNetwork
from api import server
import uvicorn

api_threads = []

def start_node(p2p_port, api_port, peers_to_dial=[]):
    """Start a full node on the given local ports."""
    consensus = PoWConsensus(target_difficulty=2)
    vm = PythonVM()
    chain = Blockchain(consensus=consensus, runtime=vm, require_signature=False)
    
    network = P2PNetwork(port=p2p_port, api_port=api_port)
    network.set_chain(chain)
    
    api_thread = threading.Thread(target=server.run, args=(chain, api_port, network), daemon=True)
    api_thread.start()
    api_threads.append(api_thread)
    
    time.sleep(2) # Wait for bind
    
    for p in peers_to_dial:
        network.connect_to_peer(p)
        
    return chain, network

async def send_sync_request_and_receive(target_url: str, last_index: int):
    """
    Directly connect to a peer via WebSocket, send a SYNC_REQUEST, 
    and wait for a SYNC_RESPONSE. Returns the blocks received.
    """
    sync_req = json.dumps({"type": "SYNC_REQUEST", "data": {"last_index": last_index}})
    async with websockets.connect(target_url) as ws:
        print(f"[Test] Connected to {target_url}, sending SYNC_REQUEST(last_index={last_index})", flush=True)
        await ws.send(sync_req)
        # Wait for the response
        for _ in range(10):
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=3.0)
                msg = json.loads(response)
                print(f"[Test] Received message type: {msg.get('type')}", flush=True)
                if msg.get("type") == "SYNC_RESPONSE":
                    return msg.get("data", [])
            except asyncio.TimeoutError:
                print("[Test] Timeout waiting for SYNC_RESPONSE", flush=True)
                break
    return []

def test_sync():
    print("--- Testing WebSocket Historical Block Synchronization ---", flush=True)
    
    # Node A is our main seed node
    print("1. Starting Node A on port 8001...", flush=True)
    chain_a, net_a = start_node(p2p_port=5001, api_port=8001)
    
    # Node A mines some blocks while completely alone
    print("Node A mining 3 blocks while offline...", flush=True)
    for i in range(3):
        tx = {"from": f"user_x", "to": "user_y", "amount": 10 * i, "type": "transfer"}
        chain_a.add_transaction(tx)
        chain_a.mine_pending_transactions("miner_a")
        
    print(f"Node A isolated chain length is now: {len(chain_a.chain)}", flush=True)
    print(f"Node A genesis hash: {chain_a.chain[0].hash}", flush=True)
    
    # Bring Node B online, starting at Genesis
    print("\n2. Starting Node B on port 8002...", flush=True)
    chain_b, net_b = start_node(p2p_port=5002, api_port=8002)
    print(f"Node B genesis hash: {chain_b.chain[0].hash}", flush=True)

    print(f"Node B initial chain length: {len(chain_b.chain)} (Genesis only)", flush=True)
    
    # Confirm genesis hashes match
    assert chain_a.chain[0].hash == chain_b.chain[0].hash, \
        f"Genesis hash mismatch! A={chain_a.chain[0].hash} B={chain_b.chain[0].hash}"
    print("[PASS] Genesis hashes match!", flush=True)
    
    # Now send SYNC_REQUEST directly to Node A and receive historical blocks
    print("\n3. Sending direct SYNC_REQUEST to Node A (port 8001)...", flush=True)
    blocks_data = asyncio.run(send_sync_request_and_receive("ws://localhost:8001/ws", last_index=0))
    
    print(f"Received {len(blocks_data)} blocks from Node A.", flush=True)
    if len(blocks_data) == 0:
        print("ERROR: Received 0 blocks. SYNC_REQUEST may not have been handled by Node A!", flush=True)
    assert len(blocks_data) == 3, f"Expected 3 historical blocks, got {len(blocks_data)}"
    
    # Now reconstruct blocks and feed them to Node B
    print("Applying received blocks to Node B...", flush=True)
    new_chain = []
    print(f"Node B current chain length before merge: {len(chain_b.chain)}", flush=True)
    print(f"Node B genesis hash: {chain_b.chain[0].hash}", flush=True)
    for b_data in blocks_data:
        print(f"  Incoming block #{b_data['index']}: prev_hash={b_data['previous_hash'][:12]}... hash={b_data['hash'][:12]}...", flush=True)
        # Verify hash inline before reconstruction
        import hashlib as _hl, json as _json
        data_copy = {k:v for k,v in b_data.items() if k != 'hash'}
        recomp = _hl.sha256(_json.dumps(data_copy, sort_keys=True).encode()).hexdigest()
        print(f"    stored={b_data['hash'][:12]} recomputed={recomp[:12]} match={b_data['hash']==recomp}", flush=True)
        block = Block.from_dict(b_data)
        block._is_local_mine = False
        new_chain.append(block)

    print(f"Calling append_chain_suffix with {len(new_chain)} blocks starting at index {new_chain[0].index}", flush=True)
    # Explicitly check is_valid_chain first to see the diagnostic message
    added = chain_b.append_chain_suffix(new_chain)
    print(f"append_chain_suffix added: {added} blocks", flush=True)
    print(f"Node B chain length after: {len(chain_b.chain)}", flush=True)
    
    print(f"\nNode A Final Chain Length: {len(chain_a.chain)}", flush=True)
    print(f"Node B Final Chain Length: {len(chain_b.chain)}", flush=True)
    
    assert len(chain_b.chain) == 4, f"Node B did not sync history! Length is {len(chain_b.chain)}, expected 4."
    assert chain_b.last_block.hash == chain_a.last_block.hash, "Node B has a different ledger hash than Node A after syncing!"
    
    print("\n[PASS] PHASE 1 PASSED: Historical block download and sync successful!", flush=True)
    
    # -----------------------------------------------------------------------
    # PHASE 2: Gap Detection and Repair
    # -----------------------------------------------------------------------
    print("\n--- Phase 2: Gap Detection ---", flush=True)
    
    # Node A mines 2 more blocks (Block 4 and 5) while Node B is "offline"
    print("Node A mining Block 4 and 5 while Node B is lagging...", flush=True)
    for label in ["B4", "B5"]:
        tx = {"from": "test", "to": "test", "amount": 0, "type": "transfer"}
        chain_a.add_transaction(tx)
        chain_a.mine_pending_transactions("miner_a")
    
    print(f"Node A is now at length {len(chain_a.chain)}, Node B is at {len(chain_b.chain)}", flush=True)
    
    # Simulate gap detection: Node B sends SYNC_REQUEST from its current tip
    print("\n4. Node B sending gap-fill SYNC_REQUEST to Node A...", flush=True)
    current_b_index = chain_b.last_block.index
    gap_blocks_data = asyncio.run(send_sync_request_and_receive("ws://localhost:8001/ws", last_index=current_b_index))
    
    print(f"Node B received {len(gap_blocks_data)} gap blocks from Node A.", flush=True)
    assert len(gap_blocks_data) == 2, f"Expected 2 gap blocks (B4, B5), got {len(gap_blocks_data)}"
    
    # Apply gap blocks using append_chain_suffix
    gap_chain = []
    for b_data in gap_blocks_data:
        block = Block.from_dict(b_data)
        block._is_local_mine = False
        gap_chain.append(block)
    
    added = chain_b.append_chain_suffix(gap_chain)
    print(f"Gap repair: applied {added} blocks.", flush=True)
    
    print(f"\nNode A Final Mined Length: {len(chain_a.chain)}", flush=True)
    print(f"Node B Final Gap-Repaired Length: {len(chain_b.chain)}", flush=True)
    
    assert len(chain_b.chain) == len(chain_a.chain), "Node B did not repair its missing gap!"
    assert chain_b.last_block.hash == chain_a.last_block.hash, "Node B ledger is divergent after gap repair!"

    print("\n[PASS] PHASE 2 PASSED: Gap detection and repair successful!", flush=True)

    # -----------------------------------------------------------------------
    # PHASE 3: Fork Resolution and Tamper Recovery
    # -----------------------------------------------------------------------
    print("\n--- Phase 3: Fork Resolution & Tampering Recovery ---", flush=True)

    # Set up the SyncModule inside Node B so it can handle the resolution
    from modules.sync.full import FullSync
    sync_b = FullSync(chain_b, net_b)
    net_b.set_sync_module(sync_b)

    # Node B tampered with Block 4 (index 4 is at index 4 in zero-based list)
    print("Simulating local attacker tampering with Node B's Block 4...", flush=True)
    chain_b.chain[4].transactions = [{"from": "hacker", "to": "attacker", "amount": 99999}]
    chain_b.chain[4].hash = "fake_tampered_hash_0000"
    
    # Node A naturally mines Block 6
    print("Node A mining Block 6...", flush=True)
    tx = {"from": "user_a", "to": "user_b", "amount": 5, "type": "transfer"}
    chain_a.add_transaction(tx)
    chain_a.mine_pending_transactions("miner_a")
    b6 = chain_a.last_block
    
    # Node A tries to gossip Block 6 to Node B
    print("Node A gossips Block 6. Node B detects gap and potential mismatch...", flush=True)
    
    # Node B gap detection
    gap_request_str = sync_b.handle_gap(b6.index)
    gap_msg = json.loads(gap_request_str)
    
    # Simulate P2P requesting blocks from Node A
    requested_last_index = gap_msg["data"]["last_index"]
    print(f"Node B requested blocks after index {requested_last_index}", flush=True)
    
    recovery_blocks_data = asyncio.run(send_sync_request_and_receive("ws://localhost:8001/ws", last_index=requested_last_index))
    print(f"Node B received {len(recovery_blocks_data)} blocks for recovery.", flush=True)
    
    # Handle the response in Node B (This should fallback to older chunks because Block 4 is tampered)
    fallback_request_str = sync_b.handle_sync_response(recovery_blocks_data)
    
    if fallback_request_str:
        fallback_msg = json.loads(fallback_request_str)
        fallback_last_index = fallback_msg["data"]["last_index"]
        print(f"Node B fell back and requested blocks after index {fallback_last_index}...", flush=True)
        
        final_recovery_blocks = asyncio.run(send_sync_request_and_receive("ws://localhost:8001/ws", last_index=fallback_last_index))
        # This second attempt should include the common ancestor and trigger replace_chain
        sync_b.handle_sync_response(final_recovery_blocks)
    
    print(f"\nNode A Final Mined Length: {len(chain_a.chain)}", flush=True)
    print(f"Node B Final Gap-Repaired Length: {len(chain_b.chain)}", flush=True)
    print(f"Node A Block 4 Hash: {chain_a.chain[4].hash[:10]}...")
    print(f"Node B Block 4 Hash: {chain_b.chain[4].hash[:10]}...")
    
    assert len(chain_b.chain) == len(chain_a.chain), "Node B did not repair its missing gap!"
    assert chain_b.last_block.hash == chain_a.last_block.hash, "Node B ledger is divergent after gap repair!"
    assert chain_b.chain[4].hash == chain_a.chain[4].hash, "Node B failed to overwrite the tampered block!"

    print("\n[PASS] PHASE 3 PASSED: Fork resolution and tamper recovery successful!", flush=True)


    print("\n=== WebSocket Sync Test PASSED Successfully! ===", flush=True)
    sys.exit(0)

if __name__ == "__main__":
    test_sync()
