import time
from interfaces.consensus import ConsensusInterface
from core.block import Block

class NoConsensus(ConsensusInterface):
    """
    Deterministic Sandbox Configuration (No Consensus).
    Instantly validates and proposes blocks without any cryptographic or network restrictions.
    Excellent for local functional testing of Smart Contracts.
    """
    def __init__(self):
        # We don't need any state or network bindings
        pass

    def validate_block(self, block: Block) -> bool:
        print(f"[None/Sandbox] Validated block {block.index} instantly. Sandbox mode active.")
        return True

    def propose_block(self, transactions: list, previous_hash: str, index: int, miner_address: str, state_root: str = "") -> Block:
        print(f"\n[None/Sandbox] Proposing block {index} instantly...")
        
        return Block(
            index=index,
            transactions=transactions,
            timestamp=time.time(),
            previous_hash=previous_hash,
            validator=miner_address,
            state_root=state_root
        )

    def commit_block(self, block: Block) -> bool:
        return True
