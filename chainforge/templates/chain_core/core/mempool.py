"""
core/mempool.py

A dedicated Mempool (transaction pool) with:
- Nonce tracking per sender to prevent replay attacks
- Gas fee enforcement and priority ordering (highest gas_price first)
- Duplicate detection
"""
from typing import Dict, List, Any, Optional
import threading


class Mempool:
    """
    Thread-safe transaction mempool with nonce and gas fee validation.
    
    Transaction format expected:
    {
        "from":      <sender address / public key>,
        "to":        <receiver>,
        "amount":    <value>,
        "nonce":     <int, monotonically increasing per sender>,
        "gas_price": <int, tokens willing to pay per gas unit>,
        "gas_limit": <int, max gas units for this tx>,
        "type":      "transfer" | "contract_call",
        ...
    }
    """

    def __init__(self, min_gas_price: int = 0):
        # Pending transactions list (maintained sorted by gas_price desc)
        self._txs: List[Dict[str, Any]] = []

        # Tracks the LAST CONFIRMED nonce per address (from finalized blocks)
        self.confirmed_nonces: Dict[str, int] = {}

        # min gas price floor (0 = optional, projects without currency can set 0)
        self.min_gas_price = min_gas_price

        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add(self, tx: Dict[str, Any]) -> tuple:
        """
        Validate and add a transaction to the mempool.
        Returns (success: bool, reason: str).
        
        If 'nonce' is not present in tx, one is auto-assigned (backward compat).
        If 'nonce' is present, strict replay-attack and ordering rules apply.
        """
        with self._lock:
            sender = tx.get("from")
            if not sender:
                return False, "Missing 'from' field"

            # --- Nonce handling ---
            nonce = tx.get("nonce")
            expected_nonce = self.confirmed_nonces.get(sender, 0) + 1

            if nonce is None:
                # Backward-compat: auto-assign the next valid nonce
                pending_nonces = [t.get("nonce", 0) for t in self._txs if t.get("from") == sender]
                auto_nonce = max(pending_nonces, default=self.confirmed_nonces.get(sender, 0)) + 1
                tx = dict(tx)  # shallow copy — don't mutate caller's dict
                tx["nonce"] = auto_nonce
                nonce = auto_nonce
            else:
                # Explicit nonce — enforce strict rules
                for existing in self._txs:
                    if existing.get("from") == sender and existing.get("nonce") == nonce:
                        return False, f"Duplicate transaction: nonce {nonce} already in mempool for {sender}"

                if nonce < expected_nonce:
                    return False, f"Replay attack: nonce {nonce} already used (expected >= {expected_nonce})"

                if nonce > expected_nonce + 9:
                    return False, f"Nonce too far in future: got {nonce}, expected {expected_nonce}"

            # --- Gas fee check ---
            gas_price = tx.get("gas_price", 0)
            if gas_price < self.min_gas_price:
                return False, f"Gas price {gas_price} below minimum {self.min_gas_price}"

            # --- Add and re-sort by gas_price descending ---
            self._txs.append(tx)
            self._txs.sort(key=lambda t: t.get("gas_price", 0), reverse=True)

            return True, "ok"

    def get_pending(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Return up to `limit` transactions ordered by gas_price descending."""
        with self._lock:
            return list(self._txs[:limit])

    def remove(self, confirmed_txs: List[Dict[str, Any]]):
        """
        Remove confirmed transactions from the mempool and update nonce state.
        Called after a block is finalized.
        """
        with self._lock:
            for tx in confirmed_txs:
                sender = tx.get("from")
                nonce = tx.get("nonce")
                # Update confirmed nonce
                if sender and nonce is not None:
                    if nonce > self.confirmed_nonces.get(sender, 0):
                        self.confirmed_nonces[sender] = nonce
                # Remove from pending list
                self._txs = [t for t in self._txs if not (
                    t.get("from") == tx.get("from") and
                    t.get("nonce") == tx.get("nonce")
                )]

    def set_confirmed_nonces(self, nonces: Dict[str, int]):
        """
        Bulk-set the confirmed nonce state (used during chain reorg / state rebuild).
        """
        with self._lock:
            self.confirmed_nonces = dict(nonces)
            # Prune any pending txs whose nonces are now stale
            self._txs = [
                t for t in self._txs
                if t.get("nonce", 0) > self.confirmed_nonces.get(t.get("from", ""), 0)
            ]

    def clear(self):
        """Clear the mempool entirely (e.g. on catastrophic reorg)."""
        with self._lock:
            self._txs = []

    def get_next_nonce(self, address: str) -> int:
        """Return the next valid nonce for an address."""
        with self._lock:
            confirmed = self.confirmed_nonces.get(address, 0)
            # Also check if there's already a pending tx with a higher nonce
            pending_nonces = [
                t.get("nonce", 0) for t in self._txs
                if t.get("from") == address
            ]
            if pending_nonces:
                return max(max(pending_nonces), confirmed) + 1
            return confirmed + 1

    def size(self) -> int:
        with self._lock:
            return len(self._txs)

    def to_dict(self) -> List[Dict[str, Any]]:
        """Serializable snapshot of the mempool."""
        with self._lock:
            return list(self._txs)
