import asyncio
from typing import List, Any
import requests
import json
import threading
from interfaces.network import NetworkInterface

class P2PNetwork(NetworkInterface):
    """
    HTTP-based P2P Network implementation.
    Nodes share data by calling each other's REST APIs.
    """
    def __init__(self, port: int = 5000):
        self.peers = set()
        self.port = port
        
    async def start_server(self):
        # Inbound networking is managed entirely by FastAPI.
        # This explicit bypass prevents spawning a redundant network stack.
        pass

    def _broadcast_task(self, endpoint: str, payload: dict):
        for peer in self.peers:
            try:
                # Ensure peer has http prefix
                url = peer if peer.startswith("http") else f"http://{peer}"
                response = requests.post(f"{url}{endpoint}", json=payload, timeout=2)
            except Exception as e:
                print(f"Failed to broadcast to {peer}: {e}")

    def broadcast(self, message: dict):
        """Route generic network messages based on type."""
        msg_type = message.get("type", "")
        if msg_type == "NEW_TRANSACTION":
            self.broadcast_transaction(message.get("data", {}))
        elif msg_type == "NEW_BLOCK":
            # Some callers pass object data directly, others may pass block objects
            data = message.get("data", {})
            threading.Thread(target=self._broadcast_task, args=("/blocks/sync", {"block": data}), daemon=True).start()
        else:
            threading.Thread(target=self._broadcast_task, args=("/message", message), daemon=True).start()

    def broadcast_transaction(self, tx: dict):
        """Broadcast a transaction to all connected peers"""
        threading.Thread(target=self._broadcast_task, args=("/transactions/sync", {"tx": tx}), daemon=True).start()

    def broadcast_block(self, block: Any):
        """Broadcast a new block to all connected peers"""
        threading.Thread(target=self._broadcast_task, args=("/blocks/sync", {"block": block.to_dict()}), daemon=True).start()

    def connect_to_peer(self, peer_address: str):
        if peer_address and peer_address not in self.peers:
            print(f"Connecting to peer: {peer_address}")
            self.peers.add(peer_address)

    def get_peers(self) -> List[str]:
        return list(self.peers)
