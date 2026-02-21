import argparse
import time
import threading
from core.chain import Blockchain
from core.block import Block
from modules.consensus.pow import PoWConsensus
from modules.network.p2p import P2PNetwork
from modules.sync.full import FullSync
from api import server

def main():
    parser = argparse.ArgumentParser(description="ChainForge Generated Blockchain")
    parser.add_argument("--port", type=int, default=5000, help="P2P Port")
    parser.add_argument("--api-port", type=int, default=8000, help="API Port")
    parser.add_argument("--peers", type=str, default="", help="Comma separated list of peers")
    args = parser.parse_args()

    print(f"Starting Blockchain Node on port {args.port}...")
    
    # Load Config
    config = {
        "consensus": "pow", 
        "port": args.port
    }
    
    import os
    import json
    
    config_path = os.path.join(os.path.dirname(__file__), "config", "genesis.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                file_config = json.load(f)
                
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

    display_config = f"Mode={file_config.get('networkType')}, Consensus={config['consensus']}, Sync={config.get('syncMode')}, Runtime={config.get('runtime')}"
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

    # 2. Blockchain (depends on Consensus, Runtime)
    chain = Blockchain(consensus=consensus, runtime=runtime)

    # 3. Sync (depends on Chain, Network)
    sync = di.get_sync(chain, network)

    # Start API Server
    api_thread = threading.Thread(target=server.run, args=(chain, args.api_port))
    api_thread.daemon = True
    api_thread.start()

    # Start Network
    # asyncio.run(network.start_server())
    
    # Simple mining loop for demo
    while True:
        time.sleep(5)
        if chain.pending_transactions:
            print("Mining pending transactions...")
            chain.mine_pending_transactions("miner1")
        
if __name__ == "__main__":
    main()
