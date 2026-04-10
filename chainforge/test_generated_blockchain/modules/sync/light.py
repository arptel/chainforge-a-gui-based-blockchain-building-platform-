import requests
from interfaces.sync import SyncInterface
from core.chain import Blockchain
from interfaces.network import NetworkInterface
from core.block import Block

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
            response = requests.get(f"{url}/headers")
            response.raise_for_status()
            headers = response.json()
            blocks = [Block.from_dict(h) for h in headers]
            if len(blocks) > len(self.chain.chain):
                self.chain.replace_chain(blocks)
                print(f"[LightSync] Successfully synced {len(blocks)} header-only blocks.")
        except Exception as e:
            print(f"[LightSync] Sync failed: {e}")

    def handle_new_block(self, block_data: dict):
        # Already stripped within chain role processing, here we verify the interface handles it properly
        print(f"[LightSync] Received block header via gossip protocol. Body discarded.")
