import asyncio
from typing import List, Any
from ...interfaces.network import NetworkInterface

class P2PNetwork(NetworkInterface):
    """
    Simple P2P Network implementation using asyncio.
    """
    def __init__(self, port: int = 5000):
        self.peers = set()
        self.port = port
        self.server = None

    async def start_server(self):
        self.server = await asyncio.start_server(
            self.handle_connection, '0.0.0.0', self.port)
        async with self.server:
            await self.server.serve_forever()

    async def handle_connection(self, reader, writer):
        data = await reader.read(100)
        message = data.decode()
        addr = writer.get_extra_info('peername')
        print(f"Received {message} from {addr}")
        writer.close()

    def broadcast(self, message: Any):
        # Logic to send message to all peers
        pass

    def connect_to_peer(self, peer_address: str):
        self.peers.add(peer_address)
        # Logic to establish connection
        pass

    def get_peers(self) -> List[str]:
        return list(self.peers)
