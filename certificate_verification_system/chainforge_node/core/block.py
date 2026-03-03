import hashlib
import json
import time
from typing import List, Dict, Any, Optional


class Block:
    def __init__(
        self,
        index: int,
        transactions: List[Dict[str, Any]],
        timestamp: float,
        previous_hash: str,
        validator: str,
        merkle_root: str = None,
        state_root: str = "",
    ):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.validator = validator
        self.nonce = 0

        # Merkle root over transactions — computed automatically if not provided
        if merkle_root is None:
            from core.merkle import compute_merkle_root
            self.merkle_root = compute_merkle_root(transactions)
        else:
            self.merkle_root = merkle_root

        # State root set by Blockchain.add_block after executing transactions
        # (empty string is a valid placeholder before state execution)
        self.state_root = state_root

        self.hash = self.compute_hash()

    def compute_hash(self) -> str:
        """SHA-256 over all block fields (excluding hash itself)."""
        block_data = {k: v for k, v in self.__dict__.items() if not k.startswith('_') and k != 'hash'}
        block_string = json.dumps(block_data, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Return a clean serializable copy of the block (not a live reference)."""
        return {
            "index": self.index,
            "transactions": self.transactions,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "validator": self.validator,
            "nonce": self.nonce,
            "merkle_root": self.merkle_root,
            "state_root": self.state_root,
            "hash": self.hash,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Block":
        """Reconstruct a Block from a serialized dict (e.g. from DB or network)."""
        block = cls(
            index=data["index"],
            transactions=data["transactions"],
            timestamp=data["timestamp"],
            previous_hash=data["previous_hash"],
            validator=data.get("validator", ""),
            merkle_root=data.get("merkle_root"),
            state_root=data.get("state_root", ""),
        )
        block.nonce = data.get("nonce", 0)
        # Compute the hash to ensure the properties match the sender's format exactly
        if "hash" in data:
            block.hash = data["hash"]
        else:
            block.hash = block.compute_hash()
        return block
