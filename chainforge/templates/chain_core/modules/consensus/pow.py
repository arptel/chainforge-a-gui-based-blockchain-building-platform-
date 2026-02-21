import time
import hashlib
from interfaces.consensus import ConsensusInterface
from core.block import Block

class PoWConsensus(ConsensusInterface):
    """
    Proof of Work Consensus.
    Miners must compute a hash value lower than the target difficulty.
    """
    def __init__(self, target_difficulty=4):
        self.target_difficulty = target_difficulty

    def validate_block(self, block: Block) -> bool:
        if block.hash.startswith("0" * self.target_difficulty):
            print(f"[PoW] Block {block.index} hash ({block.hash[:10]}...) met difficulty {self.target_difficulty}. Validated!")
            return True
        print(f"[PoW] Block {block.index} hash ({block.hash[:10]}...) failed difficulty target.")
        return False

    def propose_block(self, transactions: list, previous_hash: str, index: int, miner_address: str) -> Block:
        print(f"\n[PoW] Mining block {index} with difficulty {self.target_difficulty}...")
        
        block = Block(
            index=index,
            transactions=transactions,
            timestamp=time.time(),
            previous_hash=previous_hash,
            validator=miner_address
        )
        
        # Explicit active hashing loop
        nonce = 0
        target = "0" * self.target_difficulty
        while True:
            # Reconstruct the string to hash identical to block's calculate_hash()
            header = f"{block.index}{block.previous_hash}{block.timestamp}{block.transactions}{nonce}{block.validator}"
            current_hash = hashlib.sha256(header.encode()).hexdigest()
            
            if current_hash.startswith(target):
                block.nonce = nonce
                block.hash = current_hash
                print(f"[PoW] 🎯 Mined block {index}! Nonce: {nonce} Hash: {current_hash[:15]}...")
                return block
            nonce += 1

    def commit_block(self, block: Block) -> bool:
        return True
