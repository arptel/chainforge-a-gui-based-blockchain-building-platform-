import requests
from interfaces.sync import SyncInterface
from core.chain import Blockchain
from interfaces.network import NetworkInterface
from core.block import Block


class FastSync(SyncInterface):
    """Fast Blockchain Synchronization.

    Downloads a snapshot of the state + recent headers and brings the node up to date.
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
            print("[FastSync] No peers available to sync.")
            return

        for peer in peers:
            url = self._to_http(peer)
            try:
                print(f"[FastSync] Fetching state snapshot from {url}/state")
                resp_state = requests.get(f"{url}/state", timeout=5)
                resp_state.raise_for_status()
                state = resp_state.json()

                # Apply state snapshot
                self.chain.state = state
                print(f"[FastSync] Applied state snapshot with {len(state)} entries.")

                # Fetch headers to update the chain tip (without executing old txs if role is light)
                resp_headers = requests.get(f"{url}/headers", timeout=5)
                resp_headers.raise_for_status()
                headers = resp_headers.json()

                blocks = [Block.from_dict(h) for h in headers]
                if len(blocks) > len(self.chain.chain):
                    print(f"[FastSync] Updating chain to {len(blocks)} blocks (from {len(self.chain.chain)}).")
                    self.chain.replace_chain(blocks)
                else:
                    print("[FastSync] Peer chain not longer than local chain.")

                return
            except Exception as e:
                print(f"[FastSync] Failed to sync from {peer}: {e}")

        print("[FastSync] No peer provided usable sync data.")

    def handle_new_block(self, block_data: dict):
        print(f"[FastSync] New block gossip received: {block_data.get('index')}")
        try:
            block = Block.from_dict(block_data)
            self.chain.add_block(block)
        except Exception as e:
            print(f"[FastSync] Failed to apply new block: {e}")

    def handle_gap(self, incoming_index: int) -> str:
        print(f"[FastSync] Gap detected at index {incoming_index}. Requesting full sync via SYNC_REQUEST.")
        import json
        return json.dumps({"type": "SYNC_REQUEST", "data": {"last_index": self.chain.last_block.index}})

    def handle_sync_response(self, response_data: dict) -> str:
        # Treat this like a full sync response (blocks list)
        print("[FastSync] Received sync response; applying blocks.")
        try:
            blocks = [Block.from_dict(b) for b in response_data]
            self.chain.replace_chain(blocks)
        except Exception as e:
            print(f"[FastSync] Failed to apply sync response blocks: {e}")
        return None
