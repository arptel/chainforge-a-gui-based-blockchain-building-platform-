"""
PoA (Proof of Authority) Consensus Adapter Stub
"""

try:
    from chain_adapter import IChainAdapter, NodeProcess, Transaction, Block, ConsensusState, ChainEvent
except ImportError:
    from ..chain_adapter import IChainAdapter, NodeProcess, Transaction, Block, ConsensusState, ChainEvent
from typing import Callable, List


class PoAAdapter(IChainAdapter):
    """
    Proof of Authority adapter implementation.
    Pre-approved authority nodes validate blocks sequentially.
    """

    async def spawn_node(self, role: str, port: int) -> NodeProcess:
        """
        Spawn a PoA node (authority or regular node).
        Only authority nodes can propose/validate blocks.
        """
        # TODO: Implement PoA-specific node spawning
        pass

    async def terminate_node(self, node_id: str) -> None:
        """
        Terminate a PoA node process.
        """
        # TODO: Implement node termination logic
        pass

    async def submit_transaction(self, tx: Transaction) -> str:
        """
        Submit transaction to mempool.
        Only authority nodes can include transactions in blocks.
        """
        # TODO: Implement transaction submission
        pass

    async def get_blocks(self, since: int) -> List[Block]:
        """
        Retrieve blocks from PoA chain since given height.
        """
        # TODO: Implement block retrieval
        pass

    async def get_consensus_state(self) -> ConsensusState:
        """
        Return current PoA state: authority node list, pending approvals.
        """
        # TODO: Implement consensus state retrieval
        pass

    def subscribe_to_events(self, handler: Callable[[ChainEvent], None]) -> None:
        """
        Subscribe to PoA-specific events: AUTHORITY_STAMP, BLOCK_APPROVED, BLOCK_FINALIZED.
        """
        # TODO: Implement event subscription
        pass
