"""
Tendermint Consensus Adapter Stub
"""

try:
    from chain_adapter import IChainAdapter, NodeProcess, Transaction, Block, ConsensusState, ChainEvent
except ImportError:
    from ..chain_adapter import IChainAdapter, NodeProcess, Transaction, Block, ConsensusState, ChainEvent
from typing import Callable, List


class TendermintAdapter(IChainAdapter):
    """
    Tendermint consensus adapter implementation.
    Four-phase BFT: Propose, Prevote, Precommit, Commit.
    Round-based with deterministic proposer rotation.
    """

    async def spawn_node(self, role: str, port: int) -> NodeProcess:
        """
        Spawn a Tendermint validator node.
        """
        # TODO: Implement Tendermint-specific node spawning
        pass

    async def terminate_node(self, node_id: str) -> None:
        """
        Terminate a Tendermint validator node.
        """
        # TODO: Implement node termination logic
        pass

    async def submit_transaction(self, tx: Transaction) -> str:
        """
        Submit transaction to mempool.
        Will be included by current proposer.
        """
        # TODO: Implement transaction submission
        pass

    async def get_blocks(self, since: int) -> List[Block]:
        """
        Retrieve blocks from Tendermint chain since given height.
        """
        # TODO: Implement block retrieval
        pass

    async def get_consensus_state(self) -> ConsensusState:
        """
        Return current Tendermint state: height, round, proposer, phase, vote counts.
        """
        # TODO: Implement consensus state retrieval
        pass

    def subscribe_to_events(self, handler: Callable[[ChainEvent], None]) -> None:
        """
        Subscribe to Tendermint-specific events: PROPOSE, PREVOTE, PRECOMMIT, COMMIT, ROUND_TIMEOUT.
        """
        # TODO: Implement event subscription
        pass
