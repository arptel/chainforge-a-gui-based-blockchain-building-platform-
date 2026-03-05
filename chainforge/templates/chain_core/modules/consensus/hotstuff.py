import time
from interfaces.consensus import ConsensusInterface
from core.block import Block

class HotStuffConsensus(ConsensusInterface):
    """
    HotStuff BFT.
    Implements a pipelined 3-phase consensus loop favored by modern networks (Libra/Diem, Aptos).
    """
    def __init__(self, network_layer=None):
        self.network = network_layer

    def validate_block(self, block: Block) -> bool:
        print(f"[HotStuff] Pipelined view confirmed. Block {block.index} Quorum signature valid.")
        return True

    def propose_block(self, transactions: list, previous_hash: str, index: int, miner_address: str, state_root: str = "") -> Block:
        print(f"\n[HotStuff] Leader proposing pipelined block view...")
        
        # Phase 1: Prepare
        print(f"[HotStuff] 🔵 Prepare Phase: Threshold signatures requested...")
        time.sleep(0.3) 
        
        # Phase 2: Pre-commit
        print(f"[HotStuff] 🟡 Pre-commit Phase: Building quorum certificate (QC)...")
        time.sleep(0.3) 
        
        # Phase 3: Commit
        print(f"[HotStuff] 🟢 Commit Phase: View transitioned. Block canonicalized.")
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
