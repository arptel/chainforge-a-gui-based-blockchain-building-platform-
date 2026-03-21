"""
Adapter factory and exports
"""

from .pow_adapter import PoWAdapter
from .pos_adapter import PoSAdapter
from .poa_adapter import PoAAdapter
from .pbft_adapter import PBFTAdapter
from .raft_adapter import RaftAdapter
from .tendermint_adapter import TendermintAdapter
from .hotstuff_adapter import HotStuffAdapter
from .paxos_adapter import PaxosAdapter
from .none_adapter import NoneAdapter

CONSENSUS_ADAPTERS = {
    'pow': PoWAdapter,
    'pos': PoSAdapter,
    'poa': PoAAdapter,
    'pbft': PBFTAdapter,
    'raft': RaftAdapter,
    'tendermint': TendermintAdapter,
    'hotstuff': HotStuffAdapter,
    'paxos': PaxosAdapter,
    'none': NoneAdapter,
}

def get_adapter(consensus_type: str):
    """Get the appropriate adapter class for the given consensus type."""
    adapter_class = CONSENSUS_ADAPTERS.get(consensus_type.lower())
    if not adapter_class:
        raise ValueError(f"Unknown consensus type: {consensus_type}")
    return adapter_class()

__all__ = [
    'PoWAdapter',
    'PoSAdapter',
    'PoAAdapter',
    'PBFTAdapter',
    'RaftAdapter',
    'TendermintAdapter',
    'HotStuffAdapter',
    'PaxosAdapter',
    'NoneAdapter',
    'get_adapter',
    'CONSENSUS_ADAPTERS',
]
