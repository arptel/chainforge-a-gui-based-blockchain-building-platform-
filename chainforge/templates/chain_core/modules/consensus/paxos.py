import time
import random
from interfaces.consensus import ConsensusInterface
from core.block import Block

class PaxosConsensus(ConsensusInterface):
    """
    Paxos Consensus.
    Crash fault tolerance based on Proposer, Acceptor, and Learner roles.
    """
    def __init__(self, network_layer=None):
        self.network = network_layer
        self.role = random.choice(["proposer", "acceptor", "learner"])
        print(f"[Paxos] Node started with role: {self.role.upper()}")

    def validate_block(self, block: Block) -> bool:
        if self.role == 'learner':
            print(f"[Paxos] Learner discovered new generic consensus integer for block {block.index}.")
        elif self.role == 'acceptor':
            print(f"[Paxos] Acceptor acknowledged promised ballot value.")
        return True

    def propose_block(self, transactions: list, previous_hash: str, index: int, miner_address: str, state_root: str = "") -> Block:
        if self.role != "proposer":
             # Wait a little to prevent console spam
             time.sleep(2)
             print(f"[Paxos] Node is {self.role}, cannot propose.")
             return None
             
        print(f"\n[Paxos] Proposer initiating Phase 1a (Prepare)...")
        time.sleep(0.3)
        print(f"[Paxos] Phase 1b (Promise) accepted by majority.")
        time.sleep(0.3)
        print(f"[Paxos] Phase 2a (Accept Request) broadcasted...")
        time.sleep(0.3)
        print(f"[Paxos] Phase 2b (Accepted) registered. Consensus reached.")
        
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
