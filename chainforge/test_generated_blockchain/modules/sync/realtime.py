import requests
import threading
import time
from interfaces.sync import SyncInterface
from core.chain import Blockchain
from interfaces.network import NetworkInterface

class RealtimeSync(SyncInterface):
    """
    Realtime Stream Synchronization.
    Utilizes an active polling (or websocket) background thread to constantly drain the mempool.
    """
    def __init__(self, chain: Blockchain, network: NetworkInterface):
        self.chain = chain
        self.network = network
        self._is_polling = False

    def _poll_mempool(self):
        print(f"[RealtimeSync] Background polling thread activated.")
        while self._is_polling:
            peers = self.network.get_peers()
            if peers:
                peer = peers[0]
                url = peer if peer.startswith("http") else f"http://{peer}"
                try:
                    # In a prototype, simulate WebSocket or aggressive HTTP polling
                    # response = requests.get(f"{url}/transactions")
                    pass
                except Exception:
                    pass
            time.sleep(2) # Stream every 2 seconds

    def sync_chain(self):
        """
        Start the standard base sync, then kick off the realtime polling stream.
        """
        print(f"[RealtimeSync] Executing standard chain catch-up before socket stream opens...")
        
        if not self._is_polling:
            self._is_polling = True
            threading.Thread(target=self._poll_mempool, daemon=True).start()

    def handle_new_block(self, block_data: dict):
        print(f"[RealtimeSync] Realtime stream caught new block!")
