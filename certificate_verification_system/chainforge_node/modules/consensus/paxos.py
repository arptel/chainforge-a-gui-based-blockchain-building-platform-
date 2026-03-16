"""
modules/consensus/paxos.py

Paxos Consensus Protocol Implementation.
Modified for Blockchain: Use a 2-phase proposal system to reach agreement 
on the next block in the sequence. 

1. Prepare: Proposer sends a ballot number (n) to nodes.
2. Promise: Nodes promise not to accept lower ballots.
3. Accept: Proposer sends the block value for consensus.
4. Accepted: Nodes acknowledge the block.
"""
import time
from typing import Dict, Any, List, Optional
try:
    from interfaces.consensus import ConsensusInterface
    from core.block import Block
except ImportError:
    from chainforge.templates.chain_core.interfaces.consensus import ConsensusInterface
    from chainforge.templates.chain_core.core.block import Block

class PaxosConsensus(ConsensusInterface):
    def __init__(self, node_id: str, peers: List[str] = None):
        self.node_id = node_id
        self.peers = peers or []
        self.majority = (len(self.peers) // 2) + 1
        
        # State
        self.current_ballot = 0
        self.promised_ballot = 0
        self.accepted_ballot = 0
        self.accepted_value = None
        
        # Vote counters
        self.promises: Dict[int, set] = {} # ballot -> {voters}
        self.accepted_votes: Dict[int, set] = {} # ballot -> {voters}
        
        self.network = None

    def propose_block(self, transactions: list, previous_hash: str, index: int, miner_address: str, state_root: str = "") -> Optional[Block]:
        """Proposer phase 1: Send Prepare."""
        self.current_ballot += 1
        print(f"[Paxos] Node {self.node_id} initiating Paxos for block {index}, Ballot {self.current_ballot}")
        
        self.temp_block = Block(
            index=index,
            transactions=transactions,
            timestamp=time.time(),
            previous_hash=previous_hash,
            validator=miner_address,
            state_root=state_root
        )
        
        msg = {
            "type": "PAXOS_PREPARE",
            "ballot": self.current_ballot,
            "sequence": index,
            "sender": self.node_id
        }
        
        if self.network:
            self.network.broadcast(msg)
        else:
            return self.temp_block # Single node fallback
            
        return self.temp_block

    def validate_block(self, block: Block) -> bool:
        """Verify Paxos majority consensus reached."""
        if block.index == 0: return True
        
        # Successful consensus means we have an accepted value with a majority
        if not self.peers: return True
        
        votes = self.accepted_votes.get(self.current_ballot, set())
        if len(votes) >= self.majority:
            return True
            
        return False

    def handle_consensus_message(self, msg: Dict[str, Any]):
        msg_type = msg.get("type")
        if msg_type == "PAXOS_PREPARE":
            self._handle_prepare(msg)
        elif msg_type == "PAXOS_PROMISE":
            self._handle_promise(msg)
        elif msg_type == "PAXOS_ACCEPT":
            self._handle_accept(msg)
        elif msg_type == "PAXOS_ACCEPTED":
            self._handle_accepted(msg)

    def _handle_prepare(self, msg):
        ballot = msg["ballot"]
        sender = msg["sender"]
        
        if ballot > self.promised_ballot:
            self.promised_ballot = ballot
            promise_msg = {
                "type": "PAXOS_PROMISE",
                "ballot": ballot,
                "prev_accepted_ballot": self.accepted_ballot,
                "prev_accepted_value": self.accepted_value if self.accepted_value else None,
                "sender": self.node_id
            }
            if self.network:
                self.network.broadcast(promise_msg)

    def _handle_promise(self, msg):
        ballot = msg["ballot"]
        sender = msg["sender"]
        
        if ballot not in self.promises: self.promises[ballot] = set()
        self.promises[ballot].add(sender)
        
        if len(self.promises[ballot]) >= self.majority:
            # Phase 2: Accept
            accept_msg = {
                "type": "PAXOS_ACCEPT",
                "ballot": ballot,
                "value": self.temp_block.to_dict(),
                "sender": self.node_id
            }
            if self.network:
                self.network.broadcast(accept_msg)

    def _handle_accept(self, msg):
        ballot = msg["ballot"]
        value = msg["value"]
        sender = msg["sender"]
        
        if ballot >= self.promised_ballot:
            self.promised_ballot = ballot
            self.accepted_ballot = ballot
            self.accepted_value = value
            
            accepted_msg = {
                "type": "PAXOS_ACCEPTED",
                "ballot": ballot,
                "sender": self.node_id
            }
            if self.network:
                self.network.broadcast(accepted_msg)

    def _handle_accepted(self, msg):
        ballot = msg["ballot"]
        sender = msg["sender"]
        
        if ballot not in self.accepted_votes: self.accepted_votes[ballot] = set()
        self.accepted_votes[ballot].add(sender)
        
        if len(self.accepted_votes[ballot]) >= self.majority:
            print(f"[Paxos] Consensus reached for ballot {ballot}")
