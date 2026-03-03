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

def start_node(port):
    consensus = PoWConsensus(target_difficulty=2)
    vm = PythonVM()
    chain = Blockchain(consensus=consensus, runtime=vm, require_signature=False)
    network = P2PNetwork(port)
    network.set_chain(chain)
    server.set_network(network)
    
    api_thread = threading.Thread(target=server.run, args=(chain, port), daemon=True)
    api_thread.start()
    time.sleep(2)
    return chain, network

async def _test_p2p_websockets():
    print("--- Testing WebSocket P2P Networking ---")
    
    # 1. Start a Single Full Node A
    print("Starting Node A on port 8001...")
    chain_a, net_a = start_node(8001)
    
    print("\nSimulating Node B dialing Node A directly using websockets client...")
    
    # 2. Node B (client simulated) dials Node A
    try:
        async with websockets.connect("ws://localhost:8001/ws") as ws:
            print("[Mock Client] Connecting as Node B...")
            
            # 3. Node A mines a block
            print("\nNode A mining a block...")
            tx = {"from": "user_a", "to": "user_b", "amount": 100, "type": "transfer"}
            chain_a.add_transaction(tx)
            block1_a = chain_a.consensus.propose_block([tx], chain_a.last_block.hash, len(chain_a.chain), "miner_a")
            chain_a.add_block(block1_a)
            
            # Broadcast it from Node A!
            print("Node A broadcasting block over WebSockets...")
            net_a.broadcast_block(chain_a.last_block)
            
            # 4. Node B awaits receipt of broadcast
            print("[Mock Client] Waiting for gossip payload...")
            response = await asyncio.wait_for(ws.recv(), timeout=2.0)
            
            data = json.loads(response)
            assert data.get("type") == "NEW_BLOCK", "Did not receive NEW_BLOCK type"
            assert data["data"]["hash"] == chain_a.last_block.hash, "Hash mismatch in gossiped block"
            
            print("\nWebSocket P2P Tests Passed Successfully! Broadcast received.")
    except Exception as e:
        print(f"\nWebSocket test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(_test_p2p_websockets())
