from ...interfaces.sync import SyncInterface
from ...core.chain import Blockchain
from ...interfaces.network import NetworkInterface

class BatchSync(SyncInterface):
    """
    Batch Sync: Processes blocks in batches to optimize throughput.
    """
    def __init__(self, chain: Blockchain, network: NetworkInterface):
        self.chain = chain
        self.network = network
        print("Initializing Batch Sync module...")

    def sync_chain(self):
        print("Batch Sync: Requesting block batches...")

    def handle_new_block(self, block):
        print(f"Batch Sync: Queuing block {block} for batch processing...")
        # Add to queue, process when batch is full
        self.chain.add_block(block) 
