"""
Config Parser - Validates and parses config.yaml for the simulator.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
import yaml
import logging

logger = logging.getLogger(__name__)


@dataclass
class Config:
    """Parsed configuration from config.yaml."""
    network_type: str  # permissioned, permissionless
    governance: str  # consortium, democratic, single, centralized, decentralized
    consensus: str  # pow, pos, poa, pbft, raft, tendermint, hotstuff, paxos, none
    node_roles: List[str]  # [full, validator, light, ...]
    sync_mode: str  # full, light, fast, snapshot, batch, realtime
    max_nodes: int  # 0 = unlimited
    block_time_ms: int  # milliseconds

    modules: List[str] = field(default_factory=list)
    api_endpoint: Optional[str] = None
    require_auth: bool = False

    # Unknown fields stored here for forward compatibility
    extras: Dict[str, Any] = field(default_factory=dict)


class ConfigParser:
    """
    Parses and validates config.yaml files.

    Enforces:
    - All required fields are present
    - Valid values for known enums (consensus type, sync mode, etc.)
    - Specific error messages for missing fields
    - Forward compatibility (unknown fields ignored)
    """

    REQUIRED_FIELDS = {
        'network_type',
        'governance',
        'consensus',
        'node_roles',
        'sync_mode',
        'max_nodes',
        'block_time_ms',
    }

    VALID_NETWORK_TYPES = {'permissioned', 'permissionless', 'public'}
    VALID_GOVERNANCE = {'consortium', 'democratic', 'single', 'centralized', 'decentralized'}
    VALID_CONSENSUS_TYPES = {'pow', 'pos', 'poa', 'pbft', 'raft', 'tendermint', 'hotstuff', 'paxos', 'none'}
    VALID_SYNC_MODES = {'full', 'light', 'fast', 'snapshot', 'batch', 'realtime'}
    VALID_NODE_ROLES = {'miner', 'full', 'light', 'validator', 'authority'}

    def parse_file(self, config_path: str) -> Config:
        """
        Parse a config.yaml file.

        Raises:
            FileNotFoundError: If config file not found
            ValueError: If config is invalid or required fields missing
            yaml.YAMLError: If YAML parsing fails
        """
        try:
            with open(config_path, 'r') as f:
                data = yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"This does not appear to be a valid ChainForge project. "
                f"config.yaml not found at: {config_path}"
            )
        except yaml.YAMLError as e:
            raise ValueError(f"Failed to parse config.yaml: {e}")

        if not isinstance(data, dict):
            raise ValueError("config.yaml must contain a YAML mapping (key-value pairs)")

        return self.validate(data)

    def parse_string(self, yaml_content: str) -> Config:
        """Parse YAML content from a string."""
        data = yaml.safe_load(yaml_content)
        if not isinstance(data, dict):
            raise ValueError("config.yaml must contain a YAML mapping (key-value pairs)")
        return self.validate(data)

    def validate(self, data: Dict[str, Any]) -> Config:
        """
        Validate parsed config dictionary.

        Raises:
            ValueError: With specific field-level error messages
        """
        # Check all required fields present
        for field_name in self.REQUIRED_FIELDS:
            if field_name not in data:
                raise ValueError(
                    f"Invalid ChainForge project: required field '{field_name}' "
                    f"is missing from config.yaml."
                )

        # Validate network_type
        network_type = str(data['network_type']).lower()
        if network_type not in self.VALID_NETWORK_TYPES:
            raise ValueError(
                f"Invalid network_type '{data['network_type']}'. "
                f"Must be one of: {', '.join(sorted(self.VALID_NETWORK_TYPES))}"
            )

        # Validate governance
        governance = str(data['governance']).lower()
        if governance not in self.VALID_GOVERNANCE:
            raise ValueError(
                f"Invalid governance '{data['governance']}'. "
                f"Must be one of: {', '.join(sorted(self.VALID_GOVERNANCE))}"
            )

        # Validate consensus
        consensus = str(data['consensus']).lower()
        if consensus not in self.VALID_CONSENSUS_TYPES:
            raise ValueError(
                f"Invalid consensus '{data['consensus']}'. "
                f"Must be one of: {', '.join(sorted(self.VALID_CONSENSUS_TYPES))}"
            )

        # Validate node_roles
        node_roles = data['node_roles']
        if not isinstance(node_roles, list) or len(node_roles) == 0:
            raise ValueError("node_roles must be a non-empty list of role strings.")
        for role in node_roles:
            if str(role).lower() not in self.VALID_NODE_ROLES:
                raise ValueError(
                    f"Invalid node role '{role}'. "
                    f"Must be one of: {', '.join(sorted(self.VALID_NODE_ROLES))}"
                )

        # Validate sync_mode
        sync_mode = str(data['sync_mode']).lower()
        if sync_mode not in self.VALID_SYNC_MODES:
            raise ValueError(
                f"Invalid sync_mode '{data['sync_mode']}'. "
                f"Must be one of: {', '.join(sorted(self.VALID_SYNC_MODES))}"
            )

        # Validate max_nodes
        try:
            max_nodes = int(data['max_nodes'])
        except (ValueError, TypeError):
            raise ValueError(f"max_nodes must be an integer, got: {data['max_nodes']}")
        if max_nodes < 0:
            raise ValueError(f"max_nodes must be >= 0, got: {max_nodes}")

        # Validate block_time_ms
        try:
            block_time_ms = int(data['block_time_ms'])
        except (ValueError, TypeError):
            raise ValueError(f"block_time_ms must be an integer, got: {data['block_time_ms']}")
        if block_time_ms <= 0:
            raise ValueError(f"block_time_ms must be > 0, got: {block_time_ms}")

        # Extract known optional fields
        modules = data.get('modules', [])
        if not isinstance(modules, list):
            modules = [modules] if modules else []

        api_endpoint = data.get('api_endpoint', None)
        require_auth = bool(data.get('require_auth', False))

        # Collect unknown fields as extras for forward compatibility
        known_fields = self.REQUIRED_FIELDS | {'modules', 'api_endpoint', 'require_auth'}
        extras = {k: v for k, v in data.items() if k not in known_fields}

        return Config(
            network_type=network_type,
            governance=governance,
            consensus=consensus,
            node_roles=[str(r).lower() for r in node_roles],
            sync_mode=sync_mode,
            max_nodes=max_nodes,
            block_time_ms=block_time_ms,
            modules=[str(m) for m in modules],
            api_endpoint=api_endpoint,
            require_auth=require_auth,
            extras=extras,
        )

    def to_dict(self, config: Config) -> Dict[str, Any]:
        """Convert Config object back to dictionary."""
        d = asdict(config)
        # Merge extras into top-level
        extras = d.pop('extras', {})
        d.update(extras)
        return d

    def to_yaml(self, config: Config) -> str:
        """Convert Config object to YAML string."""
        return yaml.dump(self.to_dict(config), default_flow_style=False)

    @staticmethod
    def create_default_config() -> Config:
        """Create a minimal valid config for testing."""
        return Config(
            network_type='permissioned',
            governance='consortium',
            consensus='pbft',
            node_roles=['validator', 'full', 'light'],
            sync_mode='full',
            max_nodes=20,
            block_time_ms=3000,
            modules=['token', 'governance'],
            api_endpoint='http://localhost:8545',
            require_auth=True,
        )
