"""
Debug script: Test receiving blocks from a live Node A and checking
if the Block objects reconstructed in test_sync.py have correct compute_hash.
"""
import sys, os, asyncio, threading, time, json, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.chain import Blockchain
from core.block import Block
from modules.consensus.pow import PoWConsensus
from modules.vm.python_vm import PythonVM
from modules.network.p2p import P2PNetwork
from api import server
import websockets

def start_node_a():
    consensus = PoWConsensus(target_difficulty=2)
    vm = PythonVM()
    chain = Blockchain(consensus=consensus, runtime=vm, require_signature=False)
    network = P2PNetwork(port=5001, api_port=8001)
    network.set_chain(chain)
    
    api_thread = threading.Thread(target=server.run, args=(chain, 8001, network), daemon=True)
    api_thread.start()
    time.sleep(2)
    
    # Mine 3 blocks
    for i in range(3):
        chain.add_transaction({'from': 'x', 'to': 'y', 'amount': i, 'type': 'transfer'})
        b = chain.consensus.propose_block(chain.pending_transactions, chain.last_block.hash, len(chain.chain), 'miner')
        chain.add_block(b)
    
    print(f"Node A chain length: {len(chain.chain)}", flush=True)
    print(f"Node A Block 1 hash: {chain.chain[1].hash[:16]}", flush=True)
    return chain, network

async def get_blocks():
    sync_req = json.dumps({"type": "SYNC_REQUEST", "data": {"last_index": 0}})
    async with websockets.connect("ws://localhost:8001/ws") as ws:
        await ws.send(sync_req)
        for _ in range(10):
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=5.0)
                msg = json.loads(response)
                if msg.get("type") == "SYNC_RESPONSE":
                    return msg.get("data", [])
            except asyncio.TimeoutError:
                break
    return []

chain_a, net_a = start_node_a()
blocks_data = asyncio.run(get_blocks())

print(f"\nReceived {len(blocks_data)} blocks", flush=True)
for b_data in blocks_data:
    # Check hash of received data
    data_minus_hash = {k:v for k,v in b_data.items() if k != 'hash'}
    recomp = hashlib.sha256(json.dumps(data_minus_hash, sort_keys=True).encode()).hexdigest()
    print(f"Block {b_data['index']}: stored={b_data['hash'][:12]} direct_recomp={recomp[:12]} match={b_data['hash']==recomp}", flush=True)

    # Now reconstruct Block object
    rec = Block(index=b_data['index'], transactions=b_data['transactions'], timestamp=b_data['timestamp'], previous_hash=b_data['previous_hash'], validator=b_data.get('validator'))
    rec.nonce = b_data.get('nonce', 0)
    rec.hash = b_data.get('hash')
    
    rec_recomp = rec.compute_hash()
    print(f"  After reconstruction: rec.hash={rec.hash[:12]} rec.compute_hash={rec_recomp[:12]} match={rec.hash==rec_recomp}", flush=True)
    if rec.hash != rec_recomp:
        rec_d = {k:v for k,v in rec.__dict__.items() if k != 'hash'}
        print(f"  rec.__dict__ (no hash): {json.dumps(rec_d, sort_keys=True)[:200]}", flush=True)
        print(f"  b_data (no hash):       {json.dumps(data_minus_hash, sort_keys=True)[:200]}", flush=True)
        print(f"  Same JSON? {json.dumps(rec_d, sort_keys=True) == json.dumps(data_minus_hash, sort_keys=True)}", flush=True)
