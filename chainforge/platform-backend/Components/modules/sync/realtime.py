from ...interfaces.sync import SyncInterface
from ...core.chain import Blockchain
from ...interfaces.network import NetworkInterface

class RealtimeSync(SyncInterface):
    """
    Real-time Sync: Immediate propagation and validation of blocks/transactions.
    Used in centralized or high-performance permissioned networks.
    """
    def __init__(self, chain: Blockchain, network: NetworkInterface):
        self.chain = chain
        self.network = network
        print("Initializing Real-time Sync module...")

    def sync_chain(self):
        print("Real-time Sync: Listening for immediate broadcasts...")

    def handle_new_block(self, block):
        print(f"Real-time Sync: Immediately processing block {block}")
        self.chain.add_block(block)
