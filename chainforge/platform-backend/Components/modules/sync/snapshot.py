from ...interfaces.sync import SyncInterface
from ...core.chain import Blockchain
from ...interfaces.network import NetworkInterface

class SnapshotSync(SyncInterface):
    """
    Snapshot Sync: periodically downloads the full state at a specific block height.
    """
    def __init__(self, chain: Blockchain, network: NetworkInterface):
        self.chain = chain
        self.network = network
        print("Initializing Snapshot Sync module...")

    def sync_chain(self):
        print("Snapshot Sync: Downloading latest state snapshot...")
        # Logic to download complete state dump

    def handle_new_block(self, block):
        print(f"Snapshot Sync: Processing block {block}")
        self.chain.add_block(block)
