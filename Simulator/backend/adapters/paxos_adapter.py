"""
Paxos Consensus Adapter Stub
"""

try:
    from chain_adapter import IChainAdapter, NodeProcess, Transaction, Block, ConsensusState, ChainEvent
except ImportError:
    from ..chain_adapter import IChainAdapter, NodeProcess, Transaction, Block, ConsensusState, ChainEvent
from typing import Callable, List


class PaxosAdapter(IChainAdapter):
    """
    Paxos consensus adapter implementation.
    Two-phase: Prepare (Phase 1) and Accept (Phase 2).
    Reaches consensus on a single value per round.
    """

    async def spawn_node(self, role: str, port: int) -> NodeProcess:
        """
        Spawn a Paxos node (proposer, acceptor, or learner).
        """
        # TODO: Implement Paxos-specific node spawning
        pass

    async def terminate_node(self, node_id: str) -> None:
        """
        Terminate a Paxos node process.
        """
        # TODO: Implement node termination logic
        pass

    async def submit_transaction(self, tx: Transaction) -> str:
        """
        Submit transaction value to current proposer.
        Proposer will attempt to reach consensus on this value.
        """
        # TODO: Implement transaction submission
        pass

    async def get_blocks(self, since: int) -> List[Block]:
        """
        Retrieve blocks (consensus rounds results) from Paxos chain since given height.
        """
        # TODO: Implement block retrieval
        pass

    async def get_consensus_state(self) -> ConsensusState:
        """
        Return current Paxos state: proposal number, phase, acceptor promises, accepted values.
        """
        # TODO: Implement consensus state retrieval
        pass

    def subscribe_to_events(self, handler: Callable[[ChainEvent], None]) -> None:
        """
        Subscribe to Paxos-specific events: PREPARE, PROMISE, ACCEPT, ACCEPTED, LEARNED.
        """
        # TODO: Implement event subscription
        pass
