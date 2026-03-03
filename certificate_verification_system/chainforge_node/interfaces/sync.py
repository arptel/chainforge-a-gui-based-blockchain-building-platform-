from abc import ABC, abstractmethod
from typing import Any, Optional

class SyncInterface(ABC):
    @abstractmethod
    def sync_chain(self):
        """Synchronize the chain from peers."""
        pass

    @abstractmethod
    def handle_new_block(self, block: Any):
        """Handle a new block received from the network."""
        pass

    @abstractmethod
    def handle_gap(self, incoming_index: int) -> Optional[str]:
        """
        Handle a gap detected between our latest block and an incoming block.
        Optionally returns a string payload to be sent as a direct response via P2P.
        """
        pass

    @abstractmethod
    def handle_sync_response(self, response_data: Any):
        """Handle data returned from a sync request."""
        pass
