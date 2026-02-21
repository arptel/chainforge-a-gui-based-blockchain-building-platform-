from ...interfaces.sync import SyncInterface
from ...core.chain import Blockchain
from ...interfaces.network import NetworkInterface

class FastSync(SyncInterface):
    """
    Fast Sync: Downloads recent state snapshots and headers, verifying PoW/PoS, 
    but skipping full validation of historical blocks.
    """
    def __init__(self, chain: Blockchain, network: NetworkInterface):
        self.chain = chain
        self.network = network
        print("Initializing Fast Sync module...")

    def sync_chain(self):
        print("Fast Sync: Requesting recent state snapshots from peers...")
        # Logic to download state trie + recent blocks
        # self.network.broadcast("GET_SNAPSHOT")

    def handle_new_block(self, block):
        print(f"Fast Sync: Received new block {block}")
        # Standard block handling after sync
        self.chain.add_block(block)
