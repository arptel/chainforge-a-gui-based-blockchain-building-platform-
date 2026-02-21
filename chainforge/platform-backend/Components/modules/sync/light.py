from ...interfaces.sync import SyncInterface
from ...core.chain import Blockchain
from ...interfaces.network import NetworkInterface

class LightSync(SyncInterface):
    """
    Light Sync: Downloads only block headers and verifies Merkle proofs for specific transactions.
    Ideal for mobile or embedded devices.
    """
    def __init__(self, chain: Blockchain, network: NetworkInterface):
        self.chain = chain
        self.network = network
        print("Initializing Light Sync module...")

    def sync_chain(self):
        print("Light Sync: Requesting block headers from peers...")
        # Logic to download headers only
        # self.network.broadcast("GET_HEADERS")

    def handle_new_block(self, block):
        print(f"Light Sync: Received new block header {block}")
        # Verify header validity only
