"""
PBFT (Practical Byzantine Fault Tolerance) Consensus Adapter Stub
"""

try:
    from chain_adapter import IChainAdapter, NodeProcess, Transaction, Block, ConsensusState, ChainEvent
except ImportError:
    from ..chain_adapter import IChainAdapter, NodeProcess, Transaction, Block, ConsensusState, ChainEvent
from typing import Callable, List


class PBFTAdapter(IChainAdapter):
    """
    PBFT (Practical Byzantine Fault Tolerance) adapter implementation.
    Three-phase consensus: Pre-Prepare, Prepare, Commit.
    Tolerates f <= (n-1)/3 faulty nodes.
    """

    async def spawn_node(self, role: str, port: int) -> NodeProcess:
        """
        Spawn a PBFT replica node.
        One replica is designated as primary for the round.
        """
        # TODO: Implement PBFT-specific node spawning
        pass

    async def terminate_node(self, node_id: str) -> None:
        """
        Terminate a PBFT replica node.
        May trigger view change if primary is terminated.
        """
        # TODO: Implement node termination logic
        pass

    async def submit_transaction(self, tx: Transaction) -> str:
        """
        Submit transaction to primary replica's mempool.
        """
        # TODO: Implement transaction submission
        pass

    async def get_blocks(self, since: int) -> List[Block]:
        """
        Retrieve blocks from PBFT chain since given height.
        """
        # TODO: Implement block retrieval
        pass

    async def get_consensus_state(self) -> ConsensusState:
        """
        Return current PBFT state: current phase, round, primary replica, fault tolerance.
        """
        # TODO: Implement consensus state retrieval
        pass

    def subscribe_to_events(self, handler: Callable[[ChainEvent], None]) -> None:
        """
        Subscribe to PBFT-specific events: PRE_PREPARE, PREPARE, COMMIT, VIEW_CHANGE.
        """
        # TODO: Implement event subscription
        pass
