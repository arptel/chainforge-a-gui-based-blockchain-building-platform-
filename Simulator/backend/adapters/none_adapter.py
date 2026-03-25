"""
None (No Consensus) Adapter - Fully implemented.
Any node can propose and commit blocks unilaterally.
No voting, no consensus phases — direct commit on transaction.
"""

import asyncio
import json
import time
import logging
from typing import Callable, List, Optional, Dict, Any

import httpx

try:
    from chain_adapter import IChainAdapter, NodeProcess, Transaction, Block, ConsensusState, ChainEvent
except ImportError:
    from ..chain_adapter import IChainAdapter, NodeProcess, Transaction, Block, ConsensusState, ChainEvent

logger = logging.getLogger(__name__)


class NoneAdapter(IChainAdapter):
    """
    No Consensus adapter implementation.
    Any node can propose and commit blocks unilaterally.
    Useful for single-node development chains.
    """

    def __init__(self):
        self.nodes: Dict[str, NodeProcess] = {}
        self.event_handlers: List[Callable[[ChainEvent], None]] = []
        self.blocks: List[Block] = []
        self._current_round: int = 0
        self._stdout_readers: Dict[str, asyncio.Task] = {}

    async def spawn_node(self, role: str, port: int) -> NodeProcess:
        """
        Spawn a node in no-consensus mode.
        All nodes are equal; any can propose blocks.
        """
        node_id = f"node-{len(self.nodes) + 1}"
        node = NodeProcess(
            node_id=node_id,
            role=role,
            port=port,
            status="ready",
        )
        self.nodes[node_id] = node
        return node

    async def terminate_node(self, node_id: str) -> None:
        """Terminate a node."""
        if node_id not in self.nodes:
            raise ValueError(f"Node '{node_id}' not found in adapter.")
        # Cancel stdout reader if exists
        if node_id in self._stdout_readers:
            self._stdout_readers[node_id].cancel()
            del self._stdout_readers[node_id]
        del self.nodes[node_id]

    async def submit_transaction(self, tx: Transaction, from_node_id: str = None) -> str:
        """
        Submit transaction to a node's RPC.
        The node will include it in its next block and emit events.
        """
        # Find the target node to submit to
        target_node_id = from_node_id or tx.from_address
        if target_node_id not in self.nodes:
            # If specific node not found, submit to first available
            if not self.nodes:
                raise RuntimeError("No nodes available to submit transaction to.")
            target_node_id = next(iter(self.nodes))

        target = self.nodes[target_node_id]

        # Submit to the node's RPC endpoint
        url = f"http://127.0.0.1:{target.port}/submit_transaction"
        payload = {
            "from_address": tx.from_address,
            "to_address": tx.to_address,
            "amount": tx.amount,
            "memo": tx.memo,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    content=json.dumps(payload),
                    headers={"Content-Type": "application/json"},
                    timeout=10.0,
                )
                if response.status_code == 200:
                    result = response.json()
                    return result.get("txHash", "unknown")
                else:
                    raise RuntimeError(f"Node RPC returned {response.status_code}: {response.text}")
        except httpx.ConnectError as e:
            raise RuntimeError(f"Cannot connect to node {target_node_id} at port {target.port}: {e}")

    async def get_blocks(self, since: int = 0) -> List[Block]:
        """Retrieve blocks from the chain (uses locally tracked blocks from events)."""
        return [b for b in self.blocks if b.block_number >= since]

    async def get_consensus_state(self) -> ConsensusState:
        """Return state: no consensus mechanism active."""
        leader = None
        if self.nodes:
            leader = next(iter(self.nodes.keys()))

        return ConsensusState(
            consensus_type="none",
            current_round=self._current_round,
            current_phase="none",
            current_leader=leader,
            validator_count=len(self.nodes),
            faulty_nodes=0,
            ready_validators=list(self.nodes.keys()),
            pending_votes={},
        )

    def subscribe_to_events(self, handler: Callable[[ChainEvent], None]) -> None:
        """Subscribe to events from this adapter."""
        self.event_handlers.append(handler)

    def _emit_event(self, event: ChainEvent):
        """Emit an event to all registered handlers."""
        for handler in self.event_handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Event handler error: {e}")

    async def start_stdout_reader(self, node_id: str, process: asyncio.subprocess.Process):
        """
        Read stdout from a node process and parse EVENT: lines into ChainEvents.
        This connects the real node process output to the event bridge.
        """
        if process.stdout is None:
            return

        task = asyncio.create_task(self._read_stdout(node_id, process))
        self._stdout_readers[node_id] = task

    async def _read_stdout(self, node_id: str, process: asyncio.subprocess.Process):
        """Continuously read stdout from a node process."""
        try:
            while True:
                if process.stdout is None:
                    break
                line = await process.stdout.readline()
                if not line:
                    break
                decoded = line.decode().strip()
                if decoded.startswith("EVENT:"):
                    json_str = decoded[6:]  # Remove "EVENT:" prefix
                    try:
                        event_data = json.loads(json_str)
                        event = ChainEvent(
                            event_type=event_data["type"],
                            timestamp=event_data.get("timestamp", int(time.time() * 1000)),
                            node_id=event_data.get("nodeId", node_id),
                            payload=event_data.get("payload", {}),
                        )
                        self._emit_event(event)

                        # Track blocks locally
                        if event.event_type == "BLOCK_COMMITTED":
                            self._current_round += 1
                            self.blocks.append(Block(
                                block_number=event.payload.get("blockHeight", 0),
                                block_hash=event.payload.get("hash", ""),
                                proposer=event.payload.get("proposerNodeId", node_id),
                                transactions=[],
                                timestamp=event.timestamp,
                                tx_count=event.payload.get("txCount", 0),
                            ))
                    except (json.JSONDecodeError, KeyError) as e:
                        logger.warning(f"Failed to parse event from {node_id}: {e}")
                else:
                    logger.debug(f"Node {node_id} stdout: {decoded}")
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Stdout reader error for {node_id}: {e}")
