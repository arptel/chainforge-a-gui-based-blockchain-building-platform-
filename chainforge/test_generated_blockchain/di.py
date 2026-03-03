from typing import Dict, Any, Type
from interfaces.consensus import ConsensusInterface
from interfaces.network import NetworkInterface
from interfaces.sync import SyncInterface
try: from modules.consensus.pow import PoWConsensus
except ImportError: PoWConsensus = None
try: from modules.consensus.raft import RaftConsensus
except ImportError: RaftConsensus = None
try: from modules.consensus.poa import PoAConsensus
except ImportError: PoAConsensus = None
try: from modules.consensus.pos import PoSConsensus
except ImportError: PoSConsensus = None
try: from modules.consensus.pbft import PBFTConsensus
except ImportError: PBFTConsensus = None
try: from modules.consensus.hotstuff import HotStuffConsensus
except ImportError: HotStuffConsensus = None
try: from modules.consensus.tendermint import TendermintConsensus
except ImportError: TendermintConsensus = None
try: from modules.consensus.paxos import PaxosConsensus
except ImportError: PaxosConsensus = None
try: from modules.consensus.none import NoConsensus
except ImportError: NoConsensus = None

try: from modules.network.p2p import P2PNetwork
except ImportError: P2PNetwork = None

try: from modules.sync.full import FullSync
except ImportError: FullSync = None
try: from modules.sync.fast import FastSync
except ImportError: FastSync = None
try: from modules.sync.light import LightSync
except ImportError: LightSync = None
try: from modules.sync.snapshot import SnapshotSync
except ImportError: SnapshotSync = None
try: from modules.sync.realtime import RealtimeSync
except ImportError: RealtimeSync = None
try: from modules.sync.batch import BatchSync
except ImportError: BatchSync = None
from core.chain import Blockchain
from interfaces.vm import VMInterface
from modules.vm.python_vm import PythonVM

# Attempt to load other VMs if present in the ZIP, but don't hard-crash if missing.
try:
    from modules.vm.evm import EVMRuntime
except ImportError:
    EVMRuntime = None

try:
    from modules.vm.wasm import WASMRuntime
except ImportError:
    WASMRuntime = None

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
        "evm": EVMRuntime if EVMRuntime else PythonVM,
        "wasm": WASMRuntime if WASMRuntime else PythonVM,
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
            print(f"Warning: Unknown runtime '{mode}', defaulting to PythonVM")
            cls = PythonVM
        return cls()
