"""
config_generator.py

Reads chain_node/config/genesis.json and produces:
  1. A normalised config dict (consensus, sync_mode, node_roles, governance, etc.)
  2. A rich "chain info" dict with human-readable descriptions for the Info panel.

This replaces the need for a manual config.yaml file.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Human-readable descriptions for the Info panel
# ---------------------------------------------------------------------------

CONSENSUS_DESCRIPTIONS: Dict[str, str] = {
    "pow": "Proof of Work — miners compete to solve a cryptographic puzzle. The first miner to find a valid hash earns the right to propose the next block.",
    "pos": "Proof of Stake — validators are selected to propose blocks proportional to their staked tokens. Energy-efficient alternative to PoW.",
    "poa": "Proof of Authority — pre-approved authority nodes take turns proposing blocks. Fast finality with trusted validators.",
    "pbft": "Practical Byzantine Fault Tolerance — a 3-phase (Pre-Prepare, Prepare, Commit) protocol tolerating up to ⌊(n-1)/3⌋ Byzantine faults.",
    "hotstuff": "HotStuff — a 3-phase pipelined BFT protocol with linear communication complexity. Uses Quorum Certificates for efficient consensus.",
    "tendermint": "Tendermint — a 4-phase (Propose, Prevote, Precommit, Commit) BFT protocol with instant finality and ⅔+ quorum requirement.",
    "raft": "Raft — a Crash Fault Tolerant leader-based protocol. The leader replicates log entries to followers; requires majority acknowledgment.",
    "paxos": "Paxos — a 2-phase (Prepare, Accept) protocol for reaching consensus in distributed systems with crash failures.",
    "none": "No Consensus — blocks are committed unilaterally by any node. Useful for single-node development chains.",
}

SYNC_DESCRIPTIONS: Dict[str, str] = {
    "full": "Full Sync — downloads and replays all blocks from genesis. Every block and transaction is verified.",
    "fast": "Fast Sync — downloads a recent state snapshot, then syncs only recent blocks. Faster initial sync.",
    "light": "Light Sync — downloads only block headers and uses Merkle proofs for verification. Minimal storage.",
    "snapshot": "Snapshot Sync — downloads the full state at a checkpoint. Counter jumps to the checkpoint height.",
    "realtime": "Realtime Sync — joins at the chain tip with no catch-up. Immediate participation.",
    "batch": "Batch Sync — downloads blocks in waves/batches. Efficient for high-throughput chains.",
}

NETWORK_DESCRIPTIONS: Dict[str, str] = {
    "public": "A public (permissionless) blockchain. Anyone can join, mine, and transact without approval.",
    "permissioned": "A permissioned blockchain. Only approved participants can join the network.",
}

GOVERNANCE_DESCRIPTIONS: Dict[str, str] = {
    "decentralized": "Decentralized governance — no single entity controls the network.",
    "consortium": "Consortium governance — multiple organizations jointly govern the network through voting.",
    "centralized": "Centralized governance — a single authority (owner) controls node admission and operations.",
}

JOIN_MECHANISM_DESCRIPTIONS: Dict[str, str] = {
    "open": "Open — anyone can join the network freely without approval.",
    "multisig": "Multi-Signature — new nodes must be approved by a threshold vote from existing validators.",
    "ca": "Certificate Authority — new nodes must be approved by the designated certificate authority (node-0).",
    "owner": "Owner-Only — only the network owner (node-0) can add new nodes.",
}

# Consensus phase names for each type (for the phase indicator bar)
CONSENSUS_PHASES: Dict[str, List[str]] = {
    "pow": ["MINING", "VALIDATE", "COMMIT"],
    "pos": ["SELECT", "VALIDATE", "COMMIT"],
    "poa": ["PROPOSE", "STAMP", "COMMIT"],
    "pbft": ["PRE-PREPARE", "PREPARE", "COMMIT"],
    "hotstuff": ["PROPOSE", "PRE-COMMIT", "COMMIT"],
    "tendermint": ["PROPOSE", "PREVOTE", "PRECOMMIT", "COMMIT"],
    "raft": ["PROPOSE", "REPLICATE", "COMMIT"],
    "paxos": ["PREPARE", "ACCEPT"],
    "none": ["COMMIT"],
}


def detect_chain_node(backend_dir: str) -> Optional[str]:
    """
    Check if chain_node/ exists with the expected structure.
    Returns the path to chain_node/ if valid, None otherwise.
    """
    chain_node_dir = os.path.join(backend_dir, "chain_node")
    genesis_path = os.path.join(chain_node_dir, "config", "genesis.json")
    di_path = os.path.join(chain_node_dir, "di.py")

    if os.path.isfile(genesis_path) and os.path.isfile(di_path):
        return chain_node_dir
    return None


def load_genesis(chain_node_dir: str) -> Dict[str, Any]:
    """Load and return the genesis.json config."""
    genesis_path = os.path.join(chain_node_dir, "config", "genesis.json")
    with open(genesis_path, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_config(genesis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a genesis.json into a normalised config dict.

    Returns dict with keys:
        network_type, governance, consensus, sync_mode, node_roles,
        max_nodes, block_time_ms, require_signature, enable_gas,
        min_gas_price, default_gas_limit, join_mechanism,
        validator_structure, fault_tolerance, smart_contracts
    """
    net_type = genesis.get("networkType", "public")

    if net_type == "public":
        consensus = genesis.get("publicConsensus", "pow")
        sync_mode = genesis.get("publicSyncMode", "full")
        node_roles = ["miner", "full", "light"]
        governance = "decentralized"
        join_mechanism = "open"
        validator_structure = "equal"
        fault_tolerance = None
    elif net_type == "permissioned":
        perm_type = genesis.get("permissionedType", "centralized")

        if perm_type == "consortium":
            consensus = genesis.get("consortiumConsensus", "pbft")
            sync_mode = genesis.get("consortiumSync", "full")
            node_roles = ["validator", "full", "light"]
            governance = "consortium"
            identity = genesis.get("consortiumIdentity", "multisig")
            join_mechanism = identity  # "multisig" or "ca"
            validator_structure = genesis.get("consortiumValidatorStruct", "equal")
            fault_tolerance = genesis.get("consortiumFaultTol", "bft")
        else:
            # centralized
            consensus = genesis.get("centralizedConsensus", "raft")
            sync_mode = genesis.get("centralizedSync", "realtime")
            node_roles = ["full", "light"]
            governance = "centralized"
            join_mechanism = "owner"
            validator_structure = None
            fault_tolerance = None
    else:
        # Fallback
        consensus = "none"
        sync_mode = "full"
        node_roles = ["full", "light"]
        governance = "decentralized"
        join_mechanism = "open"
        validator_structure = "equal"
        fault_tolerance = None

    # Smart contracts from genesis
    smart_contracts = []
    for sc in genesis.get("smartContracts", []):
        smart_contracts.append({
            "id": sc.get("id"),
            "name": sc.get("name"),
            "type": sc.get("type", "python"),
            "isSystem": sc.get("isSystem", False),
        })

    return {
        "network_type": net_type,
        "governance": governance,
        "consensus": consensus,
        "sync_mode": sync_mode,
        "node_roles": node_roles,
        "max_nodes": genesis.get("nodeCount", 10),
        "block_time_ms": 3000,
        "require_signature": genesis.get("requireSignature", False),
        "enable_gas": genesis.get("enableGas", False),
        "min_gas_price": genesis.get("minGasPrice", 0),
        "default_gas_limit": genesis.get("defaultGasLimit", 100000),
        "join_mechanism": join_mechanism,
        "validator_structure": validator_structure,
        "fault_tolerance": fault_tolerance,
        "smart_contracts": smart_contracts,
    }


