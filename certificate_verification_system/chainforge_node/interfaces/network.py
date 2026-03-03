from abc import ABC, abstractmethod
from typing import Any, List

class NetworkInterface(ABC):
    @abstractmethod
    def set_sync_module(self, sync_module: Any):
        """Set the active sync module instance."""
        pass

    @abstractmethod
    def broadcast(self, message: Any):
        """Broadcast a message to the network."""
        pass

    @abstractmethod
    def connect_to_peer(self, peer_address: str):
        """Connect to a peer."""
        pass

    @abstractmethod
    def get_peers(self) -> List[str]:
        """Get list of connected peers."""
        pass
