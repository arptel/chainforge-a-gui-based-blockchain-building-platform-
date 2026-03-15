import requests
import threading
import time
from interfaces.sync import SyncInterface
from core.chain import Blockchain
from interfaces.network import NetworkInterface
from core.block import Block


class RealtimeSync(SyncInterface):
    """Realtime Stream Synchronization.

    Polls peers periodically for the latest chain state and updates local state.
    """

    def __init__(self, chain: Blockchain, network: NetworkInterface):
        self.chain = chain
        self.network = network
        self._is_polling = False
        self._last_known_index = chain.last_block.index

    def _to_http(self, peer: str) -> str:
        if peer.startswith("ws://"):
            return peer.replace("ws://", "http://").rstrip("/ws")
        if peer.startswith("wss://"):
            return peer.replace("wss://", "https://").rstrip("/ws")
        if peer.startswith("http://") or peer.startswith("https://"):
            return peer.rstrip("/ws")
        return f"http://{peer}"

    def _poll_chain(self):
        print(f"[RealtimeSync] Background polling thread activated.")
        while self._is_polling:
            peers = self.network.get_peers()
            if peers:
                peer = peers[0]
                url = self._to_http(peer)
                try:
                    resp = requests.get(f"{url}/headers", timeout=5)
                    resp.raise_for_status()
                    headers = resp.json()
                    if isinstance(headers, list) and headers:
                        if len(headers) > self._last_known_index + 1:
                            blocks = [Block.from_dict(h) for h in headers]
                            if len(blocks) > len(self.chain.chain):
                                print(f"[RealtimeSync] Found newer chain (len={len(blocks)}). Updating local chain.")
                                self.chain.replace_chain(blocks)
                                self._last_known_index = self.chain.last_block.index
                except Exception as e:
                    # Swallow errors to keep polling
                    pass
            time.sleep(2)  # Stream every 2 seconds

    def sync_chain(self):
        print(f"[RealtimeSync] Starting realtime sync polling thread...")
        if not self._is_polling:
            self._is_polling = True
            threading.Thread(target=self._poll_chain, daemon=True).start()

    def handle_new_block(self, block_data: dict):
        print(f"[RealtimeSync] Realtime stream caught new block index={block_data.get('index')}")
        try:
            block = Block.from_dict(block_data)
            self.chain.add_block(block)
            self._last_known_index = self.chain.last_block.index
        except Exception as e:
            print(f"[RealtimeSync] Failed to apply new block: {e}")
