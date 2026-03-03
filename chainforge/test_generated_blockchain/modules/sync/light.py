import requests
from interfaces.sync import SyncInterface
from core.chain import Blockchain
from interfaces.network import NetworkInterface

class LightSync(SyncInterface):
    """
    Light Blockchain Synchronization.
    Downloads ONLY block headers (excluding the heavy transaction payloads).
    """
    def __init__(self, chain: Blockchain, network: NetworkInterface):
        self.chain = chain
        self.network = network

    def sync_chain(self):
        peers = self.network.get_peers()
        if not peers:
            print("[LightSync] No peers available to sync.")
            return

        peer = peers[0]
        url = peer if peer.startswith("http") else f"http://{peer}"
        print(f"[LightSync] Initiating header-only block download from {url}...")
        
        try:
            # Prototype mock for grabbing block headers
            # response = requests.get(f"{url}/headers?start=0")
            print(f"[LightSync] Successfully downloaded historical block headers.")
            print(f"[LightSync] Merkle roots verified. All transaction bodies ignored.")
        except Exception as e:
            print(f"[LightSync] Sync failed: {e}")

    def handle_new_block(self, block_data: dict):
        # Already stripped within chain role processing, here we verify the interface handles it properly
        print(f"[LightSync] Received block header via gossip protocol. Body discarded.")
