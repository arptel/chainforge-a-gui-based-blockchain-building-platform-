import requests
from interfaces.sync import SyncInterface
from core.chain import Blockchain
from interfaces.network import NetworkInterface


class SnapshotSync(SyncInterface):
    """State Snapshot Synchronization.

    Loads a complete state dump from a peer and overwrites local state.
    """

    def __init__(self, chain: Blockchain, network: NetworkInterface):
        self.chain = chain
        self.network = network

    def _to_http(self, peer: str) -> str:
        if peer.startswith("ws://"):
            return peer.replace("ws://", "http://").rstrip("/ws")
        if peer.startswith("wss://"):
            return peer.replace("wss://", "https://").rstrip("/ws")
        if peer.startswith("http://") or peer.startswith("https://"):
            return peer.rstrip("/ws")
        return f"http://{peer}"

    def sync_chain(self):
        peers = self.network.get_peers()
        if not peers:
            print("[SnapshotSync] No peers available to sync.")
            return

        for peer in peers:
            url = self._to_http(peer)
            try:
                print(f"[SnapshotSync] Downloading state snapshot from {url}/state")
                resp = requests.get(f"{url}/state", timeout=5)
                resp.raise_for_status()
                state = resp.json()

                # Overwrite local state with peer snapshot
                self.chain.state = state
                print(f"[SnapshotSync] State snapshot applied ({len(state)} entries).")
                return
            except Exception as e:
                print(f"[SnapshotSync] Failed to sync from {peer}: {e}")

        print("[SnapshotSync] No peer provided usable state snapshot.")

    def handle_new_block(self, block_data: dict):
        # Snapshot nodes may still want to keep track of latest block index
        print(f"[SnapshotSync] New block notification received (index={block_data.get('index')}).")
