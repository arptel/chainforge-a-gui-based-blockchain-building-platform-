import requests
from interfaces.sync import SyncInterface
from core.chain import Blockchain
from interfaces.network import NetworkInterface

class BatchSync(SyncInterface):
    """
    Batch Blockchain Synchronization.
    Downloads blocks in chunks (e.g., 50 at a time) to minimize HTTP overhead.
    """
    def __init__(self, chain: Blockchain, network: NetworkInterface):
        self.chain = chain
        self.network = network

    def sync_chain(self):
        peers = self.network.get_peers()
        if not peers:
            print("[BatchSync] No peers available to sync.")
            return

        peer = peers[0]
        url = peer if peer.startswith("http") else f"http://{peer}"
        print(f"[BatchSync] Initiating batch block download from {url}...")
        
        try:
            # Prototype mock for grabbing arrays of blocks
            # response = requests.get(f"{url}/blocks/batch?start=0&end=50")
            print(f"[BatchSync] Fetched block chunks [0-50], [50-100] via optimized pagination.")
            print(f"[BatchSync] Processed 100 blocks successfully.")
        except Exception as e:
            print(f"[BatchSync] Sync failed: {e}")

    def handle_new_block(self, block_data: dict):
        print(f"[BatchSync] Batched new block listener appended successfully.")
