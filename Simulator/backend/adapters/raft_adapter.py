"""
Raft Consensus Adapter Stub
"""

try:
    from chain_adapter import IChainAdapter, NodeProcess, Transaction, Block, ConsensusState, ChainEvent
except ImportError:
    from ..chain_adapter import IChainAdapter, NodeProcess, Transaction, Block, ConsensusState, ChainEvent
from typing import Callable, List


class RaftAdapter(IChainAdapter):
    """
    Raft consensus adapter implementation.
    Leader-based consensus with log replication and elections.
    """

    async def spawn_node(self, role: str, port: int) -> NodeProcess:
        """
        Spawn a Raft node (leader or follower).
        All nodes start as followers and participate in elections.
        """
        # TODO: Implement Raft-specific node spawning
        pass

    async def terminate_node(self, node_id: str) -> None:
        """
        Terminate a Raft node process.
        If leader is terminated, triggers election.
        """
        # TODO: Implement node termination logic
        pass

    async def submit_transaction(self, tx: Transaction) -> str:
        """
        Submit transaction to leader's log.
        Followers redirect to leader.
        """
        # TODO: Implement transaction submission
        pass

    async def get_blocks(self, since: int) -> List[Block]:
        """
        Retrieve committed blocks from Raft log since given height.
        """
        # TODO: Implement block retrieval
        pass

    async def get_consensus_state(self) -> ConsensusState:
        """
        Return current Raft state: term, leader ID, log height, replication progress.
        """
        # TODO: Implement consensus state retrieval
        pass

    def subscribe_to_events(self, handler: Callable[[ChainEvent], None]) -> None:
        """
        Subscribe to Raft-specific events: HEARTBEAT, APPEND_ENTRIES, ELECTION, COMMIT.
        """
        # TODO: Implement event subscription
        pass
