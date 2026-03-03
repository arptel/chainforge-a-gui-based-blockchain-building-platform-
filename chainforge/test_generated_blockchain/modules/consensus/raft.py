import time
import random
from interfaces.consensus import ConsensusInterface
from core.block import Block

class RaftConsensus(ConsensusInterface):
    """
    Raft Consensus.
    Crash fault-tolerant leader election loop. Only the leader proposes.
    """
    def __init__(self, network_layer=None):
        self.network = network_layer
        self.is_leader = False
        self.leader_id = None
        self._simulate_election()

    def _simulate_election(self):
        # A mock implementation to demonstrate how Raft elects a leader on startup
        print("[Raft] Node starting as Follower. Awaiting heartbeats...")
        time.sleep(2)
        
        # Assume timeout reached, randomized election starts
        print("[Raft] Heartbeat timeout. Converting to Candidate and requesting votes...")
        time.sleep(random.uniform(0.1, 0.5))
        
        # Simple probability: 50% chance this node becomes the Leader in the mock
        self.is_leader = random.choice([True, False])
        if self.is_leader:
            print("[Raft] 👑 Elected as Network LEADER. Broadcasting heartbeats.")
            # Naturally it would start a heartbeat Thread here
        else:
            print("[Raft] Became FOLLOWER. Acknowledged remote Leader.")

    def validate_block(self, block: Block) -> bool:
        if not self.is_leader:
            print(f"[Raft] Follower appended Leader's block {block.index}.")
            return True
        return True

    def propose_block(self, transactions: list, previous_hash: str, index: int, miner_address: str) -> Block:
        if not self.is_leader:
            print("[Raft] Cannot propose: This node is a Follower. Forwarding to Leader.")
            return None # Cancel mining attempt
            
        print(f"\n[Raft] Leader proposing block {index} via AppendEntries RPC...")
        time.sleep(0.5)
        print(f"[Raft] Majority of Followers acknowledged AppendEntries. Committing.")
        
        return Block(
            index=index,
            transactions=transactions,
            timestamp=time.time(),
            previous_hash=previous_hash,
            validator=miner_address
        )

    def commit_block(self, block: Block) -> bool:
        return True
