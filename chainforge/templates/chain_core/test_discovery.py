import sys
import os
import asyncio
import threading
import time
import websockets
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.chain import Blockchain
from modules.consensus.pow import PoWConsensus
from modules.vm.python_vm import PythonVM
from modules.network.p2p import P2PNetwork
from api import server
import uvicorn

# Global list to store launched servers so they keep running
api_threads = []

def start_node(p2p_port, api_port, peers_to_dial=[]):
    """Start a full node on the given local ports."""
    consensus = PoWConsensus(target_difficulty=2)
    vm = PythonVM()
    chain = Blockchain(consensus=consensus, runtime=vm, require_signature=False)
    
    # Crucial: pass BOTH ports so it knows its public API port for discovery
    network = P2PNetwork(port=p2p_port, api_port=api_port)
    network.set_chain(chain)
    
    server.set_network(network)
    
    # We can use server.run directly with captured logs
    api_thread = threading.Thread(target=server.run, args=(chain, api_port, network), daemon=True)
    api_thread.start()
    api_threads.append(api_thread)
    
    time.sleep(2) # Wait 2s for Uvicorn to bind socket
    
    for p in peers_to_dial:
        network.connect_to_peer(p)
        
    return chain, network

def test_peer_discovery():
    print("--- Testing Automated Peer Discovery ---", flush=True)
    
    print("1. Starting Node A (Bootstrap Node) on port 8001...", flush=True)
    chain_a, net_a = start_node(p2p_port=5001, api_port=8001)
    
    print("\n2. Starting Node B on port 8002 and dialing Node A...", flush=True)
    chain_b, net_b = start_node(p2p_port=5002, api_port=8002, peers_to_dial=["ws://localhost:8001/ws"])
    
    print("\n3. Starting Node C on port 8003 and dialing Node A...", flush=True)
    chain_c, net_c = start_node(p2p_port=5003, api_port=8003, peers_to_dial=["ws://localhost:8001/ws"])
    
    # Wait for gossip convergence with robust polling
    print("\nWaiting for gossip to propagate...", flush=True)
    for _ in range(10):
        time.sleep(1)
        a_peers = net_a.get_peers()
        b_peers = net_b.get_peers()
        c_peers = net_c.get_peers()
        
        # We expect everyone to know about 8001, 8002, and 8003
        if "ws://localhost:8002/ws" in a_peers and "ws://localhost:8003/ws" in a_peers and \
           "ws://localhost:8003/ws" in b_peers and "ws://localhost:8002/ws" in c_peers:
           break
           
    print("\n--- Network State ---", flush=True)
    print(f"Node A known peers: {net_a.get_peers()}", flush=True)
    print(f"Node B known peers: {net_b.get_peers()}", flush=True)
    print(f"Node C known peers: {net_c.get_peers()}", flush=True)
    
    assert "ws://localhost:8003/ws" in net_a.get_peers(), "Node A did not learn about Node C"
    assert "ws://localhost:8002/ws" in net_a.get_peers(), "Node A did not learn about Node B"
    
    assert "ws://localhost:8001/ws" in net_b.get_peers(), "Node B did not learn about Node A"
    assert "ws://localhost:8003/ws" in net_b.get_peers(), "Node B did not discover Node C via Node A!"
    
    assert "ws://localhost:8001/ws" in net_c.get_peers(), "Node C did not learn about Node A"
    assert "ws://localhost:8002/ws" in net_c.get_peers(), "Node C did not discover Node B via Node A!"
    
    print("\nAutomated Peer Discovery via Gossip Passed Successfully!", flush=True)
    sys.exit(0)

if __name__ == "__main__":
    test_peer_discovery()
