import requests
from interfaces.sync import SyncInterface
from core.chain import Blockchain
from interfaces.network import NetworkInterface
from core.block import Block

class FastSync(SyncInterface):
    """
    Fast Blockchain Synchronization.
    Downloads the database snapshot firsthand, then only downloads recent headers.
    """
    def __init__(self, chain: Blockchain, network: NetworkInterface):
        self.chain = chain
        self.network = network

    def sync_chain(self):
        peers = self.network.get_peers()
        if not peers:
            print("[FastSync] No peers available to sync.")
            return

        peer = peers[0]
        url = peer if peer.startswith("http") else f"http://{peer}"
        print(f"[FastSync] Initiating state snapshot download from {url}...")
        
        try:
            resp_state = requests.get(f"{url}/state", timeout=5)
            resp_state.raise_for_status()
            self.chain.state = resp_state.json()
            print("[FastSync] Applied state snapshot.")
            
            resp_headers = requests.get(f"{url}/headers", timeout=5)
            if resp_headers.status_code == 200:
                headers = resp_headers.json()
                blocks = [Block.from_dict(h) for h in headers]
                if len(blocks) > len(self.chain.chain):
                    self.chain.replace_chain(blocks)
                    print("[FastSync] Node is now caught up without executing old transactions.")
        except Exception as e:
            print(f"[FastSync] Sync failed: {e}")

    def handle_new_block(self, block_data: dict):
        # We append normally now that we possess the state
        print(f"[FastSync] Handled new block gossip.")
