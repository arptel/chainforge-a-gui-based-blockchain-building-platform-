"""
modules/consensus/hotstuff.py

HotStuff Consensus Implementation (Simplified 4-phase Pipelined BFT).
Provides Linear Communication Complexity and Optimistic Responsiveness.

Phases: Prepare → Pre-commit → Commit → Decide
Each phase requires a +2/3 Quorum Certificate (QC).
"""
import time
from typing import Dict, Any, List, Optional, Set
import sys
import os

try:
    from interfaces.consensus import ConsensusInterface  # type: ignore
    from core.block import Block  # type: ignore
except ImportError:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
    from interfaces.consensus import ConsensusInterface  # type: ignore
    from core.block import Block  # type: ignore

class HotStuffConsensus(ConsensusInterface):
    def __init__(self, node_id: str, peers: Optional[List[str]] = None):
        self.node_id = node_id
        self.peers = peers or []
        self.quorum = (len(self.peers) * 2 // 3) + 1
        
        # State
        self.view = 0
        self.high_qc = None
        self.locked_block = None
        
        # In-memory vote storage: view -> phase -> {block_hash: {voters}}
        self.votes: Dict[int, Dict[str, Dict[str, Set[str]]]] = {}
        
        self.network: Any = None

    def propose_block(self, transactions: list, previous_hash: str, index: int, miner_address: str, state_root: str = "") -> Optional[Block]:
        """Leader: Advance view and broadcast block with High QC."""
        self.view += 1
        print(f"[HotStuff] Node {self.node_id} Leader for View {self.view}")
        
        block = Block(
            index=index,
            transactions=transactions,
            timestamp=time.time(),
            previous_hash=previous_hash,
            validator=miner_address,
            state_root=state_root
        )
        
        msg = {
            "type": "HOTSTUFF_PREPARE",
            "view": self.view,
            "block": block.to_dict(),
            "high_qc": self.high_qc,
            "sender": self.node_id
        }
        
        if self.network:
            self.network.broadcast(msg)
        else:
            return block
            
        return block

    def validate_block(self, block: Block) -> bool:
        """Verify HotStuff Decide quorum (+2/3 support)."""
        if block.index == 0: return True
        if not self.peers: return True
        
        b_hash = block.hash
        # In a DECIDE phase, we check if enough nodes reached the last stage
        votes_dict = self.votes.get(self.view, {}).get("COMMIT", {}).get(b_hash, set())
        if len(votes_dict) >= self.quorum:
            return True
            
        return False

    def handle_consensus_message(self, msg: Dict[str, Any]):
        try:
            v: int = int(str(msg.get("view", "-1")))
        except (ValueError, TypeError):
            return
            
        msg_type = msg.get("type")
        
        if v < 0:
            return
        
        if v not in self.votes: self.votes[v] = {"PREPARE": {}, "PRE_COMMIT": {}, "COMMIT": {}, "DECIDE": {}}
        
        if msg_type == "HOTSTUFF_PREPARE":
            self._handle_prepare(msg)
        elif msg_type == "HOTSTUFF_VOTE":
            self._handle_vote(msg)

    def _handle_prepare(self, msg):
        v, sender = msg["view"], msg["sender"]
        b_data = msg["block"]
        b_hash = Block.from_dict(b_data).hash
        
        print(f"[HotStuff] Received Prepare for View {v} from {sender}")
        
        # Broadcast vote for this phase
        vote_msg = {
            "type": "HOTSTUFF_VOTE",
            "view": v,
            "phase": "PREPARE",
            "block_hash": b_hash,
            "sender": self.node_id
        }
        if self.network:
            self.network.broadcast(vote_msg)

    def _handle_vote(self, msg):
        v, phase, sender = msg["view"], msg["phase"], msg["sender"]
        b_hash = msg["block_hash"]
        
        p_votes = self.votes[v][phase]
        if b_hash not in p_votes: p_votes[b_hash] = set()
        p_votes[b_hash].add(sender)
        
        if len(p_votes[b_hash]) >= self.quorum:
            # Advance to next phase (simulated pipeline)
            next_phases = {"PREPARE": "PRE_COMMIT", "PRE_COMMIT": "COMMIT", "COMMIT": "DECIDE"}
            next_phase = next_phases.get(phase)
            
            if next_phase:
                print(f"[HotStuff] Phase {phase} Quorum met, advancing to {next_phase}")
                adv_msg = {
                    "type": "HOTSTUFF_VOTE",
                    "view": v,
                    "phase": next_phase,
                    "block_hash": b_hash,
                    "sender": self.node_id
                }
                if self.network:
                    self.network.broadcast(adv_msg)
            elif phase == "DECIDE":
                print(f"[HotStuff] Decisions met for View {v}!")
                self.high_qc = b_hash
