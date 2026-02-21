from ...interfaces.sync import SyncInterface
from ...core.chain import Blockchain
from ...interfaces.network import NetworkInterface
from typing import Any

class FullSync(SyncInterface):
    """
    Full Blockchain Synchronization.
    """
    def __init__(self, chain: Blockchain, network: NetworkInterface):
        self.chain = chain
        self.network = network

    def sync_chain(self):
        """
        Request blocks from peers until caught up.
        """
        peers = self.network.get_peers()
        if not peers:
            print("No peers to sync with")
            return
        
        # Logic to query peers for their latest block and download missing links
        pass

    def handle_new_block(self, block: Any):
        """
        Validate and add new block.
        """
        # Logic to validate and append
        if self.chain.add_block(block):
            print(f"Added block {block.index}")
        else:
            print(f"Block {block.index} rejected")
