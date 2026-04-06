"""
node_manager.py

Manages in-memory blockchain node instances.  Replaces the old
ProcessManager + chainforge_node.py subprocess architecture with a
direct-import approach that allows real cross-node consensus.

Each NodeInstance holds its own Blockchain object (with its own SQLite DB)
and the NodeManager orchestrates consensus rounds between them.
"""

import os
import sys
import copy
import time
import glob
import uuid
import hashlib
import json
import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class NodeInstance:
    """One in-memory blockchain node."""
    node_id: str
    role: str               # validator, miner, full, light
    blockchain: Any = None  # Blockchain from chain_node/core/chain.py
    status: str = "synced"  # synced, syncing, offline
    tx_log: list = field(default_factory=list)    # [{time, text, tx_hash}, ...]
    event_log: list = field(default_factory=list) # [{time, msg}, ...]

    def log(self, msg: str):
        self.event_log.append({"time": int(time.time() * 1000), "msg": msg})


# ---------------------------------------------------------------------------
# Pending join request for permissioned networks
# ---------------------------------------------------------------------------

@dataclass
class JoinRequest:
    request_id: str
    role: str
    votes: Dict[str, bool] = field(default_factory=dict)  # voter_id -> True/False
    status: str = "pending"  # pending, approved, rejected
    created_at: int = 0


# ---------------------------------------------------------------------------
# NodeManager
# ---------------------------------------------------------------------------

