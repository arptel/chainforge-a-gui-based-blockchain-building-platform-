import requests
import threading
from interfaces.sync import SyncInterface
from core.chain import Blockchain
from interfaces.network import NetworkInterface
from core.block import Block

class FullSync(SyncInterface):
    """
    Full Blockchain Synchronization via WebSockets.
    Requests missing blocks from peers upon startup or connection.
    """
    def __init__(self, chain: Blockchain, network: NetworkInterface):
        self.chain = chain
        self.network = network
        self._sync_lock = threading.Lock()
        self._syncing = False  # Guard against concurrent sync operations

    def sync_chain(self):
        """
        Triggered when the node formally starts.
        We broadcast our current index to all connected peers asking them 
        to fill in any gaps we have.
        """
        peers = self.network.get_peers()
        if not peers:
            print("[FullSync] No peers available to sync on boot. Waiting for gossip...")
            return

        current_index = self.chain.last_block.index
        print(f"[FullSync] Initiating network block sync starting from index {current_index}...")
        
        # Fire the sync request via the network's internal queue mechanism to avoid cross-thread async blocks
        if hasattr(self.network, 'trigger_sync_request'):
            self.network.trigger_sync_request(current_index)
        else:
            print("[FullSync] Network interface missing trigger_sync_request")

    def handle_gap(self, incoming_index: int) -> str:
        """
        Triggered by P2P when a block index gap is detected.
        Returns the SYNC_REQUEST payload string to be sent back.
        """
        print(f"[FullSync] Handling gap up to {incoming_index}. Requesting blocks after {self.chain.last_block.index}.")
        import json
        return json.dumps({"type": "SYNC_REQUEST", "data": {"last_index": self.chain.last_block.index}})

    def handle_new_block(self, block: Block) -> bool:
        """
        Triggered by P2P when a NEW_BLOCK is gossiped.
        Attempts to add to the chain.
        Returns True if successful, False if invalid or gap detected.
        """
        if block.index == self.chain.last_block.index + 1:
            print(f"[FullSync] Applying gossiped block {block.index} via FullSync.")
            return self.chain.add_block(block)
        return False

    def handle_sync_response(self, blocks_data: list) -> str:
        """
        Triggered by P2P when a SYNC_RESPONSE is received.
        Applies historical blocks. If application fails due to hash mismatch,
        initiates fork resolution by requesting older blocks iteratively.
        Returns a new SYNC_REQUEST string if fallback is needed, else None.
        """
        if not blocks_data:
            return None

        # Prevent multiple concurrent sync responses from corrupting the chain
        if not self._sync_lock.acquire(blocking=False):
            print("[FullSync] Sync already in progress, dropping duplicate response.")
            return None
        
        try:
            print(f"[FullSync] Received {len(blocks_data)} historical blocks. Applying...")
            new_chain = []
            for b_data in blocks_data:
                block = Block.from_dict(b_data)
                new_chain.append(block)

            attach_index = new_chain[0].index
            
            # Quick dedup: if we already have this block, skip
            if attach_index <= self.chain.last_block.index:
                # Check if last block in the response is also already applied
                if new_chain[-1].index <= self.chain.last_block.index:
                    print(f"[FullSync] Already have blocks up to {self.chain.last_block.index}, skipping duplicate sync.")
                    return None
                # Filter to only blocks we don't have yet
                new_chain = [b for b in new_chain if b.index > self.chain.last_block.index]
                if not new_chain:
                    return None
                attach_index = new_chain[0].index
            
            # 1. Check if this suffix hooks into our current chain tip
            if attach_index == self.chain.last_block.index + 1:
                if self.chain.is_valid_chain(self.chain.chain):
                    added = self.chain.append_chain_suffix(new_chain)
                    if added > 0:
                        print(f"[FullSync] Applied {added} blocks via sync. Chain now at index {self.chain.last_block.index}.")
                        return None
                    else:
                        print("[FullSync] append_chain_suffix failed.")
                else:
                    print("[FullSync] Local chain is invalid (tampered). Bypassing simple append to force full fork resolution.")

            # 2. Fork Resolution / Suffix Replacement
            if not self.chain.is_valid_chain(new_chain, is_suffix=True):
                print("[FullSync] Received invalid sync chain suffix. Dropping.")
                return None
            
            if attach_index - 1 < len(self.chain.chain):
                local_anchor = self.chain.chain[attach_index - 1]
                local_chain_to_anchor = self.chain.chain[:attach_index]
                
                if new_chain[0].previous_hash == local_anchor.hash and self.chain.is_valid_chain(local_chain_to_anchor):
                    potential_length = attach_index + len(new_chain)
                    if potential_length > len(self.chain.chain):
                        print(f"[FullSync] Valid common ancestor found at index {attach_index - 1}. Initiating replace_chain for fork resolution.")
                        success = self.chain.replace_chain(new_chain)
                        if success:
                            print(f"[FullSync] Successfully resolved fork. Chain tip is now {self.chain.last_block.index}.")
                        return None
                    else:
                        print(f"[FullSync] Fork is not longer ({potential_length}) than our chain ({len(self.chain.chain)}). Ignoring.")
                        return None
                else:
                    if new_chain[0].previous_hash == local_anchor.hash:
                        print(f"[FullSync] Anchor hash matches at {attach_index - 1}, but local history is tampered. Forcing older block download.")
                
            # 3. Fallback
            fallback_target = max(0, attach_index - 10)
            print(f"[FullSync] Anchor mismatch or local tamper detected at index {attach_index}. Falling back to request blocks after index {fallback_target}.")
            import json
            return json.dumps({"type": "SYNC_REQUEST", "data": {"last_index": fallback_target}})
        finally:
            self._sync_lock.release()
