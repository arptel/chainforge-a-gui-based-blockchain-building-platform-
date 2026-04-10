import asyncio
import json
import threading
import websockets
from typing import List, Any, Set

import sys
import os

try:
    from interfaces.network import NetworkInterface  # type: ignore
except ImportError:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
    from interfaces.network import NetworkInterface  # type: ignore

class P2PNetwork(NetworkInterface):
    """
    WebSocket-based P2P Network implementation.
    Maintains persistent, real-time bi-directional connections with peers.
    """
    def __init__(self, port: int = 5000, api_port: int = 8000):
        # Store active websocket connections
        self.active_connections: set = set()
        # Keep track of known peer URIs to avoid duplicates
        self.known_peers: set = set()
        self.port = port
        
        # Build our own public URI for gossip (assuming localhost for demo)
        self.my_uri = f"ws://127.0.0.1:{api_port}/ws"
        # Optional: Add myself to known_peers to avoid dialing myself if gossiped back
        self.known_peers.add(self.my_uri)
        
        # We need a reference to the node's Blockchain to process incoming logic
        self.node_chain = None
        self.sync_module = None
        self.consensus_module = None
        
    def set_chain(self, chain):
        self.node_chain = chain

    def set_sync_module(self, sync_module: Any):
        self.sync_module = sync_module

    def set_consensus_module(self, consensus_module: Any):
        """Bind a consensus module to the network for message routing."""
        self.consensus_module = consensus_module
        if hasattr(consensus_module, 'set_network'):
            consensus_module.set_network(self)
        elif hasattr(consensus_module, 'network'):
            consensus_module.network = self

    async def start_server(self):
        # Inbound networking is fully managed by FastAPI mounting the /ws endpoint.
        # No stand-alone server loop is needed here; we explicitly bypass it.
        pass

    def _broadcast_ws(self, message: dict):
        """
        Internal: Broadcast a message to all connected peers.
        Safe to call from both sync threads AND inside an async event loop.
        """
        if not self.active_connections:
            return
            
        msg_str = json.dumps(message)
        dead_connections = []
        
        for ws, loop in list(self.active_connections):
            try:
                async def _send(socket, msg):
                    try:
                        if hasattr(socket, 'send_text'):   # FastAPI WebSocket (inbound)
                            await socket.send_text(msg)
                        else:                              # websockets client (outbound)
                            await socket.send(msg)
                    except Exception as e:
                        print(f"[P2P] Send failed: {e}")
                
                try:
                    # Check if we're already inside a running event loop
                    running_loop = asyncio.get_event_loop()
                    if running_loop.is_running():
                        # We're inside an async context (e.g. uvicorn handler): schedule as a task
                        asyncio.ensure_future(_send(ws, msg_str), loop=loop)
                    elif loop is not None:
                        asyncio.run_coroutine_threadsafe(_send(ws, msg_str), loop)
                except RuntimeError:
                    # No event loop in this thread — use threadsafe dispatch to the target loop
                    if loop is not None:
                        asyncio.run_coroutine_threadsafe(_send(ws, msg_str), loop)
                    
            except Exception as e:
                print(f"[P2P] Failed to schedule broadcast to peer: {e}")
                dead_connections.append((ws, loop))

        # Cleanup
        for dead in dead_connections:
            self.active_connections.discard(dead)

    def trigger_sync_request(self, last_index: int):
        """
        Helper method to fire a sync request safely using the active loops.
        """
        sync_req = {"type": "SYNC_REQUEST", "data": {"last_index": last_index}}
        
        def _job():
            import time
            for _ in range(15):
                if self.active_connections:
                    self._broadcast_ws(sync_req)
                    print(f"[P2P Sync] Queued out SYNC_REQUEST via broadcast.")
                    return
                time.sleep(1)
            print("[P2P Sync] Timed out waiting for connections to dispatch SYNC_REQUEST.")
            
        import threading
        threading.Thread(target=_job, daemon=True).start()

    def broadcast(self, message: dict):
        self._broadcast_ws(message)

    def broadcast_node_address(self, peer_uri: str):
        """Broadcast a newly discovered peer URI to all known connections."""
        payload = {"type": "PEER_DISCOVERY", "data": peer_uri}
        self._broadcast_ws(payload)

    def broadcast_transaction(self, tx: dict):
        """Broadcast a transaction instantly to all connected peers"""
        payload = {"type": "NEW_TRANSACTION", "data": tx}
        self._broadcast_ws(payload)

    def broadcast_block(self, block: Any):
        """Broadcast a new block instantly to all connected peers"""
        payload = {"type": "NEW_BLOCK", "data": block.to_dict()}
        self._broadcast_ws(payload)

    def connect_to_peer(self, peer_address: str):
        """Dial OUT to a peer and establish a persistent websocket."""
        if peer_address and peer_address not in self.known_peers:
            self.known_peers.add(peer_address)
            
            # Ensure it's a websocket URI
            uri = peer_address
            if uri.startswith("http"):
                uri = uri.replace("http", "ws")
            if not uri.startswith("ws"):
                uri = f"ws://{uri}"
            if not uri.endswith("/ws"):
                uri = f"{uri}/ws"
                
            print(f"[P2P] Dialing peer: {uri} ...")
            
            # Start a background thread to maintain this outbound connection
            threading.Thread(target=self._maintain_outbound_connection, args=(uri,), daemon=True).start()

    def _maintain_outbound_connection(self, uri: str):
        """Runs in a background thread to dial out and listen to a peer asynchronously."""
        async def _connect_and_listen():
            loop = asyncio.get_running_loop()
            try:
                async with websockets.connect(uri) as ws:
                    print(f"[P2P] Successfully connected OUT to {uri}")
                    self.active_connections.add((ws, loop))
                    
                    # Say hello to this specific peer
                    hello_msg = json.dumps({"type": "PEER_DISCOVERY", "data": self.my_uri})
                    await ws.send(hello_msg)
                    
                    # Auto-trigger blockchain sync now that we have a peer!
                    if self.sync_module and hasattr(self.sync_module, 'sync_chain'):
                        print(f"[P2P] Scheduling initial sync via newly connected peer {uri}...")
                        loop.call_later(2.0, self.sync_module.sync_chain)
                    
                    # Listen indefinitely to whatever this peer sends us
                    while True:
                        try:
                            message = await ws.recv()
                            response = await self._handle_incoming_message(message)
                            if response:  # e.g. SYNC_RESPONSE for a SYNC_REQUEST
                                await ws.send(response)
                        except websockets.exceptions.ConnectionClosed:
                            print(f"[P2P] Peer {uri} disconnected.")
                            break
            except Exception as e:
                print(f"[P2P] Could not connect to {uri}: {e}")
            finally:
                if 'ws' in locals():
                    self.active_connections.discard((ws, loop))
                    
        # Run the async loop for this specific connection
        asyncio.run(_connect_and_listen())

    async def _handle_incoming_message(self, message: str, websocket=None):
        """
        Route incoming JSON messages to the appropriate module.
        """
        if not self.node_chain:
            return None
            
        try:
            data = json.loads(message)
            msg_type = data.get("type", "")

            # 1. Route Consensus Messages (PBFT, Paxos, etc.)
            if self.consensus_module and msg_type.startswith(("PBFT_", "PAXOS_", "TENDERMINT_", "HOTSTUFF_")):
                self.consensus_module.handle_consensus_message(data)
                return

            msg_data = data.get("data")
            
            if msg_type == "PEER_DISCOVERY":
                incoming_uri = msg_data
                # Whitelist enforcement
                if "system.whitelist" in self.node_chain.state:
                    whitelist = self.node_chain.state["system.whitelist"]
                    # Usually URIs or IPs would be mapped. For demo, we just print notice if not whitelisted.
                    if incoming_uri not in whitelist:
                        print(f"[P2P] Peer {incoming_uri} rejected. Not in system whitelist.")
                        return json.dumps({"type": "REJECTED", "reason": "Not whitelisted"})
                
                if incoming_uri != self.my_uri and incoming_uri not in self.known_peers:
                    print(f"[P2P Discovery] Discovered new peer: {incoming_uri}")
                    self.connect_to_peer(incoming_uri)
                    self.broadcast_node_address(incoming_uri)
                    
            elif msg_type == "SYNC_REQUEST":
                if hasattr(self.sync_module, 'handle_sync_request'):
                    response_payload = self.sync_module.handle_sync_request(msg_data)
                    if response_payload: return response_payload
                else:
                    last_index = msg_data.get("last_index", 0)
                    missing_blocks = [b.to_dict() for b in self.node_chain.chain if b.index > last_index]
                    if missing_blocks:
                        print(f"[P2P Sync] Serving {len(missing_blocks)} historical blocks to peer.")
                        return json.dumps({"type": "SYNC_RESPONSE", "data": missing_blocks})
                    
            elif msg_type == "SYNC_RESPONSE":
                if self.sync_module and hasattr(self.sync_module, 'handle_sync_response'):
                    new_request = self.sync_module.handle_sync_response(msg_data)
                    if new_request: return new_request
                    
            elif msg_type == "NEW_TRANSACTION":
                if msg_data not in self.node_chain.pending_transactions:
                    self.node_chain.add_transaction(msg_data)
                    
            elif msg_type == "NEW_BLOCK":
                from core.block import Block
                block = Block.from_dict(msg_data)
                
                # Gap detection logic
                if block.index > self.node_chain.last_block.index + 1:
                    print(f"[P2P] Detected gap! We are at {self.node_chain.last_block.index}, received {block.index}.")
                    if self.sync_module and hasattr(self.sync_module, 'handle_gap'):
                        gap_request = self.sync_module.handle_gap(block.index)
                        if gap_request: return gap_request
                    else:
                        return json.dumps({"type": "SYNC_REQUEST", "data": {"last_index": self.node_chain.last_block.index}})
                elif block.index <= self.node_chain.last_block.index:
                    return None
                
                success = self.node_chain.add_block(block)
                if success:
                    print(f"[P2P] Successfully appended block {block.index} from peer network!")
                    # Gossip protocol: Re-broadcast the new block to all other peers so the network stays synced
                    self.broadcast_block(block)
                    
                    if self.node_chain.role in ["full", "miner"]:
                        for b_tx in block.transactions:
                            if b_tx in self.node_chain.pending_transactions:
                                self.node_chain.pending_transactions.remove(b_tx)
                                
        except Exception as e:
            print(f"[P2P] Failed to process incoming message: {e}")

    def add_incoming_connection(self, websocket):
        """Called by FastAPI when a peer dials IN to us."""
        loop = asyncio.get_running_loop()
        self.active_connections.add((websocket, loop))

    def remove_incoming_connection(self, websocket):
        """Called by FastAPI when a peer drops the connection."""
        to_remove = [c for c in self.active_connections if c[0] == websocket]
        for c in to_remove:
            self.active_connections.discard(c)

    def get_peers(self) -> List[str]:
        return list(self.known_peers)
