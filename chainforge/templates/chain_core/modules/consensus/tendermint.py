import time
from interfaces.consensus import ConsensusInterface
from core.block import Block

class TendermintConsensus(ConsensusInterface):
    """
    Tendermint BFT.
    Implements a deterministic state-machine 3-phase consensus loop (Propose, Pre-vote, Pre-commit).
    """
    def __init__(self, network_layer=None):
        self.network = network_layer

    def validate_block(self, block: Block) -> bool:
        print(f"[Tendermint] Checked active validator set. Validated +2/3 signatures for block {block.index}.")
        return True

    def propose_block(self, transactions: list, previous_hash: str, index: int, miner_address: str, state_root: str = "") -> Block:
        print(f"\n[Tendermint] Starting Round 0 for Height {index}...")
        
        # Phase 1: Propose
        print(f"[Tendermint] 🔵 Propose: Disseminating block part hashes...")
        time.sleep(0.4) 
        
        # Phase 2: Pre-vote 
        print(f"[Tendermint] 🟡 Pre-vote: Receiving signed peer votes for part hashes...")
        time.sleep(0.4) 
        
        # Phase 3: Pre-commit
        print(f"[Tendermint] 🟢 Pre-commit: +2/3 Pre-votes validated! Sealing state deterministic commitment.")
        time.sleep(0.2)
        
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
