"""
IChainAdapter Interface - Core abstraction for all consensus types.
Each consensus adapter must implement all methods with exact signatures.
"""

from abc import ABC, abstractmethod
from typing import Optional, Callable, Dict, Any, List, Tuple
from dataclasses import dataclass


@dataclass
class NodeProcess:
    """Represents a spawned blockchain node process."""
    node_id: str
    role: str
    port: int
    pid: Optional[int] = None
    status: str = "initializing"  # initializing, ready, offline, stopped


@dataclass
class Transaction:
    """Represents a blockchain transaction."""
    tx_hash: str
    from_address: str
    to_address: str
    amount: float
    memo: str = ""
    timestamp: int = 0


@dataclass
class Block:
    """Represents a committed blockchain block."""
    block_number: int
    block_hash: str
    proposer: str
    transactions: List[Transaction]
    timestamp: int
    votes_received: Dict[str, bool] = None
    tx_count: int = 0


@dataclass
class ConsensusState:
    """Current consensus state and phase information."""
    consensus_type: str
    current_round: int
    current_phase: str  # propose, prevote, precommit, prepare, commit, etc.
    current_leader: Optional[str]
    validator_count: int
    faulty_nodes: int
    ready_validators: List[str]
    pending_votes: Dict[str, bool]


@dataclass
class ChainEvent:
    """Envelope for all chain events pushed to frontend."""
    event_type: str  # NODE_JOINED, BLOCK_COMMITTED, VOTE_CAST, CONSENSUS_PHASE, etc.
    timestamp: int
    node_id: str
    payload: Dict[str, Any]


class IChainAdapter(ABC):
    """
    Abstract base class for all consensus type adapters.
    
    Each adapter (PoW, PoS, PoA, PBFT, Raft, Tendermint, HotStuff, Paxos, None)
    must implement these methods with their consensus-specific logic.
    """

    @abstractmethod
    async def spawn_node(self, role: str, port: int) -> NodeProcess:
        """
        Spawn a real blockchain node process with the specified role.
        
        Args:
            role: Node role (full, validator, light, etc.) from config.yaml
            port: Port number to assign
            
        Returns:
            NodeProcess with initialized node_id, role, port, and status
            
        Raises:
            RuntimeError: If node process fails to spawn or acquire ready signal
        """
        pass

    @abstractmethod
    async def terminate_node(self, node_id: str) -> None:
        """
        Terminate a running blockchain node process.
        
        Args:
            node_id: Unique identifier of the node to terminate
            
        Raises:
            ValueError: If node_id not found or already terminated
            RuntimeError: If process termination fails
        """
        pass

    @abstractmethod
    async def submit_transaction(self, tx: Transaction, from_node_id: str = None) -> str:
        """
        Submit a transaction to the blockchain.
        
        Args:
            tx: Transaction object with addresses, amount, and memo
            
        Returns:
            Transaction hash (string)
            
        Raises:
            RuntimeError: If transaction submission fails (mempool full, invalid, etc.)
        """
        pass

    @abstractmethod
    async def get_blocks(self, since: int) -> List[Block]:
        """
        Retrieve committed blocks since a given block number.
        
        Args:
            since: Block number to start from (inclusive)
            
        Returns:
            List of Block objects in order
        """
        pass

    @abstractmethod
    async def get_consensus_state(self) -> ConsensusState:
        """
        Get current consensus state, phase, and node status.
        
        Returns:
            ConsensusState object with current round, phase, leader, validator info
        """
        pass

    @abstractmethod
    def subscribe_to_events(self, handler: Callable[[ChainEvent], None]) -> None:
        """
        Subscribe to chain events (block commits, votes, consensus phases, sync progress).
        
        Args:
            handler: Callback function that receives ChainEvent objects
        """
        pass
