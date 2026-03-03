"""
core/merkle.py

Binary Merkle Tree implementation for transaction inclusion proofs.

Provides:
  - compute_merkle_root(transactions)  -> root hash string
  - generate_merkle_proof(transactions, tx_index) -> list of (sibling_hash, direction)
  - verify_merkle_proof(tx_hash, proof, root) -> bool
"""
import hashlib
import json
from typing import List, Tuple, Any, Dict


def _hash_tx(tx: Dict[str, Any]) -> str:
    """Deterministic SHA-256 hash of a single transaction."""
    return hashlib.sha256(
        json.dumps(tx, sort_keys=True).encode()
    ).hexdigest()


def _hash_pair(left: str, right: str) -> str:
    """Hash two child hashes together into one parent hash."""
    return hashlib.sha256((left + right).encode()).hexdigest()


def _build_tree(leaves: List[str]) -> List[List[str]]:
    """
    Build the full Merkle tree from a list of leaf hashes.
    Returns a list of levels, index 0 = leaf level, last = root.
    """
    if not leaves:
        return [[hashlib.sha256(b"").hexdigest()]]

    level = list(leaves)
    tree = [level]

    while len(level) > 1:
        # Duplicate last leaf if odd count (standard Bitcoin-style padding)
        if len(level) % 2 == 1:
            level = level + [level[-1]]
        next_level = [_hash_pair(level[i], level[i + 1]) for i in range(0, len(level), 2)]
        tree.append(next_level)
        level = next_level

    return tree


def compute_merkle_root(transactions: List[Dict[str, Any]]) -> str:
    """
    Compute the Merkle root hash for a list of transactions.
    Returns an empty-block sentinel hash for empty tx lists.
    """
    if not transactions:
        return hashlib.sha256(b"empty").hexdigest()

    leaves = [_hash_tx(tx) for tx in transactions]
    tree = _build_tree(leaves)
    return tree[-1][0]  # Root is the only element of the top level


def generate_merkle_proof(
    transactions: List[Dict[str, Any]], tx_index: int
) -> List[Tuple[str, str]]:
    """
    Generate a Merkle inclusion proof for the transaction at `tx_index`.

    Returns a list of (sibling_hash, direction) tuples where direction is
    "left" or "right" indicating where the sibling sits relative to the
    current node. To reconstruct the root, work up from the leaf combining
    the current hash with each sibling in the given direction.

    Raises IndexError if tx_index is out of range.
    """
    if not transactions:
        raise ValueError("Cannot generate proof for empty transaction list")
    if tx_index < 0 or tx_index >= len(transactions):
        raise IndexError(f"tx_index {tx_index} out of range (0-{len(transactions)-1})")

    leaves = [_hash_tx(tx) for tx in transactions]
    tree = _build_tree(leaves)

    proof: List[Tuple[str, str]] = []
    index = tx_index

    for level in tree[:-1]:  # Walk from leaves up (exclude the root level)
        # Pad the level copy as the tree builder does
        padded = list(level)
        if len(padded) % 2 == 1:
            padded.append(padded[-1])

        if index % 2 == 0:
            # Current node is a left child — sibling is to the right
            sibling_index = index + 1
            proof.append((padded[sibling_index], "right"))
        else:
            # Current node is a right child — sibling is to the left
            sibling_index = index - 1
            proof.append((padded[sibling_index], "left"))

        index //= 2  # Move to the parent's index in the next level

    return proof


def verify_merkle_proof(
    tx: Dict[str, Any],
    proof: List[Tuple[str, str]],
    expected_root: str
) -> bool:
    """
    Verify a transaction's Merkle inclusion proof against the expected root.

    `tx`           — the transaction dict to verify.
    `proof`        — list of (sibling_hash, direction) as returned by generate_merkle_proof.
    `expected_root`— the merkle_root stored in the block header.

    Returns True if the proof is valid.
    """
    current_hash = _hash_tx(tx)

    for sibling_hash, direction in proof:
        if direction == "right":
            current_hash = _hash_pair(current_hash, sibling_hash)
        else:
            current_hash = _hash_pair(sibling_hash, current_hash)

    return current_hash == expected_root
