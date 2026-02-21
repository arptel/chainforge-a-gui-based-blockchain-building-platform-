from ...interfaces.consensus import ConsensusInterface
from ...core.block import Block
from typing import Any, Dict
import hashlib

class PoWConsensus(ConsensusInterface):
    def __init__(self, difficulty: int = 4):
        self.difficulty = difficulty

    def propose_block(self, transactions: list[Dict[str, Any]]) -> Any:
        # Simplified for template purposes
        # In reality, this would construct a block and mine it
        pass

    def mine_block(self, block: Block) -> Block:
        """
        Proof of Work mining algorithm
        """
        target = "0" * self.difficulty
        while block.hash[:self.difficulty] != target:
            block.nonce += 1
            block.hash = block.compute_hash()
        return block

    def validate_block(self, block: Block) -> bool:
        if block.hash != block.compute_hash():
            return False
        if block.hash[:self.difficulty] != "0" * self.difficulty:
            return False
        return True

    def commit_block(self, block: Any) -> bool:
        return True
