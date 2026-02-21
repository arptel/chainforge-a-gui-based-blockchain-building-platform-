from abc import ABC, abstractmethod
from typing import Any

class SyncInterface(ABC):
    @abstractmethod
    def sync_chain(self):
        """Synchronize the chain from peers."""
        pass

    @abstractmethod
    def handle_new_block(self, block: Any):
        """Handle a new block received from the network."""
        pass
