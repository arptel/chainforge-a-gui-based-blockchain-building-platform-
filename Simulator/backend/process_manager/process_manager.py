"""
Process Manager - Manages lifecycle of blockchain node processes.
Spawns, monitors, and terminates real ChainForge node subprocesses.
"""

from typing import Dict, Optional, Callable
from dataclasses import dataclass, field
import asyncio
import time
import logging
import uuid

logger = logging.getLogger(__name__)

# Base port for dynamically assigned node ports
BASE_PORT = 8600


@dataclass
class ManagedProcess:
    """Represents a managed node process."""
    node_id: str
    role: str
    port: int
    pid: Optional[int] = None
    status: str = "initializing"  # initializing, running, stopped, error
    start_time: float = 0
    stop_time: Optional[float] = None
    process: Optional[asyncio.subprocess.Process] = field(default=None, repr=False)


class ProcessManager:
    """
    Manages spawning, monitoring, and terminating blockchain node processes.
    Responsible for enforcing max_nodes limit and handling process lifecycle.
    """

    def __init__(self, max_nodes: int = 0, node_timeout_sec: int = 30):
        """
        Args:
            max_nodes: Maximum number of concurrent nodes (0 = unlimited)
            node_timeout_sec: Timeout for node startup in seconds
        """
        self.max_nodes = max_nodes
        self.node_timeout_sec = node_timeout_sec
        self.processes: Dict[str, ManagedProcess] = {}
        self._next_port = BASE_PORT
        self._port_lock = asyncio.Lock()
        self.on_node_ready: Optional[Callable] = None
        self.on_node_offline: Optional[Callable] = None
        self._monitor_tasks: Dict[str, asyncio.Task] = {}

    async def _assign_port(self) -> int:
        """Assign the next available port."""
        async with self._port_lock:
            port = self._next_port
            self._next_port += 1
            return port

    async def spawn_node_process(
        self,
        role: str,
        consensus: str = "none",
        block_time_ms: int = 3000,
        node_id: Optional[str] = None,
    ) -> ManagedProcess:
        """
        Spawn a new blockchain node process.

        Args:
            role: Node role (full, validator, light, etc.)
            consensus: Consensus algorithm name
            block_time_ms: Target block time in ms
            node_id: Optional specific node ID (auto-generated if not provided)

        Returns:
            ManagedProcess instance

        Raises:
            RuntimeError: If max_nodes limit reached or process spawn fails
        """
        # Generate node ID if not provided
        if node_id is None:
            node_id = f"node-{len(self.processes) + 1}"

        # Check if node_id already exists
        if node_id in self.processes:
            raise ValueError(f"Node '{node_id}' already exists.")

        # Enforce max_nodes limit
        active_count = sum(1 for p in self.processes.values() if p.status in ("initializing", "running"))
        if self.max_nodes > 0 and active_count >= self.max_nodes:
            raise RuntimeError(
                f"Maximum node limit ({self.max_nodes}) reached for this configuration."
            )

        # Assign a dynamic port
        port = await self._assign_port()

        # Create the managed process entry
        managed = ManagedProcess(
            node_id=node_id,
            role=role,
            port=port,
            status="initializing",
            start_time=time.time(),
        )

        # Build the command to spawn the ChainForge node process.
        # The actual ChainForge node binary/script is expected to accept these flags.
        # We use a simulated node process that outputs events to stdout.
        # For a real deployment, replace this with the actual ChainForge node binary.
        cmd = [
            "python", "-u",  # unbuffered output
            _get_node_script_path(),
            "--node-id", node_id,
            "--role", role,
            "--port", str(port),
            "--consensus", consensus,
            "--block-time-ms", str(block_time_ms),
        ]

        logger.info(f"Spawning node process: {node_id} (role={role}, port={port})")

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            managed.process = process
            managed.pid = process.pid
            logger.info(f"Node {node_id} spawned with PID {process.pid}")
        except FileNotFoundError as e:
            managed.status = "error"
            self.processes[node_id] = managed
            raise RuntimeError(f"Failed to spawn node process: {e}")
        except Exception as e:
            managed.status = "error"
            self.processes[node_id] = managed
            raise RuntimeError(f"Failed to spawn node process: {e}")

        self.processes[node_id] = managed

        # Wait for ready signal from the process
        try:
            ready = await self._wait_for_ready(managed)
            if ready:
                managed.status = "running"
                logger.info(f"Node {node_id} is ready (PID={managed.pid}, port={port})")
                if self.on_node_ready:
                    await self.on_node_ready(managed)
            else:
                managed.status = "error"
                logger.error(f"Node {node_id} failed to become ready within timeout")
                raise RuntimeError(
                    f"Node {node_id} failed to start: timed out waiting for ready signal "
                    f"after {self.node_timeout_sec} seconds."
                )
        except RuntimeError:
            raise
        except Exception as e:
            managed.status = "error"
            raise RuntimeError(f"Node {node_id} startup failed: {e}")

        # Start background monitor for process health
        task = asyncio.create_task(self._monitor_process(node_id))
        self._monitor_tasks[node_id] = task

        return managed

    async def _wait_for_ready(self, managed: ManagedProcess) -> bool:
        """
        Wait for the node process to output a READY signal on stdout.
        Returns True if ready, False if timeout.
        """
        if managed.process is None or managed.process.stdout is None:
            return False

        try:
            deadline = time.time() + self.node_timeout_sec
            while time.time() < deadline:
                try:
                    line = await asyncio.wait_for(
                        managed.process.stdout.readline(),
                        timeout=min(1.0, deadline - time.time())
                    )
                    if not line:
                        # Process ended
                        return False
                    decoded = line.decode().strip()
                    logger.debug(f"Node {managed.node_id} stdout: {decoded}")
                    if "READY" in decoded.upper():
                        return True
                except asyncio.TimeoutError:
                    # Check if process is still alive
                    if managed.process.returncode is not None:
                        return False
                    continue
            return False
        except Exception as e:
            logger.error(f"Error waiting for ready signal from {managed.node_id}: {e}")
            return False

    async def terminate_node_process(self, node_id: str, force: bool = False) -> None:
        """
        Terminate a running node process.

        Args:
            node_id: Unique identifier of node to terminate
            force: If True, use kill() instead of terminate()
        """
        if node_id not in self.processes:
            raise ValueError(f"Node '{node_id}' not found.")

        managed = self.processes[node_id]
        if managed.status == "stopped":
            raise ValueError(f"Node '{node_id}' is already stopped.")

        # Cancel the monitor task
        if node_id in self._monitor_tasks:
            self._monitor_tasks[node_id].cancel()
            del self._monitor_tasks[node_id]

        if managed.process is not None and managed.process.returncode is None:
            try:
                if force:
                    managed.process.kill()
                else:
                    managed.process.terminate()

                # Wait for process to exit (max 5 seconds)
                try:
                    await asyncio.wait_for(managed.process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    # Force kill if graceful termination didn't work
                    managed.process.kill()
                    await managed.process.wait()

                logger.info(f"Node {node_id} terminated (PID={managed.pid})")
            except ProcessLookupError:
                logger.warning(f"Node {node_id} process already gone")
            except Exception as e:
                raise RuntimeError(f"Failed to terminate node {node_id}: {e}")

        managed.status = "stopped"
        managed.stop_time = time.time()

        if self.on_node_offline:
            await self.on_node_offline(managed, "terminated by user")

    async def terminate_all_nodes(self, force: bool = False) -> None:
        """Terminate all running node processes."""
        node_ids = list(self.processes.keys())
        for node_id in node_ids:
            if self.processes[node_id].status in ("initializing", "running"):
                try:
                    await self.terminate_node_process(node_id, force=force)
                except Exception as e:
                    logger.error(f"Error terminating node {node_id}: {e}")

    async def _monitor_process(self, node_id: str) -> None:
        """
        Background task: monitor a node process for unexpected exits.
        """
        if node_id not in self.processes:
            return

        managed = self.processes[node_id]
        if managed.process is None:
            return

        try:
            # Wait for the process to exit
            await managed.process.wait()

            # If we get here, the process exited
            if managed.status == "running":
                # Unexpected exit
                exit_code = managed.process.returncode
                managed.status = "error"
                managed.stop_time = time.time()
                reason = f"Process exited unexpectedly with code {exit_code}"
                logger.error(f"Node {node_id}: {reason}")

                if self.on_node_offline:
                    await self.on_node_offline(managed, reason)
        except asyncio.CancelledError:
            # Monitor was cancelled (normal during terminate)
            pass
        except Exception as e:
            logger.error(f"Monitor error for node {node_id}: {e}")

    def get_process_status(self, node_id: str) -> Optional[str]:
        """Get current status of a node process."""
        if node_id in self.processes:
            return self.processes[node_id].status
        return None

    def get_process_info(self, node_id: str) -> Optional[ManagedProcess]:
        """Get full info for a node process."""
        return self.processes.get(node_id)

    def get_all_processes(self) -> Dict[str, ManagedProcess]:
        """Get all managed processes."""
        return dict(self.processes)

    def set_node_ready_callback(self, callback: Callable) -> None:
        """Set callback for when a process becomes ready."""
        self.on_node_ready = callback

    def set_node_offline_callback(self, callback: Callable) -> None:
        """Set callback for when a process goes offline."""
        self.on_node_offline = callback


def _get_node_script_path() -> str:
    """Get path to the node simulation script."""
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # The node script lives alongside main in the backend directory
    # Go up from process_manager/ to backend/
    backend_dir = os.path.dirname(script_dir)
    return os.path.join(backend_dir, "chainforge_node.py")
