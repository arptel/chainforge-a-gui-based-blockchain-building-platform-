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
        computed_hash = block.compute_hash()
        print(f"[PoW] Block {block.index} hash ({block.hash[:10]}...) failed difficulty target.")
        print(f"      Debugging validation mismatch -- Computed hash: {computed_hash[:10]}... Block hash property: {block.hash[:10]}...")
        import json
        block_data = block.__dict__.copy()
        if "hash" in block_data:
            del block_data["hash"]
        print(f"      Block Dict for Hash Calculation: {json.dumps(block_data, sort_keys=True)}")
        return False

    def propose_block(self, transactions: list, previous_hash: str, index: int, miner_address: str, state_root: str = "") -> Block:
        print(f"\n[PoW] Mining block {index} with difficulty {self.target_difficulty}...")
        
        block = Block(
            index=index,
            transactions=transactions,
            timestamp=time.time(),
            previous_hash=previous_hash,
            validator=miner_address,
            state_root=state_root
        )
        
        # Explicit active hashing loop
        block.nonce = 0
        target = "0" * self.target_difficulty
        while True:
            # Let the block compute its own hash based on its current nonce
            current_hash = block.compute_hash()
            
            if current_hash.startswith(target):
                block.hash = current_hash
                print(f"[PoW] Mined block {index}! Nonce: {block.nonce} Hash: {current_hash[:15]}...")
                return block
            block.nonce += 1

    def commit_block(self, block: Block) -> bool:
        return True
