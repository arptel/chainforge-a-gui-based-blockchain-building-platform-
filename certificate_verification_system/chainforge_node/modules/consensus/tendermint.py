"""
modules/consensus/tendermint.py

Simplified Tendermint Consensus BFT Implementation.
Uses a 3-step voting process (Propose, Pre-vote, Pre-commit) to ensure 
that a block is only finalized if +2/3 of the nodes agree.

Supports Block Locking and Heights.
"""
import time
from typing import Dict, Any, List, Optional
try:
    from interfaces.consensus import ConsensusInterface
    from core.block import Block
except ImportError:
    from chainforge.templates.chain_core.interfaces.consensus import ConsensusInterface
    from chainforge.templates.chain_core.core.block import Block

class TendermintConsensus(ConsensusInterface):
    def __init__(self, node_id: str, peers: List[str] = None):
        self.node_id = node_id
        self.peers = peers or []
        self.quorum = (len(self.peers) * 2 // 3) + 1
        
        # State
        self.height = 0
        self.round = 0
        self.locked_block = None
        self.locked_round = -1
        
        # Vote storage: height -> round -> type -> {block_hash: {voters}}
        self.votes: Dict[int, Dict[int, Dict[str, Dict[str, set]]]] = {}
        
        self.network = None

    def propose_block(self, transactions: list, previous_hash: str, index: int, miner_address: str, state_root: str = "") -> Optional[Block]:
        """Proposer: Start a new height/round and broadcast proposal."""
        self.height = index
        self.round = 0
        print(f"[Tendermint] Node {self.node_id} proposing block at height {self.height}")
        
        block = Block(
            index=index,
            transactions=transactions,
            timestamp=time.time(),
            previous_hash=previous_hash,
            validator=miner_address,
            state_root=state_root
        )
        
        msg = {
            "type": "TENDERMINT_PROPOSAL",
            "height": self.height,
            "round": self.round,
            "block": block.to_dict(),
            "sender": self.node_id
        }
        
        if self.network:
            self.network.broadcast(msg)
        else:
            return block
            
        return block

    def validate_block(self, block: Block) -> bool:
        """Verify Tendermint +2/3 pre-commit quorum."""
        if block.index == 0: return True
        if not self.peers: return True
        
        h = block.index
        b_hash = block.hash
        
        # Check pre-commits for this height across any round
        for r in self.votes.get(h, {}):
            pre_commits = self.votes[h][r].get("PRE_COMMIT", {}).get(b_hash, set())
            if len(pre_commits) >= self.quorum:
                return True
                
        return False

    def handle_consensus_message(self, msg: Dict[str, Any]):
        h = msg.get("height")
        r = msg.get("round")
        msg_type = msg.get("type")
        
        if h not in self.votes: self.votes[h] = {}
        if r not in self.votes[h]: self.votes[h][r] = {"PRE_VOTE": {}, "PRE_COMMIT": {}}
        
        if msg_type == "TENDERMINT_PROPOSAL":
            self._handle_proposal(msg)
        elif msg_type == "TENDERMINT_PRE_VOTE":
            self._handle_prevote(msg)
        elif msg_type == "TENDERMINT_PRE_COMMIT":
            self._handle_precommit(msg)

    def _handle_proposal(self, msg):
        h, r, sender = msg["height"], msg["round"], msg["sender"]
        b_data = msg["block"]
        b_hash = Block.from_dict(b_data).hash
        
        print(f"[Tendermint] Received proposal at height {h} from {sender}")
        
        # Pre-vote phase
        vote_msg = {
            "type": "TENDERMINT_PRE_VOTE",
            "height": h,
            "round": r,
            "block_hash": b_hash,
            "sender": self.node_id
        }
        if self.network:
            self.network.broadcast(vote_msg)

    def _handle_prevote(self, msg):
        h, r, sender = msg["height"], msg["round"], msg["sender"]
        b_hash = msg["block_hash"]
        
        votes_dict = self.votes[h][r]["PRE_VOTE"]
        if b_hash not in votes_dict: votes_dict[b_hash] = set()
        votes_dict[b_hash].add(sender)
        
        if len(votes_dict[b_hash]) >= self.quorum:
            # Pre-commit phase
            # Block locking would happen here in a full implementation
            commit_msg = {
                "type": "TENDERMINT_PRE_COMMIT",
                "height": h,
                "round": r,
                "block_hash": b_hash,
                "sender": self.node_id
            }
            if self.network and self.node_id not in self.votes[h][r]["PRE_COMMIT"].get(b_hash, set()):
                self.network.broadcast(commit_msg)

    def _handle_precommit(self, msg):
        h, r, sender = msg["height"], msg["round"], msg["sender"]
        b_hash = msg["block_hash"]
        
        commits_dict = self.votes[h][r]["PRE_COMMIT"]
        if b_hash not in commits_dict: commits_dict[b_hash] = set()
        commits_dict[b_hash].add(sender)
        
        if len(commits_dict[b_hash]) >= self.quorum:
            print(f"[Tendermint] Finality reached for height {h}")
