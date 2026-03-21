"""
HotStuff Consensus Adapter Stub
"""

try:
    from chain_adapter import IChainAdapter, NodeProcess, Transaction, Block, ConsensusState, ChainEvent
except ImportError:
    from ..chain_adapter import IChainAdapter, NodeProcess, Transaction, Block, ConsensusState, ChainEvent
from typing import Callable, List


class HotStuffAdapter(IChainAdapter):
    """
    HotStuff consensus adapter implementation.
    Linear BFT with pipelined phases: Prepare, Pre-Commit, Commit.
    Optimized for high throughput and low latency.
    """

    async def spawn_node(self, role: str, port: int) -> NodeProcess:
        """
        Spawn a HotStuff replica node.
        One replica serves as leader for the view.
        """
        # TODO: Implement HotStuff-specific node spawning
        pass

    async def terminate_node(self, node_id: str) -> None:
        """
        Terminate a HotStuff replica node.
        May trigger leader rotation if active leader is terminated.
        """
        # TODO: Implement node termination logic
        pass

    async def submit_transaction(self, tx: Transaction) -> str:
        """
        Submit transaction to leader's block proposal.
        """
        # TODO: Implement transaction submission
        pass

    async def get_blocks(self, since: int) -> List[Block]:
        """
        Retrieve blocks from HotStuff chain since given height.
        """
        # TODO: Implement block retrieval
        pass

    async def get_consensus_state(self) -> ConsensusState:
        """
        Return current HotStuff state: view, phase, leader, QC (Quorum Certificate) status.
        """
        # TODO: Implement consensus state retrieval
        pass

    def subscribe_to_events(self, handler: Callable[[ChainEvent], None]) -> None:
        """
        Subscribe to HotStuff-specific events: PREPARE, PRE_COMMIT, COMMIT, QC_FORMED, LEADER_CHANGED.
        """
        # TODO: Implement event subscription
        pass
