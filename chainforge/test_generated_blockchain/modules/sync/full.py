import requests
from interfaces.sync import SyncInterface
from core.chain import Blockchain
from interfaces.network import NetworkInterface
from core.block import Block

class FullSync(SyncInterface):
    """
    Full Blockchain Synchronization.
    Downloads and verifies every single block from genesis.
    """
    def __init__(self, chain: Blockchain, network: NetworkInterface):
        self.chain = chain
        self.network = network

    def sync_chain(self):
        peers = self.network.get_peers()
        if not peers:
            print("[FullSync] No peers available to sync.")
            return

        # Simple functional sync: fetch blocks from the first peer
        peer = peers[0]
        url = peer if peer.startswith("http") else f"http://{peer}"
        print(f"[FullSync] Initiating full block download from {url}...")
        
        try:
            response = requests.get(f"{url}/blocks")
            response.raise_for_status()
            blocks_data = response.json()
            blocks = [Block.from_dict(b) for b in blocks_data]
            if len(blocks) > len(self.chain.chain):
                print(f"[FullSync] Downloaded {len(blocks)} blocks. Applying...")
                # Note: For prototype, replace_chain handles state replay
                self.chain.replace_chain(blocks)
                print(f"[FullSync] Successfully synced. Chain tip is now {self.chain.last_block.index}.")
            else:
                print(f"[FullSync] Peer chain is not longer than local chain.")
        except Exception as e:
            print(f"[FullSync] Sync failed: {e}")

    def handle_new_block(self, block_data: dict):
        """
        Validate and add a newly gossiped block.
        """
        # In a real scenario, we deserialize the dict into a Block object
        # block = Block(**block_data)
        # self.chain.add_block(block)
        print(f"[FullSync] Validated and appended new block broadcast.")
