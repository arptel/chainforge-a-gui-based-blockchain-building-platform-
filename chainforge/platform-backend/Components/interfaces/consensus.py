from abc import ABC, abstractmethod
from typing import Any, Dict

class ConsensusInterface(ABC):
    """
    Interface for consensus algorithms.
    """

    @abstractmethod
    def propose_block(self, transactions: list[Dict[str, Any]], previous_hash: str, index: int, miner_address: str, state_root: str = "") -> Any:
        """
        Propose a new block to the network.
        """
        pass

    @abstractmethod
    def validate_block(self, block: Any) -> bool:
        """
        Validate a proposed block.
        """
        pass

    @abstractmethod
    def commit_block(self, block: Any) -> bool:
        """
        Commit the block to the local chain.
        """
        pass
