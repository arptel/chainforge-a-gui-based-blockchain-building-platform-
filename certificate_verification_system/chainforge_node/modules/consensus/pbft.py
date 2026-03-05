import time
import uuid
from interfaces.consensus import ConsensusInterface
from core.block import Block

class PBFTConsensus(ConsensusInterface):
    """
    Practical Byzantine Fault Tolerance.
    Implements a mocked 3-phase network consensus (Pre-Prepare, Prepare, Commit).
    """
    def __init__(self, network_layer=None):
        self.network = network_layer

    def validate_block(self, block: Block) -> bool:
        # PBFT requires checking the 2/3 majority signature cache
        # In this prototype, we mock this network-heavy check.
        print(f"[PBFT] Validated 2/3 majority signatures for block {block.index}.")
        return True

    def propose_block(self, transactions: list, previous_hash: str, index: int, miner_address: str, state_root: str = "") -> Block:
        print(f"\n[PBFT] Initiating 3-Phase BFT Commit for Node {miner_address}...")
        
        # 1. Pre-Prepare (Broadcast Intent)
        print(f"[PBFT] 🔵 Phase 1: Casting Pre-Prepare proposal to peers...")
        time.sleep(0.5) # Simulate network propagation latency
        
        # 2. Prepare (Wait for 2/3 peer responses)
        # Normally: self.network.broadcast(...) and wait for peers to reply
        print(f"[PBFT] 🟡 Phase 2: Awaiting 'Prepare' votes from >66% of network...")
        time.sleep(0.5) 
        
        # 3. Commit
        print(f"[PBFT] 🟢 Phase 3: >66% Prepare threshold reached! Broadcasting 'Commit'.")
        time.sleep(0.2)
        print(f"[PBFT] Consensus achieved. Appending block locally.")
        
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
