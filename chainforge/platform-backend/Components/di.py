from typing import Dict, Any, Type
from .interfaces.consensus import ConsensusInterface
from .interfaces.network import NetworkInterface
from .interfaces.sync import SyncInterface
from .modules.consensus.pow import PoWConsensus
from .modules.consensus.raft import RaftConsensus
from .modules.consensus.poa import PoAConsensus
from .modules.consensus.pos import PoSConsensus
from .modules.consensus.pbft import PBFTConsensus
from .modules.consensus.hotstuff import HotStuffConsensus
from .modules.consensus.tendermint import TendermintConsensus
from .modules.consensus.paxos import PaxosConsensus
from .modules.consensus.none import NoConsensus
from .modules.network.p2p import P2PNetwork
from .modules.sync.fast import FastSync
from .modules.sync.light import LightSync
from .modules.sync.snapshot import SnapshotSync
from .modules.sync.realtime import RealtimeSync
from .modules.sync.batch import BatchSync
from .core.chain import Blockchain
from .interfaces.vm import VMInterface
from .modules.vm.evm import EVMRuntime
from .modules.vm.wasm import WASMRuntime
from .modules.vm.python_vm import PythonVM

class DependencyInjector:
    """
    Simple Dependency Injection Container.
    """
    
    _consensus_map: Dict[str, Type[ConsensusInterface]] = {
        "pow": PoWConsensus,
        "raft": RaftConsensus,
        "poa": PoAConsensus,
        "pos": PoSConsensus,
        "pbft": PBFTConsensus,
        "hotstuff": HotStuffConsensus,
        "tendermint": TendermintConsensus,
        "paxos": PaxosConsensus,
        "none": NoConsensus
    }
    
    _network_map: Dict[str, Type[NetworkInterface]] = {
        "p2p": P2PNetwork
    }
    
    _sync_map: Dict[str, Type[SyncInterface]] = {
        "full": FullSync,
        "fast": FastSync,
        "light": LightSync,
        "snapshot": SnapshotSync,
        "realtime": RealtimeSync,
        "batch": BatchSync
    }
    
    _runtime_map: Dict[str, Type[VMInterface]] = {
        "evm": EVMRuntime,
        "wasm": WASMRuntime,
        "python": PythonVM
    }

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def get_consensus(self) -> ConsensusInterface:
        algo = self.config.get("consensus", "pow")
        cls = self._consensus_map.get(algo)
        if not cls:
            raise ValueError(f"Unknown consensus algorithm: {algo}")
        
        # Instantiate with specific config params if needed
        return cls()

    def get_network(self) -> NetworkInterface:
        # Network usually needs a port
        cls = self._network_map.get("p2p")
        port = self.config.get("port", 5000)
        return cls(port=port)

    def get_sync(self, chain: Blockchain, network: NetworkInterface) -> SyncInterface:
        mode = self.config.get("syncMode", "full")
        cls = self._sync_map.get(mode)
        if not cls:
             # Fallback or error
             print(f"Warning: Unknown sync mode '{mode}', defaulting to FullSync")
             cls = FullSync
        return cls(chain, network)

    def get_runtime(self) -> VMInterface:
        mode = self.config.get("runtime", "evm")
        cls = self._runtime_map.get(mode)
        if not cls:
            print(f"Warning: Unknown runtime '{mode}', defaulting to EVM")
            cls = EVMRuntime
        return cls()
