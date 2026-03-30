"""
core/persistence.py

SQLite-backed persistence for blocks and account state.
Replaces the fragile blocks.json / state.json approach with
atomic single-row inserts and transactional bulk writes.

Schema
------
  blocks(idx INTEGER PRIMARY KEY, hash TEXT, data TEXT)
  state(key TEXT PRIMARY KEY, value TEXT)
"""
import os
import json
import sqlite3
import logging
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)


class Persistence:
    def __init__(self, db_path: str = "data/chainforge.db"):
        os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True)
        self.db_path = db_path
        self._init_db()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS blocks (
                    idx  INTEGER PRIMARY KEY,
                    hash TEXT NOT NULL,
                    data TEXT NOT NULL
                )
            """)
            
            # Clean up duplicate blocks from legacy databases
            conn.execute("""
                DELETE FROM blocks 
                WHERE rowid NOT IN (
                    SELECT MIN(rowid) 
                    FROM blocks 
                    GROUP BY idx
                )
            """)
            
            # Enforce uniqueness if idx isn't already primary key in legacy schema
            conn.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_unique ON blocks(idx)
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS state (
                    key   TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)
            conn.commit()

    # ------------------------------------------------------------------
    # Block persistence
    # ------------------------------------------------------------------

    def save_block(self, block) -> None:
        """Atomically upsert a block by index."""
        data_json = json.dumps(block.to_dict())
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO blocks (idx, hash, data) VALUES (?, ?, ?)",
                (block.index, block.hash, data_json)
            )
            conn.commit()
        logger.debug(f"[DB] Saved block {block.index} ({block.hash[:8]}...)")

    def save_blocks(self, blocks: list) -> None:
        """Bulk-upsert a list of blocks in a single transaction (fast reorg)."""
        rows = [(b.index, b.hash, json.dumps(b.to_dict())) for b in blocks]
        with self._connect() as conn:
            conn.executemany(
                "INSERT OR REPLACE INTO blocks (idx, hash, data) VALUES (?, ?, ?)",
                rows
            )
            conn.commit()
        logger.debug(f"[DB] Bulk-saved {len(blocks)} blocks.")

    def load_all_blocks(self) -> list:
        """Return all Block objects ordered by index (ignores duplicates based on idx)."""
        from core.block import Block
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT data FROM blocks ORDER BY idx ASC"
            ).fetchall()
        
        block_map = {}
        for row in rows:
            try:
                data = json.loads(row["data"])
                block = Block.from_dict(data)
                if block.index not in block_map:
                    block_map[block.index] = block
            except Exception as e:
                logger.error(f"[DB] Failed to deserialize block: {e}")
                
        # Return sorted by index strictly
        return [block_map[idx] for idx in sorted(block_map.keys())]

    def load_last_block(self) -> Optional[Any]:
        """Return the Block with the highest index, or None."""
        from core.block import Block
        with self._connect() as conn:
            row = conn.execute(
                "SELECT data FROM blocks ORDER BY idx DESC LIMIT 1"
            ).fetchone()
        if not row:
            return None
        try:
            return Block.from_dict(json.loads(row["data"]))
        except Exception as e:
            logger.error(f"[DB] Failed to deserialize last block: {e}")
            return None

    def block_count(self) -> int:
        with self._connect() as conn:
            return conn.execute("SELECT COUNT(*) FROM blocks").fetchone()[0]

    def delete_blocks_after(self, index: int) -> None:
        """Remove all blocks with idx > index (used during reorg)."""
        with self._connect() as conn:
            conn.execute("DELETE FROM blocks WHERE idx > ?", (index,))
            conn.commit()

    # ------------------------------------------------------------------
    # State persistence
    # ------------------------------------------------------------------

    def save_state(self, state: Dict[str, Any]) -> None:
        """Atomically replace the entire account state."""
        rows = [(str(k), json.dumps(v)) for k, v in state.items()]
        with self._connect() as conn:
            conn.execute("DELETE FROM state")
            if rows:
                conn.executemany(
                    "INSERT INTO state (key, value) VALUES (?, ?)", rows
                )
            conn.commit()

    def load_state(self) -> Dict[str, Any]:
        with self._connect() as conn:
            rows = conn.execute("SELECT key, value FROM state").fetchall()
        return {row["key"]: json.loads(row["value"]) for row in rows}

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def wipe(self) -> None:
        """Clear all data (used in tests)."""
        with self._connect() as conn:
            conn.execute("DELETE FROM blocks")
            conn.execute("DELETE FROM state")
            conn.commit()