class NodeManager:
    """
    Manages in-memory Blockchain instances, orchestrates consensus,
    and emits events for the frontend via a callback.
    """

    def __init__(
        self,
        chain_node_dir: str,
        config: Dict[str, Any],
        chain_info: Dict[str, Any],
        event_callback: Optional[Callable] = None,
    ):
        self.chain_node_dir = chain_node_dir
        self.config = config
        self.chain_info = chain_info
        self.event_callback = event_callback  # async fn(event_dict)

        self.nodes: Dict[str, NodeInstance] = {}
        self.pending_joins: Dict[str, JoinRequest] = {}
        self._next_node_num = 0
        self._proposer_index = 0  # round-robin counter

        # Data directory for per-node SQLite DBs
        self.data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        os.makedirs(self.data_dir, exist_ok=True)

        # Import chain_node modules once
        self._import_chain_node()

        # Load genesis.json for Blockchain constructor params
        genesis_path = os.path.join(chain_node_dir, "config", "genesis.json")
        with open(genesis_path, "r", encoding="utf-8") as f:
            self.genesis = json.load(f)

    # ------------------------------------------------------------------
    # Boot-time import of chain_node code
    # ------------------------------------------------------------------

    def _import_chain_node(self):
        """Add chain_node to sys.path and import required modules."""
        if self.chain_node_dir not in sys.path:
            sys.path.insert(0, self.chain_node_dir)

        # Force re-import to pick up the correct chain_node
        from core.chain import Blockchain as _BC
        from core.block import Block as _BK
        from di import DependencyInjector as _DI

        self._Blockchain = _BC
        self._Block = _BK
        self._DI = _DI
        logger.info("chain_node modules imported successfully")

    # ------------------------------------------------------------------
    # Node lifecycle
    # ------------------------------------------------------------------

    def _make_consensus(self, node_id: str):
        """
        Create a consensus module instance for a single node.

        Handles platform code where consensus classes may have unimplemented
        abstract methods (e.g. commit_block) by dynamically patching them.
        """
        consensus_type = self.config["consensus"]

        # Build a DI config dict that matches what DependencyInjector expects
        di_config = {
            "consensus": consensus_type,
            "syncMode": self.config["sync_mode"],
            "runtime": "python",
            "node_id": node_id,
            "peers": [nid for nid in self.nodes if nid != node_id],
        }
        di = self._DI(di_config)

        # Robust initialisation (mirrors the old chainforge_node.py approach)
        consensus_module = None
        try:
            consensus_module = di.get_consensus()
        except TypeError:
            # Constructor needs args or has missing abstract methods
            cls = di._consensus_map.get(consensus_type)
            if cls is not None:
                # If there are unimplemented abstract methods, patch them
                if hasattr(cls, '__abstractmethods__') and cls.__abstractmethods__:
                    patches = {}
                    for m in cls.__abstractmethods__:
                        if m == "commit_block":
                            patches[m] = lambda self, block: True
                        elif m == "validate_block":
                            patches[m] = lambda self, block: True
                        else:
                            patches[m] = lambda self, *a, **kw: None
                    ConcreteClass = type(f"Sim{cls.__name__}", (cls,), patches)
                else:
                    ConcreteClass = cls

                # Try different constructor signatures
                try:
                    consensus_module = ConcreteClass(node_id=node_id, peers=[])
                except TypeError:
                    try:
                        consensus_module = ConcreteClass()
                    except TypeError:
                        consensus_module = None

        if consensus_module is None:
            logger.warning(f"Could not initialise consensus '{consensus_type}', using no-op")
        else:
            # Monkey-patch consensus methods because the Simulator orchestrates
            # consensus rounds manually, bypassing native message-passing states.
            # Without this, nodes with peers > 0 will reject blocks because their
            # internal vote dictionaries are empty.
            consensus_module.validate_block = lambda block: True
            consensus_module.commit_block = lambda block: True

        return consensus_module

    def _make_runtime(self):
        """Create a VM/runtime instance and deploy genesis smart contracts."""
        di_config = {"runtime": "python"}
        di = self._DI(di_config)
        runtime = di.get_runtime()

        if hasattr(runtime, 'default_gas_limit'):
            runtime.default_gas_limit = self.genesis.get("defaultGasLimit", 100000)

        # Deploy smart contracts from genesis
        contracts = self.genesis.get("smartContracts", [])
        if contracts and hasattr(runtime, 'contracts'):
            for sc in contracts:
                try:
                    code = sc.get("code", "")
                    contract_id = sc.get("id", "")
                    contract_name = sc.get("name", "")
                    if code and contract_id:
                        sandbox = {"__builtins__": __builtins__}
                        exec(code, sandbox)
                        cls_obj = None
                        for v in sandbox.values():
                            if isinstance(v, type) and v.__name__ == contract_name:
                                cls_obj = v
                                break
                        if cls_obj:
                            runtime.contracts[contract_id] = cls_obj()
                            logger.debug(f"Deployed contract: {contract_name}")
                except Exception as e:
                    logger.debug(f"Contract deploy skipped ({sc.get('name')}): {e}")

        return runtime

    def create_node(self, role: str, node_id: str = None) -> NodeInstance:
        """
        Create a new in-memory blockchain node.

        For nodes that join after genesis, the new node syncs the full chain
        from an existing node (copies blocks + state).
        """
        if node_id is None:
            node_id = f"node-{self._next_node_num}"
        self._next_node_num += 1

        if node_id in self.nodes:
            raise ValueError(f"Node '{node_id}' already exists.")

        # Determine DB path
        db_path = os.path.join(self.data_dir, f"node_{node_id}.sqlite")

        # Signature and gas settings from genesis
        require_sig = self.genesis.get("requireSignature", False)
        min_gas = self.genesis.get("minGasPrice", 0) if self.genesis.get("enableGas") else 0

        # Create a fresh consensus module for this node
        consensus = self._make_consensus(node_id)
        runtime = self._make_runtime()

        # Create Blockchain instance
        blockchain = self._Blockchain(
            consensus=consensus,
            runtime=runtime,
            role=role if role != "miner" else "full",  # chain.py uses "full" / "light"
            require_signature=False,  # Simulator skips real crypto signing
            min_gas_price=min_gas,
            db_path=db_path,
        )

        node = NodeInstance(
            node_id=node_id,
            role=role,
            blockchain=blockchain,
            status="syncing",
        )
        node.log(f"Node created as {role}")

        self.nodes[node_id] = node

        # Sync from existing nodes (copy chain)
        self._sync_node(node)

        # Update peer lists on all existing consensus modules
        self._update_peer_lists()

        node.status = "synced"
        node.log("Sync complete — node is ready")

        # Emit events
        self._emit({
            "type": "NODE_JOINED",
            "nodeId": node_id,
            "payload": {
                "nodeId": node_id,
                "role": role,
                "address": node_id,
            },
        })

        logger.info(f"Node {node_id} created (role={role})")
        return node

    def _sync_node(self, node: NodeInstance):
        """Copy missing blocks from an existing active node."""
        # Find an existing synced (and online) node
        source = None
        for nid, n in self.nodes.items():
            if nid != node.node_id and n.status == "synced":
                source = n
                break

        if source is None:
            # First node — genesis already created by Blockchain.__init__
            return

        # Fast-forward sync: Only pull blocks newer than our current local height
        current_height = len(node.blockchain.chain)
        missing_blocks = source.blockchain.chain[current_height:]

        for block in missing_blocks:
            block_copy = copy.deepcopy(block)
            if node.role == "light":
                block_copy.transactions = []
            node.blockchain.add_block(block_copy)

        if len(missing_blocks) > 0:
            source.log(f"Received sync request from {node.node_id}. Sent {len(missing_blocks)} block(s).")
            node.log(f"Received {len(missing_blocks)} missing block(s) from {source.node_id}.")

        self._emit({
            "type": "SYNC_COMPLETE",
            "nodeId": node.node_id,
            "payload": {
                "nodeId": node.node_id,
                "finalHeight": len(node.blockchain.chain) - 1,
            },
        })

    def _update_peer_lists(self):
        """Update peer lists on all consensus modules."""
        all_ids = list(self.nodes.keys())
        for nid, node in self.nodes.items():
            if hasattr(node.blockchain.consensus, 'peers'):
                node.blockchain.consensus.peers = [p for p in all_ids if p != nid]
                if hasattr(node.blockchain.consensus, 'quorum'):
                    node.blockchain.consensus.quorum = (len(node.blockchain.consensus.peers) * 2 // 3) + 1

    def remove_node(self, node_id: str):
        """Remove a node and optionally delete its DB."""
        if node_id not in self.nodes:
            raise ValueError(f"Node '{node_id}' not found.")

        # For permissioned networks, node-0 cannot be removed
        if node_id == "node-0" and self.config["governance"] != "decentralized":
            raise ValueError("Cannot remove the owner node (node-0) in a permissioned network.")

        del self.nodes[node_id]

        # Delete SQLite file
        db_path = os.path.join(self.data_dir, f"node_{node_id}.sqlite")
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
            except OSError:
                pass

    def toggle_node(self, node_id: str, online: bool):
        """Turn a node ON or OFF (simulate power cut)."""
        if node_id not in self.nodes:
            raise ValueError(f"Node '{node_id}' not found.")
            
        node = self.nodes[node_id]
        was_online = node.status != "offline"

        if not online and was_online:
            # Power loss
            node.status = "offline"
            node.log("Node went OFFLINE (Power cut simulation)")
            
            # Wipe mempool to simulate volatile RAM destruction
            if hasattr(node.blockchain, "mempool"):
                node.blockchain.mempool.clear()
                
            self._emit({
                "type": "NODE_OFFLINE",
                "nodeId": node.node_id,
                "payload": {"nodeId": node.node_id}
            })
            
        elif online and not was_online:
            # Power restored
            node.status = "syncing"
            node.log("Node came ONLINE. Syncing...")
            self._sync_node(node)
            node.status = "synced"
            node.log("Sync complete. Fully operational.")
            
            self._emit({
                "type": "NODE_ONLINE",
                "nodeId": node.node_id,
                "payload": {"nodeId": node.node_id}
            })

        self._update_peer_lists()

        self._emit({
            "type": "NODE_OFFLINE",
            "nodeId": node_id,
            "payload": {"nodeId": node_id, "reason": "removed by user"},
        })
        logger.info(f"Node {node_id} removed")

    # ------------------------------------------------------------------
    # Transactions & consensus
    # ------------------------------------------------------------------

    def _can_send_tx(self, role: str) -> bool:
        """Check if a node role is authorised to submit transactions."""
        return role in ("validator", "miner", "full", "leader")

    def submit_transaction(self, from_node_id: str, text: str) -> Dict[str, Any]:
        """
        Submit a data transaction from a specific node.
        Broadcasts to all nodes, then triggers a consensus round.
        """
        if from_node_id not in self.nodes:
            raise ValueError(f"Node '{from_node_id}' not found.")

        node = self.nodes[from_node_id]
        if not self._can_send_tx(node.role):
            raise ValueError(f"Node '{from_node_id}' (role={node.role}) is not authorised to send transactions.")

        # Build transaction dict
        tx_hash = hashlib.sha256(f"{from_node_id}-{text}-{time.time()}".encode()).hexdigest()[:16]
        tx = {
            "from": from_node_id,
            "to": "network",
            "amount": 0,
            "type": "data",
            "memo": text,
            "gas_price": 0,
            "gas_limit": self.genesis.get("defaultGasLimit", 100000),
            "timestamp": time.time(),
            "tx_hash": tx_hash,
        }

        # Broadcast to ALL nodes' mempools
        for nid, n in self.nodes.items():
            if n.status == "synced" and n.role != "light":
                n.blockchain.add_transaction(copy.deepcopy(tx))
                n.log(f"Received tx {tx_hash[:8]}… from {from_node_id}")

        # Log on sender
        node.tx_log.append({
            "time": int(time.time() * 1000),
            "text": text,
            "tx_hash": tx_hash,
            "from": from_node_id,
        })

        self._emit({
            "type": "TX_BROADCAST",
            "nodeId": from_node_id,
            "payload": {
                "txId": tx_hash,
                "fromNodeId": from_node_id,
                "toNodeId": "network",
                "memo": text,
            },
        })

        # Trigger consensus round
        result = self._run_consensus_round()
        return {"tx_hash": tx_hash, "block_mined": result}

    def _run_consensus_round(self) -> bool:
        """
        Execute one consensus round:
          1. Select proposer
          2. Proposer mines a block
          3. All other nodes validate and add the block
          4. Emit consensus phase events
        """
        proposer = self._select_proposer()
        if proposer is None:
            logger.warning("No eligible proposer found")
            return False

        consensus_type = self.config["consensus"]
        phases = self.chain_info.get("consensus_phases", ["COMMIT"])

        # Phase 1: PROPOSE
        self._emit({
            "type": "CONSENSUS_PHASE",
            "nodeId": proposer.node_id,
            "payload": {"phase": phases[0], "round": self._proposer_index},
        })

        # Mine the block on the proposer node
        mined = proposer.blockchain.mine_pending_transactions(proposer.node_id)
        if not mined:
            logger.info("No pending transactions to mine")
            return False

        new_block = proposer.blockchain.last_block
        proposer.log(f"Proposed & mined block #{new_block.index}")

        self._emit({
            "type": "BLOCK_PROPOSED",
            "nodeId": proposer.node_id,
            "payload": {
                "blockHeight": new_block.index,
                "proposerNodeId": proposer.node_id,
                "txCount": len(new_block.transactions),
            },
        })

        # Phase 2: VOTE / VALIDATE
        if len(phases) >= 2:
            self._emit({
                "type": "CONSENSUS_PHASE",
                "nodeId": proposer.node_id,
                "payload": {"phase": phases[1], "round": self._proposer_index},
            })

        # Validate on all other nodes and collect votes
        validators = [n for nid, n in self.nodes.items()
                      if nid != proposer.node_id and n.status == "synced"]
        votes_accept = 0
        votes_reject = 0

        for v_node in validators:
            # Deep copy the block for this node
            block_copy = copy.deepcopy(new_block)

            # Light nodes get stripped blocks
            if v_node.role == "light":
                block_copy.transactions = []

            # Try to add the block (validates via consensus + adds to chain)
            accepted = v_node.blockchain.add_block(block_copy)

            if accepted:
                votes_accept += 1
                v_node.log(f"Received & validated block #{new_block.index} from {proposer.node_id}")
            else:
                votes_reject += 1
                v_node.log(f"Rejected block #{new_block.index} from {proposer.node_id}")

            # Emit vote event for validators/miners (not light nodes)
            if v_node.role in ("validator", "miner"):
                self._emit({
                    "type": "VOTE_CAST",
                    "nodeId": v_node.node_id,
                    "payload": {
                        "voterNodeId": v_node.node_id,
                        "blockHeight": new_block.index,
                        "vote": "accept" if accepted else "reject",
                        "round": self._proposer_index,
                    },
                })

        # Phase 3+: COMMIT
        final_phase = phases[-1]
        self._emit({
            "type": "CONSENSUS_PHASE",
            "nodeId": proposer.node_id,
            "payload": {"phase": final_phase, "round": self._proposer_index},
        })

        self._emit({
            "type": "BLOCK_COMMITTED",
            "nodeId": proposer.node_id,
            "payload": {
                "blockHeight": new_block.index,
                "hash": new_block.hash,
                "proposerNodeId": proposer.node_id,
                "txCount": len(new_block.transactions),
                "commitTime": int(time.time() * 1000),
                "votesAccept": votes_accept,
                "votesReject": votes_reject,
            },
        })

        self._proposer_index += 1
        return True

    def _select_proposer(self) -> Optional[NodeInstance]:
        """
        Select the next block proposer based on consensus type.

        - PoW:  round-robin among miner nodes
        - PoS:  round-robin among validator nodes
        - PoA:  round-robin among authority (validator) nodes
        - PBFT/HotStuff/Tendermint: leader rotation among validators
        - Raft/Paxos: always node-0 (the leader)
        - None:  first available node
        """
        consensus = self.config["consensus"]

        if consensus in ("raft", "paxos"):
            # Leader-based: node-0 is always the proposer
            if "node-0" in self.nodes:
                return self.nodes["node-0"]
            return None

        if consensus == "none":
            # Any node that can mine
            for n in self.nodes.values():
                if n.role != "light" and n.status == "synced":
                    return n
            return None

        # For all others: round-robin among eligible proposers
        if consensus == "pow":
            eligible = [n for n in self.nodes.values()
                        if n.role == "miner" and n.status == "synced"]
        else:
            # pos, poa, pbft, hotstuff, tendermint
            eligible = [n for n in self.nodes.values()
                        if n.role == "validator" and n.status == "synced"]

        if not eligible:
            # Fallback: any non-light synced node
            eligible = [n for n in self.nodes.values()
                        if n.role != "light" and n.status == "synced"]

        if not eligible:
            return None

        idx = self._proposer_index % len(eligible)
        return eligible[idx]

    # ------------------------------------------------------------------
    # Node data retrieval
    # ------------------------------------------------------------------

    def get_node_data(self, node_id: str) -> Dict[str, Any]:
        """Return detailed data for a specific node (for the detail panel)."""
        if node_id not in self.nodes:
            raise ValueError(f"Node '{node_id}' not found.")

        node = self.nodes[node_id]
        bc = node.blockchain

        # Build block list
        blocks = []
        for b in bc.chain:
            blocks.append({
                "index": b.index,
                "hash": b.hash,
                "previous_hash": b.previous_hash,
                "validator": b.validator,
                "tx_count": len(b.transactions),
                "timestamp": b.timestamp,
            })

        # State
        state = dict(bc.state) if bc.state else {}

        # Balance (if applicable)
        balance = None
        if self.chain_info.get("show_balance"):
            balance = state.get(node_id, {}).get("balance", 0)

        return {
            "node_id": node_id,
            "role": node.role,
            "status": node.status,
            "height": len(bc.chain) - 1,
            "blocks": blocks,
            "state": state,
            "tx_log": node.tx_log[-50:],  # last 50
            "event_log": node.event_log[-50:],  # last 50
            "balance": balance,
            "mempool_size": bc.mempool.size(),
        }

    def get_all_nodes_summary(self) -> List[Dict[str, Any]]:
        """Return a summary of all nodes for the node list."""
        summaries = []
        for nid, node in self.nodes.items():
            summaries.append({
                "node_id": nid,
                "role": node.role,
                "status": node.status,
                "height": len(node.blockchain.chain) - 1,
            })
        return summaries

    # ------------------------------------------------------------------
    # Permissioned join workflows
    # ------------------------------------------------------------------

    def request_join(self, role: str) -> Dict[str, Any]:
        """
        Request to join the network.
        - Public: immediately creates the node.
        - Centralized/Owner: creates a pending request for owner approval.
        - Consortium/multisig: creates a pending request for validator voting.
        - Consortium/ca: creates a pending request for CA (node-0) approval.
        """
        governance = self.config["governance"]
        join_mechanism = self.config["join_mechanism"]

        if governance == "decentralized":
            # Public — instant join
            node = self.create_node(role)
            return {"status": "approved", "node_id": node.node_id}

        # Permissioned — create pending request
        req_id = str(uuid.uuid4())[:8]
        req = JoinRequest(
            request_id=req_id,
            role=role,
            status="pending",
            created_at=int(time.time() * 1000),
        )
        self.pending_joins[req_id] = req

        self._emit({
            "type": "JOIN_REQUEST",
            "nodeId": "system",
            "payload": {
                "requestId": req_id,
                "role": role,
                "mechanism": join_mechanism,
            },
        })

        # Log on all validator nodes
        for nid, node in self.nodes.items():
            if self._is_voter(node, join_mechanism):
                node.log(f"Join request received: {role} node (req={req_id[:6]})")

        return {"status": "pending", "request_id": req_id, "mechanism": join_mechanism}

    def vote_on_join(self, voter_node_id: str, request_id: str, approve: bool) -> Dict[str, Any]:
        """Cast a vote on a pending join request."""
        if request_id not in self.pending_joins:
            raise ValueError(f"Join request '{request_id}' not found.")
        if voter_node_id not in self.nodes:
            raise ValueError(f"Node '{voter_node_id}' not found.")

        req = self.pending_joins[request_id]
        if req.status != "pending":
            raise ValueError(f"Request '{request_id}' is already {req.status}.")

        join_mechanism = self.config["join_mechanism"]
        voter = self.nodes[voter_node_id]

        if not self._is_voter(voter, join_mechanism):
            raise ValueError(f"Node '{voter_node_id}' is not authorised to vote.")

        # Record the vote
        req.votes[voter_node_id] = approve
        voter.log(f"Voted {'accept' if approve else 'reject'} on join request {request_id[:6]}")

        self._emit({
            "type": "JOIN_VOTE",
            "nodeId": voter_node_id,
            "payload": {
                "requestId": request_id,
                "voterNodeId": voter_node_id,
                "vote": "accept" if approve else "reject",
            },
        })

        # Check threshold
        approved = self._check_join_threshold(req)
        if approved is True:
            req.status = "approved"
            node = self.create_node(req.role)
            return {"status": "approved", "node_id": node.node_id}
        elif approved is False:
            req.status = "rejected"
            del self.pending_joins[request_id]
            return {"status": "rejected"}
        else:
            # Still pending — return vote tally
            accept_count = sum(1 for v in req.votes.values() if v)
            total_voters = self._count_voters(join_mechanism)
            return {
                "status": "pending",
                "votes_accept": accept_count,
                "votes_total": len(req.votes),
                "voters_needed": total_voters,
            }

    def _is_voter(self, node: NodeInstance, join_mechanism: str) -> bool:
        """Check if a node is allowed to vote on join requests."""
        if join_mechanism in ("ca", "owner"):
            return node.node_id == "node-0"
        # multisig — all validators vote
        return node.role in ("validator", "miner")

    def _count_voters(self, join_mechanism: str) -> int:
        """Count the total number of eligible voters."""
        if join_mechanism in ("ca", "owner"):
            return 1
        return sum(1 for n in self.nodes.values() if n.role in ("validator", "miner"))

    def _check_join_threshold(self, req: JoinRequest) -> Optional[bool]:
        """
        Check if the vote threshold has been met.
        Returns True (approved), False (rejected), or None (still pending).
        """
        join_mechanism = self.config["join_mechanism"]
        total_voters = self._count_voters(join_mechanism)

        if total_voters == 0:
            return True  # no voters = auto-approve

        accept_count = sum(1 for v in req.votes.values() if v)
        reject_count = sum(1 for v in req.votes.values() if not v)

        if join_mechanism in ("ca", "owner"):
            # Single authority: one vote decides
            if accept_count >= 1:
                return True
            if reject_count >= 1:
                return False
            return None

        # Multisig voting
        fault_tolerance = self.config.get("fault_tolerance", "bft")
        if fault_tolerance == "bft":
            threshold = (total_voters * 2 // 3) + 1
        else:
            threshold = (total_voters // 2) + 1

        if accept_count >= threshold:
            return True
        if reject_count > total_voters - threshold:
            return False
        return None

    def get_pending_joins(self) -> List[Dict[str, Any]]:
        """Return all pending join requests (for the frontend)."""
        result = []
        for req_id, req in self.pending_joins.items():
            if req.status == "pending":
                accept_count = sum(1 for v in req.votes.values() if v)
                total_voters = self._count_voters(self.config["join_mechanism"])
                result.append({
                    "request_id": req_id,
                    "role": req.role,
                    "votes": dict(req.votes),
                    "votes_accept": accept_count,
                    "voters_needed": total_voters,
                    "created_at": req.created_at,
                })
        return result

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------

    def reset(self):
        """Remove all nodes, delete all DBs, reset state."""
        node_ids = list(self.nodes.keys())
        for nid in node_ids:
            try:
                del self.nodes[nid]
            except KeyError:
                pass

        # Delete all SQLite files in data/
        for f in glob.glob(os.path.join(self.data_dir, "node_*.sqlite")):
            try:
                os.remove(f)
            except OSError:
                pass

        self.pending_joins.clear()
        self._next_node_num = 0
        self._proposer_index = 0
        logger.info("NodeManager reset complete")

    # ------------------------------------------------------------------
    # Event emission
    # ------------------------------------------------------------------

    def _emit(self, event: Dict[str, Any]):
        """Emit an event to the callback (usually the EventBridge)."""
        if "timestamp" not in event:
            event["timestamp"] = int(time.time() * 1000)

        if self.event_callback:
            try:
                self.event_callback(event)
            except Exception as e:
                logger.error(f"Event callback error: {e}")
