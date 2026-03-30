import socket
import subprocess
import os
import time
import requests

def get_free_port(start_port: int, max_port: int, used_ports: set) -> int:
    """Find a port that is both not in used_ports AND not currently bound by any process."""
    for port in range(start_port, max_port):
        if port in used_ports:
            continue
        # Check if anything is already listening on this port
        if is_port_in_use(port):
            continue
        # Double-check we can actually bind
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('127.0.0.1', port))
                return port
            except OSError:
                continue
    raise RuntimeError("No free ports available")

def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.1)  # 100ms timeout — critical on Windows where default is ~2s
        return s.connect_ex(('127.0.0.1', port)) == 0

def _get_all_node_urls():
    """Query the users DB for all registered node URLs."""
    try:
        import sqlite3
        db_path = os.path.join(os.path.dirname(__file__), "..", "data", "users.sqlite")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT node_url FROM users WHERE node_url IS NOT NULL AND node_url != ''")
        urls = [row[0] for row in cursor.fetchall()]
        conn.close()
        return urls
    except Exception:
        return []

def _wait_for_node_ready(api_port: int, timeout: int = 15) -> bool:
    """Poll the node's API until it responds, indicating it has started."""
    url = f"http://127.0.0.1:{api_port}/blocks"
    for _ in range(timeout):
        try:
            resp = requests.get(url, timeout=2)
            if resp.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(1)
    return False

def _wait_for_sync(api_port: int, peer_urls: list, timeout: int = 30) -> bool:
    """
    Wait until the new node's chain length matches the longest known peer.
    Returns True if synced, False if timed out.
    """
    if not peer_urls:
        return True  # No peers to sync from — we're the first node
    
    # Find the longest chain among existing peers
    max_peer_length = 1  # At minimum, genesis block
    for peer_url in peer_urls:
        try:
            resp = requests.get(f"{peer_url}/blocks", timeout=3)
            if resp.status_code == 200:
                peer_length = len(resp.json())
                if peer_length > max_peer_length:
                    max_peer_length = peer_length
        except Exception:
            continue
    
    if max_peer_length <= 1:
        return True  # All peers only have genesis — nothing to sync
    
    # Poll the new node until its chain length matches
    node_url = f"http://127.0.0.1:{api_port}/blocks"
    for _ in range(timeout):
        try:
            resp = requests.get(node_url, timeout=2)
            if resp.status_code == 200:
                our_length = len(resp.json())
                if our_length >= max_peer_length:
                    print(f"[NodeManager] Node on port {api_port} is synced! ({our_length} blocks)")
                    return True
                else:
                    print(f"[NodeManager] Syncing... {our_length}/{max_peer_length} blocks")
        except Exception:
            pass
        time.sleep(1)
    
    print(f"[NodeManager] Sync timed out after {timeout}s for port {api_port}")
    return False

