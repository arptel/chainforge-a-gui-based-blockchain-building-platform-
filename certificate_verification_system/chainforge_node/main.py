import sys
import os
# Ensure the root of the project is in sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import argparse
import time
import threading
from core.chain import Blockchain
from core.block import Block

from api import server

def main():
    parser = argparse.ArgumentParser(description="ChainForge Generated Blockchain")
    parser.add_argument("--port", type=int, default=5000, help="P2P Port")
    parser.add_argument("--api-port", type=int, default=8000, help="API Port")
    parser.add_argument("--peers", type=str, default="", help="Comma separated list of peers")
    parser.add_argument("--role", type=str, default="full", choices=["full", "light", "miner"], help="Node role in the network")
    parser.add_argument("--db-path", type=str, default=None, help="Path to SQLite database for persisting blocks and state")
    args = parser.parse_args()

    # Automatically persist data to uniquely named files by port if not explicitly given
    if args.db_path is None:
        args.db_path = f"../data/node_{args.api_port}.sqlite"

    print(f"Starting Blockchain Node on port {args.port}... Using DB: {args.db_path}")
    
    # Load Config
    config = {
        "consensus": "pow", 
        "port": args.port,
        "api_port": args.api_port
    }
    
    import os
    import json
    
    require_sig = True  # Default to secure
    config_path = os.path.join(os.path.dirname(__file__), "config", "genesis.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                file_config = json.load(f)
                
                # Parse security flag
                require_sig = file_config.get("requireSignature", True)
                
                # Map frontend config to backend DI config
                if "networkType" in file_config:
                     if file_config["networkType"] == "public":
                         config["consensus"] = file_config.get("publicConsensus", "pow")
                         config["syncMode"] = file_config.get("publicSyncMode", "full")
                         config["runtime"] = file_config.get("publicRuntime", "evm")
                     elif file_config["networkType"] == "permissioned":
                         p_type = file_config.get("permissionedType", "centralized")
                         if p_type == "centralized":
                             config["consensus"] = file_config.get("centralizedConsensus", "raft")
                             config["syncMode"] = file_config.get("centralizedSync", "realtime")
                             # Centralized might not have runtime option explicitly, default to EVM or None
                             config["runtime"] = "evm" 
                         else:
                             config["consensus"] = file_config.get("consortiumConsensus", "pbft")
                             config["syncMode"] = file_config.get("consortiumSync", "full")
                             config["runtime"] = "evm"
                
                # Fallback if specific key missing but generic one exists (legacy)
                if "consensus" in file_config:
                    config["consensus"] = file_config["consensus"]
                    
                # Gas Config
                enable_gas = file_config.get("enableGas", True)
                config["min_gas_price"] = file_config.get("minGasPrice", 0) if enable_gas else 0
                config["default_gas_limit"] = file_config.get("defaultGasLimit", 100000)

                display_config = f"Mode={file_config.get('networkType')}, Consensus={config['consensus']}, Sync={config.get('syncMode')}, Runtime={config.get('runtime')}, Secure={require_sig}, Gas={enable_gas}"
                print(f"Loaded config: {display_config}")
        except Exception as e:
            print(f"Error loading genesis.json: {e}")

    # Initialize Components via DI
    from di import DependencyInjector
    di = DependencyInjector(config)
    
    # 1. Core independent modules
    consensus = di.get_consensus()
    runtime = di.get_runtime()
    network = di.get_network()

    # Pass the default gas limit to the VM globally if it supports it
    if hasattr(runtime, 'default_gas_limit'):
        runtime.default_gas_limit = config.get("default_gas_limit", 100000)

    # 2. Blockchain (depends on Consensus, Runtime)
    chain = Blockchain(
        consensus=consensus, 
        runtime=runtime, 
        role=args.role, 
        require_signature=require_sig,
        min_gas_price=config.get("min_gas_price", 0),
        db_path=args.db_path,
        api_port=args.api_port
    )

    # 2b. Give the network a reference to the chain so it can process incoming P2P messages
    network.set_chain(chain)

    # 3. Sync (depends on Chain, Network)
    sync = di.get_sync(chain, network)

    # 5. Bind Consensus back to Network so it can route protocol messages
    if hasattr(network, 'set_consensus_module'):
        network.set_consensus_module(consensus)

    # 4. Bind Sync back to Network so Network knows how to resolve forks/gaps
    if hasattr(network, 'set_sync_module'):
        network.set_sync_module(sync)

    # Initialize peers from args
    if args.peers:
        for peer in args.peers.split(','):
            peer = peer.strip()
            if peer:
                network.connect_to_peer(peer)

    # Allow server to use network for broadcasting
    server.set_network(network)

    # Start API Server
    api_thread = threading.Thread(target=server.run, args=(chain, args.api_port))
    api_thread.daemon = True
    api_thread.start()

    # Start Network
    import asyncio
    def run_network():
        asyncio.run(network.start_server())
        
    network_thread = threading.Thread(target=run_network)
    network_thread.daemon = True
    network_thread.start()
    
    # Load persistence from disk before starting active mining loops
    if args.db_path:
        chain.load_from_disk()
    
    # Simple mining loop for demo (Only full nodes and dedicated miners should mine)
    if args.role in ['full', 'miner']:
        while True:
            time.sleep(5)
            if chain.pending_transactions:
                print(f"[{args.role.upper()} NODE] Mining pending transactions...")
                if chain.mine_pending_transactions(f"miner_{args.port}"):
                    # Broadcast the newly mined block!
                    network.broadcast_block(chain.last_block)
    else:
        print(f"[{args.role.upper()} NODE] Running in passive mode (no mining).")
        while True:
            time.sleep(10)
        
if __name__ == "__main__":
    main()
