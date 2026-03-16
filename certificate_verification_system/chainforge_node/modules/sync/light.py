import requests
from interfaces.sync import SyncInterface
from core.chain import Blockchain
from interfaces.network import NetworkInterface
from core.block import Block


class LightSync(SyncInterface):
    """Light Blockchain Synchronization.

    Downloads only block headers and keeps a lightweight copy of the chain.
    """

    def __init__(self, chain: Blockchain, network: NetworkInterface):
        self.chain = chain
        self.network = network

    def _to_http(self, peer: str) -> str:
        # Convert ws:// or wss:// peer urls to http(s) for REST queries
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
            print("[LightSync] No peers available to sync.")
            return

        for peer in peers:
            url = self._to_http(peer)
            try:
                print(f"[LightSync] Requesting headers from {url}/headers")
                resp = requests.get(f"{url}/headers", timeout=5)
                resp.raise_for_status()

                headers = resp.json()
                if not isinstance(headers, list) or not headers:
                    continue

                # Convert to Block objects, ignoring transaction payloads optimistically
                blocks = [Block.from_dict(h) for h in headers]
                if len(blocks) > len(self.chain.chain):
                    print(f"[LightSync] Found longer chain ({len(blocks)}) from {peer}. Replacing local chain.")
                    self.chain.replace_chain(blocks)
                else:
                    print(f"[LightSync] Peer chain not longer (peer={len(blocks)}, local={len(self.chain.chain)}).")
                return
            except Exception as e:
                print(f"[LightSync] Failed to sync from {peer}: {e}")

        print("[LightSync] No peer provided usable headers for sync.")

    def handle_new_block(self, block_data: dict):
        # Keep light nodes lean by not executing transactions when role is 'light'
        print(f"[LightSync] Received new block header (index={block_data.get('index')}).")
        try:
            block = Block.from_dict(block_data)
            self.chain.add_block(block)
        except Exception as e:
            print(f"[LightSync] Failed to apply new block header: {e}")