def generate_chain_info(genesis: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Produce a rich chain-info dict with human-readable descriptions
    for the frontend Info (ℹ️) panel.
    """
    consensus = config["consensus"]
    sync_mode = config["sync_mode"]
    net_type = config["network_type"]
    governance = config["governance"]
    join_mech = config["join_mechanism"]

    # token/balance applicable?
    has_token = genesis.get("publicToken") == "native"
    has_gas = config["enable_gas"]
    show_balance = has_token or has_gas

    return {
        "network_type": net_type,
        "network_description": NETWORK_DESCRIPTIONS.get(net_type, ""),
        "governance": governance,
        "governance_description": GOVERNANCE_DESCRIPTIONS.get(governance, ""),
        "consensus": consensus,
        "consensus_description": CONSENSUS_DESCRIPTIONS.get(consensus, ""),
        "consensus_phases": CONSENSUS_PHASES.get(consensus, ["COMMIT"]),
        "sync_mode": sync_mode,
        "sync_description": SYNC_DESCRIPTIONS.get(sync_mode, ""),
        "node_roles": config["node_roles"],
        "max_nodes": config["max_nodes"],
        "block_time_ms": config["block_time_ms"],
        "join_mechanism": join_mech,
        "join_description": JOIN_MECHANISM_DESCRIPTIONS.get(join_mech, ""),
        "validator_structure": config["validator_structure"],
        "fault_tolerance": config["fault_tolerance"],
        "has_token": has_token,
        "has_gas": has_gas,
        "show_balance": show_balance,
        "require_signature": config["require_signature"],
        "smart_contracts": [
            {"name": sc["name"], "type": sc["type"], "isSystem": sc["isSystem"]}
            for sc in config["smart_contracts"]
        ],
    }
