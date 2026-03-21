"""
Event Bridge - Bridges chain node events to WebSocket frontend.
Subscribes to all adapter events and normalizes them into frontend-consumable format.
"""

from typing import List, Callable, Dict, Any, Optional
from dataclasses import asdict
import asyncio
import json
import time
import logging

# Import from sibling module (absolute import for direct script execution)
try:
    from chain_adapter import ChainEvent
except ImportError:
    from ..chain_adapter import ChainEvent

logger = logging.getLogger(__name__)

# All 11 spec-required event types
SPEC_EVENT_TYPES = {
    "NODE_JOINED",
    "NODE_OFFLINE",
    "TX_BROADCAST",
    "BLOCK_PROPOSED",
    "VOTE_CAST",
    "BLOCK_COMMITTED",
    "BLOCK_REJECTED",
    "CONSENSUS_PHASE",
    "SYNC_PROGRESS",
    "SYNC_COMPLETE",
    "LEADER_ELECTED",
}


class EventBridge:
    """
    Event bridge between blockchain adapters and WebSocket clients.

    Responsibilities:
    1. Subscribe to chain adapter events
    2. Normalize adapter-specific events to spec envelope: { type, timestamp, nodeId, payload }
    3. Buffer events for client reconnection (last 100)
    4. Broadcast events to all connected frontend clients
    5. Manage event history for replay/debugging
    """

    def __init__(self, buffer_size: int = 100):
        """
        Args:
            buffer_size: Number of recent events to keep in memory for reconnects
        """
        self.buffer_size = buffer_size
        self.event_buffer: List[ChainEvent] = []
        self.broadcast_callbacks: List[Callable] = []
        self.event_type_handlers: Dict[str, List[Callable]] = {}
        self._adapter = None

    def subscribe_to_adapter_events(self, adapter) -> None:
        """
        Subscribe this bridge to all events from a chain adapter.

        Args:
            adapter: IChainAdapter instance
        """
        self._adapter = adapter
        adapter.subscribe_to_events(self._on_adapter_event)
        logger.info("EventBridge subscribed to adapter events")

    def _on_adapter_event(self, event: ChainEvent) -> None:
        """
        Synchronous callback from the adapter.
        Schedules async processing on the event loop.
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(self.on_chain_event(event))
            else:
                loop.run_until_complete(self.on_chain_event(event))
        except RuntimeError:
            # No event loop available — log and skip
            logger.warning(f"Could not dispatch event {event.event_type}: no event loop")

    async def on_chain_event(self, event: ChainEvent) -> None:
        """
        Process an incoming chain event.
        Normalizes, buffers, and broadcasts to all connected clients.

        Args:
            event: ChainEvent from blockchain adapter or process manager
        """
        # Ensure timestamp is set
        if not event.timestamp or event.timestamp == 0:
            event.timestamp = int(time.time() * 1000)

        # Log non-spec event types as warnings
        if event.event_type not in SPEC_EVENT_TYPES:
            logger.warning(f"Non-spec event type received: {event.event_type}")

        # Buffer the event (FIFO, capped at buffer_size)
        self.event_buffer.append(event)
        if len(self.event_buffer) > self.buffer_size:
            self.event_buffer = self.event_buffer[-self.buffer_size:]

        # Fire type-specific handlers
        if event.event_type in self.event_type_handlers:
            for handler in self.event_type_handlers[event.event_type]:
                try:
                    result = handler(event)
                    if asyncio.iscoroutine(result):
                        await result
                except Exception as e:
                    logger.error(f"Type handler error for {event.event_type}: {e}")

        # Broadcast to all registered callbacks (WebSocket push)
        for callback in self.broadcast_callbacks:
            try:
                result = callback(event)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error(f"Broadcast callback error: {e}")

        logger.debug(f"Event processed: {event.event_type} from {event.node_id}")

    def register_broadcast_callback(self, callback: Callable) -> None:
        """
        Register a callback to receive all events.
        Used by WebSocket handler to push events to frontend.
        """
        self.broadcast_callbacks.append(callback)

    def unregister_broadcast_callback(self, callback: Callable) -> None:
        """Remove a previously registered broadcast callback."""
        if callback in self.broadcast_callbacks:
            self.broadcast_callbacks.remove(callback)

    def register_event_type_handler(self, event_type: str,
                                    handler: Callable) -> None:
        """Register a handler for specific event types."""
        if event_type not in self.event_type_handlers:
            self.event_type_handlers[event_type] = []
        self.event_type_handlers[event_type].append(handler)

    def unregister_event_type_handler(self, event_type: str,
                                      handler: Callable) -> None:
        """Remove a handler for a specific event type."""
        if event_type in self.event_type_handlers:
            handlers = self.event_type_handlers[event_type]
            if handler in handlers:
                handlers.remove(handler)

    def get_recent_events(self, count: int = 50) -> List[ChainEvent]:
        """
        Get recent events from buffer for client reconnection.

        Args:
            count: Number of recent events to return
        """
        return list(self.event_buffer[-count:])

    def get_events_since(self, timestamp: int) -> List[ChainEvent]:
        """
        Get all events since a given timestamp.

        Args:
            timestamp: Epoch timestamp in milliseconds
        """
        return [e for e in self.event_buffer if e.timestamp >= timestamp]

    async def clear_buffer(self) -> None:
        """Clear all buffered events."""
        self.event_buffer = []
        logger.info("Event buffer cleared")

    def export_event_trace(self) -> str:
        """
        Export all buffered events as JSON for debugging/analysis.

        Returns:
            JSON string of event trace array
        """
        events = []
        for e in self.event_buffer:
            events.append({
                "type": e.event_type,
                "timestamp": e.timestamp,
                "nodeId": e.node_id,
                "payload": e.payload,
            })
        return json.dumps(events, indent=2)

    def get_event_statistics(self) -> Dict[str, Any]:
        """Get statistics on buffered events."""
        type_counts: Dict[str, int] = {}
        for e in self.event_buffer:
            type_counts[e.event_type] = type_counts.get(e.event_type, 0) + 1

        timestamps = [e.timestamp for e in self.event_buffer]
        return {
            "total_events": len(self.event_buffer),
            "events_by_type": type_counts,
            "earliest_timestamp": min(timestamps) if timestamps else None,
            "latest_timestamp": max(timestamps) if timestamps else None,
            "buffer_capacity": self.buffer_size,
            "buffer_usage_pct": round(len(self.event_buffer) / self.buffer_size * 100, 1),
        }