from typing import Optional
def spawn_node(username: str, custom_db_path: str = "", api_port: Optional[int] = None, p2p_port: Optional[int] = None):
    """
    Finds available API and P2P ports (if not provided), then launches a new chainforge_node
    instance securely in the background.
    Returns the mapped node_url (e.g., http://127.0.0.1:8082).
    """
    # Scan currently assigned API ports from DB to avoid conflicts
    used_ports = set()
    try:
        import sqlite3
        db_path = os.path.join(os.path.dirname(__file__), "..", "data", "users.sqlite")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT node_url FROM users")
        for row in cursor.fetchall():
            if row[0] and ":" in row[0]:
                port = int(row[0].split(":")[-1])
                used_ports.add(port)
        conn.close()
    except Exception:
        pass

    # Find free ports if not specified
    if api_port is None:
        api_port = get_free_port(8080, 8100, used_ports)
    
    if p2p_port is None:
        current_used = used_ports.copy()
        current_used.add(api_port)
        p2p_port = get_free_port(5000, 5100, current_used)

    # Launch the process
    node_dir = os.path.join(os.path.dirname(__file__), "..", "chainforge_node")
    node_dir = os.path.normpath(node_dir)
    
    # Use custom path if provided, otherwise default to ../data/<username>.sqlite
    if custom_db_path and custom_db_path.strip():
        db_path = custom_db_path.strip()
    else:
        db_path = os.path.join(os.path.dirname(__file__), "..", "data", f"{username}.sqlite")
    
    # Resolve to absolute path
    if not os.path.isabs(db_path):
        db_path = os.path.normpath(os.path.join(os.path.dirname(__file__), db_path))
    
    # If user gave a directory path (no file extension), append <username>.sqlite
    if not os.path.splitext(db_path)[1]:
        db_path = os.path.join(db_path, f"{username}.sqlite")
    
    # Ensure parent directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    print(f"[NodeManager] Resolved DB path: {db_path}")
    
    # Build peer list from ALL existing running nodes (mesh topology)
    peer_urls = _get_all_node_urls()
    peer_list = []
    for url in peer_urls:
        host_port = url.replace("http://", "").replace("https://", "")
        peer_list.append(host_port)
    
    peers_str = ",".join(peer_list) if peer_list else ""

    cmd = [
        "python", "-u", "main.py",
        "--api-port", str(api_port),
        "--port", str(p2p_port),
        "--db-path", db_path
    ]
    
    # Only pass --peers if we have peers to connect to
    if peers_str:
        cmd.extend(["--peers", peers_str])

    print(f"[NodeManager] Spawning background node for '{username}' on API:{api_port} P2P:{p2p_port}")
    if peers_str:
        print(f"[NodeManager] Peers: {peers_str}")
    else:
        print(f"[NodeManager] No existing peers — this is the first node.")
    
    # Run in background
    creationflags = 0
    if os.name == 'nt':
        creationflags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
    
    # Ensure data dir for logs exists
    log_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    os.makedirs(log_dir, exist_ok=True)
        
    log_file = os.path.join(log_dir, f"{username}_node.log")
    with open(log_file, "w") as f:
        subprocess.Popen(
            cmd, 
            cwd=node_dir,
            stdout=f,
            stderr=subprocess.STDOUT,
            creationflags=creationflags
        )
    
    # Give the process a moment to start, but DON'T block the API request.
    # The frontend sync gate (polling /api/sync-status) handles the waiting.
    time.sleep(2)
    print(f"[NodeManager] Node process launched for '{username}'. Frontend will poll sync status.")
    
    return f"http://127.0.0.1:{api_port}"

def ensure_node_running(username: str, node_url: str, db_path: str = ""):
    """
    Checks if the node's API port is active. If not, spawns it.
    """
    if not node_url or ":" not in node_url:
        return
    
    try:
        port = int(node_url.split(":")[-1])
        if not is_port_in_use(port):
            print(f"[NodeManager] Node for {username} on port {port} is NOT running. Restarting with DB: {db_path or 'default'}...")
            spawn_node(username, custom_db_path=db_path, api_port=port)
        else:
            print(f"[NodeManager] Node for {username} is already running on port {port}.")
    except Exception as e:
        print(f"[NodeManager] Error checking/restarting node for {username}: {e}")

def get_sync_status(node_url: str) -> dict:
    """
    Check if a node is synced with the network.
    Returns { synced: bool, local_blocks: int, network_blocks: int }
    """
    local_blocks = 0
    network_max = 0
    
    # Get this node's block count
    try:
        resp = requests.get(f"{node_url}/blocks", timeout=3)
        if resp.status_code == 200:
            local_blocks = len(resp.json())
    except Exception:
        return {"synced": False, "local_blocks": 0, "network_blocks": 0, "node_online": False}
    
    # Get the max block count from all peers
    peer_urls = _get_all_node_urls()
    for peer_url in peer_urls:
        if peer_url == node_url:
            continue
        try:
            resp = requests.get(f"{peer_url}/blocks", timeout=2)
            if resp.status_code == 200:
                peer_length = len(resp.json())
                if peer_length > network_max:
                    network_max = peer_length
        except Exception:
            continue
    
    # If no other peers exist, we're synced by definition
    if network_max == 0:
        network_max = local_blocks
    
    return {
        "synced": local_blocks >= network_max,
        "local_blocks": local_blocks,
        "network_blocks": network_max,
        "node_online": True
    }
