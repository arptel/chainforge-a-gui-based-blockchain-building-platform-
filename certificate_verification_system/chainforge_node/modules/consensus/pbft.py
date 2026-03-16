"""
modules/consensus/pbft.py

Practical Byzantine Fault Tolerance (PBFT) Consensus Implementation.
This module implements a real 3-phase consensus protocol:
1. Pre-Prepare: Leader broadcasts a block proposal.
2. Prepare: Nodes acknowledge the proposal and broadcast their preparation.
3. Commit: Nodes wait for a 2f+1 quorum of prepares, then broadcast a commit.

Requires P2P network layer for message broadcasting and vote counting.
"""
import time
import json
from typing import Dict, Any, List, Optional
try:
    from interfaces.consensus import ConsensusInterface
    from core.block import Block
except ImportError:
    from chainforge.templates.chain_core.interfaces.consensus import ConsensusInterface
    from chainforge.templates.chain_core.core.block import Block

class PBFTConsensus(ConsensusInterface):
    def __init__(self, node_id: str, peers: List[str] = None):
        self.node_id = node_id
        self.peers = peers or []
        self.f = len(self.peers) // 3
        self.quorum = 2 * self.f + 1
        
        # State tracking
        self.pre_prepares: Dict[int, Dict[str, Any]] = {}  # sequence -> message
        self.prepares: Dict[int, Dict[str, set]] = {}      # sequence -> {block_hash: {voters}}
        self.commits: Dict[int, Dict[str, set]] = {}       # sequence -> {block_hash: {voters}}
        self.committed_blocks: Dict[int, str] = {}         # sequence -> block_hash
        
        self.network = None # Will be set by set_consensus_module

    def propose_block(self, transactions: list, previous_hash: str, index: int, miner_address: str, state_root: str = "") -> Optional[Block]:
        """Leader phase: Create and broadcast a PRE-PREPARE message."""
        print(f"[PBFT] Node {self.node_id} proposing block {index}")
        
        block = Block(
            index=index,
            transactions=transactions,
            timestamp=time.time(),
            previous_hash=previous_hash,
            validator=miner_address,
            state_root=state_root
        )
        
        # Broadcast Pre-Prepare
        msg = {
            "type": "PBFT_PRE_PREPARE",
            "view": 0,
            "sequence": index,
            "block": block.to_dict(),
            "sender": self.node_id
        }
        
        if self.network:
            print(f"[PBFT] Broadcasting PRE-PREPARE for block {index}")
            self.network.broadcast(msg)
        else:
            print("[PBFT] Warning: Network layer not attached. Fallback to single-node mode.")
            return block
            
        return block

    def validate_block(self, block: Block) -> bool:
        """Verify PBFT consensus reached for this block."""
        # In this implementation, we check if we have a commit quorum for this sequence/hash
        seq = block.index
        if seq == 0: return True # Genesis
        
        block_hash = block.hash
        commit_voters = self.commits.get(seq, {}).get(block_hash, set())
        
        if len(commit_voters) >= self.quorum:
            return True
        
        # If no peers, we allow local mining
        if not self.peers:
            return True
            
        print(f"[PBFT] Validation failed: Quorum not met for block {seq} (votes: {len(commit_voters)}/{self.quorum})")
        return False

    def handle_consensus_message(self, msg: Dict[str, Any]):
        """Route incoming PBFT messages."""
        msg_type = msg.get("type")
        seq = msg.get("sequence")
        sender = msg.get("sender")
        
        if msg_type == "PBFT_PRE_PREPARE":
            self._handle_pre_prepare(msg)
        elif msg_type == "PBFT_PREPARE":
            self._handle_prepare(msg)
        elif msg_type == "PBFT_COMMIT":
            self._handle_commit(msg)

    def _handle_pre_prepare(self, msg):
        seq = msg["sequence"]
        block_data = msg["block"]
        block_hash = Block.from_dict(block_data).hash
        
        print(f"[PBFT] Received PRE-PREPARE from {msg['sender']} for block {seq}")
        self.pre_prepares[seq] = msg
        
        # Broadcast Prepare
        prepare_msg = {
            "type": "PBFT_PREPARE",
            "view": 0,
            "sequence": seq,
            "block_hash": block_hash,
            "sender": self.node_id
        }
        if self.network:
            self.network.broadcast(prepare_msg)

    def _handle_prepare(self, msg):
        seq = msg["sequence"]
        b_hash = msg["block_hash"]
        sender = msg["sender"]
        
        print(f"[PBFT] Received PREPARE from {sender} for block {seq}")
        
        if seq not in self.prepares: self.prepares[seq] = {}
        if b_hash not in self.prepares[seq]: self.prepares[seq][b_hash] = set()
        
        self.prepares[seq][b_hash].add(sender)
        
        # If we reached prepare quorum, broadcast Commit
        if len(self.prepares[seq][b_hash]) >= self.quorum:
            commit_msg = {
                "type": "PBFT_COMMIT",
                "view": 0,
                "sequence": seq,
                "block_hash": b_hash,
                "sender": self.node_id
            }
            if self.network:
                # Only broadcast commit once per sequence
                if self.node_id not in self.commits.get(seq, {}).get(b_hash, set()):
                    self.network.broadcast(commit_msg)

    def _handle_commit(self, msg):
        seq = msg["sequence"]
        b_hash = msg["block_hash"]
        sender = msg["sender"]
        
        print(f"[PBFT] Received COMMIT from {sender} for block {seq}")
        
        if seq not in self.commits: self.commits[seq] = {}
        if b_hash not in self.commits[seq]: self.commits[seq][b_hash] = set()
        
        self.commits[seq][b_hash].add(sender)
        
        if len(self.commits[seq][b_hash]) >= self.quorum:
            print(f"[PBFT] Quorum reached for block {seq}!")
            self.committed_blocks[seq] = b_hash
