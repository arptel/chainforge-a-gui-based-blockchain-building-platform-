import hashlib
import json
import time
from typing import List, Dict, Any, Optional

class Block:
    def __init__(self, index: int, transactions: List[Dict[str, Any]], timestamp: float, previous_hash: str, validator: str):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.validator = validator
        self.nonce = 0
        self.hash = self.compute_hash()

    def compute_hash(self) -> str:
        """
        A function that return the hash of the block contents.
        """
        block_data = self.__dict__.copy()
        if 'hash' in block_data:
            del block_data['hash']
            
        block_string = json.dumps(block_data, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__
