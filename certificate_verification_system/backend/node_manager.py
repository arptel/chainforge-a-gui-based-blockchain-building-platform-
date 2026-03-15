import socket
import subprocess
import os
import time

def get_free_port(start_port: int, max_port: int, used_ports: set) -> int:
    for port in range(start_port, max_port):
        if port in used_ports:
            continue
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('127.0.0.1', port))
                return port
            except OSError:
                continue
    raise RuntimeError("No free ports available")

def spawn_node(username: str, custom_db_path: str = ""):
    """
    Finds available API and P2P ports, then launches a new chainforge_node
    instance securely in the background.
    If custom_db_path is provided, uses it for the chain database location.
    Returns the mapped node_url (e.g., http://127.0.0.1:8082).
    """
    # Quick scan of currently assigned API ports to avoid race conditions
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

    # Find free ports
    api_port = get_free_port(8080, 8100, used_ports)
    # P2P ports usually start at 5000
    p2p_port = get_free_port(5000, 5100, used_ports)

    # Launch the process
    node_dir = os.path.join(os.path.dirname(__file__), "..", "chainforge_node")
    node_dir = os.path.normpath(node_dir)
    
    # Use custom path if provided, otherwise default to ../data/<username>.sqlite
    if custom_db_path and custom_db_path.strip():
        db_path = custom_db_path.strip()
    else:
        db_path = os.path.join(os.path.dirname(__file__), "..", "data", f"{username}.sqlite")
    
    # Resolve to absolute path (relative paths resolved from backend/ dir)
    if not os.path.isabs(db_path):
        db_path = os.path.normpath(os.path.join(os.path.dirname(__file__), db_path))
    
    # If user gave a directory path (no file extension), append <username>.sqlite
    if not os.path.splitext(db_path)[1]:
        db_path = os.path.join(db_path, f"{username}.sqlite")
    
    # Ensure parent directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    print(f"[NodeManager] Resolved DB path: {db_path}")
    
    # The new node connects to Node A as its initial peer
    # Pass absolute path so there's no CWD ambiguity
    cmd = [
        "python", "-u", "main.py",
        "--api-port", str(api_port),
        "--port", str(p2p_port),
        "--peers", "127.0.0.1:8080",
        "--db-path", db_path
    ]

    print(f"[NodeManager] Spawning background node for '{username}' on API:{api_port} P2P:{p2p_port}")
    
    # Run in background
    creationflags = 0
    if os.name == 'nt':
        creationflags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
        
    log_file = os.path.join(os.path.dirname(__file__), "..", "data", f"{username}_node.log")
    with open(log_file, "w") as f:
        subprocess.Popen(
            cmd, 
            cwd=node_dir,
            stdout=f,
            stderr=subprocess.STDOUT,
            creationflags=creationflags
        )
    
    # Give it seconds to boot up and bind to its port
    time.sleep(3)
    
    return f"http://127.0.0.1:{api_port}"
