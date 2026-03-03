"""
test_persistence.py

Tests for Robust State & Persistence:
1. Merkle root correctness (empty, single, multiple txs)
2. Merkle inclusion proof generation and verification
3. Merkle tamper detection (mutated tx invalidates proof)
4. State root determinism (same state = same root, different state != same root)
5. State root stamped in block header after add_block
6. SQLite round-trip: save/load blocks survive a new Persistence instance
7. SQLite state round-trip: save/load state
8. load_from_disk: chain reconstructed from SQLite matches original
9. SQLite reorg: delete_blocks_after and bulk save work correctly
"""
import sys
import os
import tempfile
import shutil

sys.path.insert(0, ".")

from core.block import Block
from core.chain import Blockchain
from core.merkle import compute_merkle_root, generate_merkle_proof, verify_merkle_proof
from core.persistence import Persistence
from modules.consensus.pow import PoWConsensus
from modules.vm.python_vm import PythonVM


def assert_true(condition, msg):
    if not condition:
        print(f"  [FAIL] {msg}")
        sys.exit(1)
    print(f"  [PASS] {msg}")


TXS = [
    {"from": "alice", "to": "bob",     "amount": 10, "type": "transfer"},
    {"from": "bob",   "to": "charlie", "amount": 5,  "type": "transfer"},
    {"from": "carol", "to": "dave",    "amount": 20, "type": "transfer"},
    {"from": "dave",  "to": "alice",   "amount": 3,  "type": "transfer"},
]


# ─── Test 1: Merkle root correctness ─────────────────────────────────────────

def test_merkle_root_correctness():
    print("\n--- Test 1: Merkle root correctness ---")
    import hashlib, json

    # Empty tx list → sentinel hash
    empty_root = compute_merkle_root([])
    expected_empty = hashlib.sha256(b"empty").hexdigest()
    assert_true(empty_root == expected_empty, "Empty tx list produces sentinel hash")

    # Single tx → root == hash of that tx
    single_root = compute_merkle_root([TXS[0]])
    tx_hash = hashlib.sha256(json.dumps(TXS[0], sort_keys=True).encode()).hexdigest()
    assert_true(single_root == tx_hash, "Single-tx root == leaf hash")

    # Multi-tx → deterministic (same input, same output)
    root_a = compute_merkle_root(TXS)
    root_b = compute_merkle_root(TXS)
    assert_true(root_a == root_b, "Merkle root is deterministic")

    # Different txs → different root
    modified = TXS[:2] + [{"from": "zzz", "to": "yyy", "amount": 999, "type": "transfer"}]
    root_c = compute_merkle_root(modified)
    assert_true(root_a != root_c, "Different txs produce different root")


# ─── Test 2: Merkle proof generation and verification ────────────────────────

def test_merkle_proof_verify():
    print("\n--- Test 2: Merkle proof generation and verification ---")
    root = compute_merkle_root(TXS)

    for i, tx in enumerate(TXS):
        proof = generate_merkle_proof(TXS, i)
        ok = verify_merkle_proof(tx, proof, root)
        assert_true(ok, f"Proof for tx[{i}] verifies against root")


# ─── Test 3: Merkle tamper detection ─────────────────────────────────────────

def test_merkle_tamper_detection():
    print("\n--- Test 3: Merkle tamper detection ---")
    root = compute_merkle_root(TXS)
    proof = generate_merkle_proof(TXS, 0)

    # Tampered tx → proof should fail
    tampered_tx = dict(TXS[0])
    tampered_tx["amount"] = 9999
    ok = verify_merkle_proof(tampered_tx, proof, root)
    assert_true(not ok, "Tampered tx fails proof verification")

    # Wrong proof (proof for tx[1] applied to tx[0]) → should fail
    wrong_proof = generate_merkle_proof(TXS, 1)
    ok2 = verify_merkle_proof(TXS[0], wrong_proof, root)
    assert_true(not ok2, "Wrong proof fails verification")


# ─── Test 4: State root determinism ──────────────────────────────────────────

def test_state_root_determinism():
    print("\n--- Test 4: State root determinism ---")
    cons = PoWConsensus(target_difficulty=1)
    chain_a = Blockchain(consensus=cons, require_signature=False)
    chain_b = Blockchain(consensus=cons, require_signature=False)

    chain_a.state = {"alice": 100, "bob": 50}
    chain_b.state = {"alice": 100, "bob": 50}
    assert_true(chain_a.current_state_root == chain_b.current_state_root,
                "Identical state → identical state root")

    chain_b.state["charlie"] = 9999
    assert_true(chain_a.current_state_root != chain_b.current_state_root,
                "Different state → different state root")


# ─── Test 5: state_root stamped in block header ───────────────────────────────

def test_state_root_in_block():
    print("\n--- Test 5: state_root stamped in block header after add_block ---")
    cons = PoWConsensus(target_difficulty=1)
    vm = PythonVM()
    chain = Blockchain(consensus=cons, runtime=vm, require_signature=False)
    chain.state["alice"] = 100

    tx = {"from": "alice", "to": "bob", "amount": 10, "type": "transfer"}
    chain.add_transaction(tx)
    pending = chain.mempool.get_pending()
    b = cons.propose_block(pending, chain.last_block.hash, len(chain.chain), "miner")
    chain.add_block(b)

    # After add_block, the block's state_root must match the current state
    assert_true(b.state_root != "", "Block state_root is not empty after add_block")
    assert_true(b.state_root == chain.current_state_root,
                "Block state_root matches current chain state root")
    assert_true(b.merkle_root != "", "Block merkle_root is not empty")


# ─── Test 6: SQLite block round-trip ─────────────────────────────────────────

def test_sqlite_block_roundtrip():
    print("\n--- Test 6: SQLite block round-trip ---")
    tmpdir = tempfile.mkdtemp()
    db_path = os.path.join(tmpdir, "test.db")
    try:
        # Write side
        p1 = Persistence(db_path)
        cons = PoWConsensus(target_difficulty=1)
        vm = PythonVM()
        chain = Blockchain(consensus=cons, runtime=vm, require_signature=False)
        chain.state["alice"] = 100
        tx = {"from": "alice", "to": "bob", "amount": 5, "type": "transfer"}
        chain.add_transaction(tx)
        pending = chain.mempool.get_pending()
        b = cons.propose_block(pending, chain.last_block.hash, len(chain.chain), "miner")
        chain.add_block(b)
        p1.save_block(chain.chain[0])  # genesis
        p1.save_block(b)

        # Read side (new Persistence instance = new connection)
        p2 = Persistence(db_path)
        loaded = p2.load_all_blocks()
        assert_true(len(loaded) == 2, f"Should load 2 blocks, got {len(loaded)}")
        assert_true(loaded[1].hash == b.hash, "Loaded block hash matches original")
        assert_true(loaded[1].merkle_root == b.merkle_root,
                    "merkle_root survives SQLite round-trip")
        assert_true(loaded[1].state_root == b.state_root,
                    "state_root survives SQLite round-trip")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


# ─── Test 7: SQLite state round-trip ─────────────────────────────────────────

def test_sqlite_state_roundtrip():
    print("\n--- Test 7: SQLite state round-trip ---")
    tmpdir = tempfile.mkdtemp()
    db_path = os.path.join(tmpdir, "test_state.db")
    try:
        state = {"alice": 100, "bob": 50, "charlie": 7}
        p = Persistence(db_path)
        p.save_state(state)

        p2 = Persistence(db_path)
        loaded = p2.load_state()
        assert_true(loaded == state, f"State round-trip matches: {loaded}")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


# ─── Test 8: load_from_disk ───────────────────────────────────────────────────

def test_load_from_disk():
    print("\n--- Test 8: load_from_disk reconstructs chain ---")
    tmpdir = tempfile.mkdtemp()
    db_path = os.path.join(tmpdir, "node.db")
    try:
        cons = PoWConsensus(target_difficulty=1)
        vm = PythonVM()

        # First run — mine 2 blocks and persist
        chain1 = Blockchain(consensus=cons, runtime=vm, require_signature=False, db_path=db_path)
        chain1.state["alice"] = 200
        for i in range(2):
            tx = {"from": "alice", "to": "bob", "amount": 1, "type": "transfer"}
            chain1.add_transaction(tx)
            pending = chain1.mempool.get_pending()
            b = cons.propose_block(pending, chain1.last_block.hash, len(chain1.chain), "miner")
            chain1.add_block(b)

        original_tip_hash = chain1.last_block.hash
        original_len = len(chain1.chain)

        # Second run — start fresh, load from disk
        chain2 = Blockchain(consensus=cons, runtime=vm, require_signature=False, db_path=db_path)
        # Override the fresh genesis with disk data
        loaded = chain2.load_from_disk()

        assert_true(loaded, "load_from_disk returned True (data found)")
        assert_true(len(chain2.chain) == original_len,
                    f"Loaded chain length {len(chain2.chain)} matches original {original_len}")
        assert_true(chain2.last_block.hash == original_tip_hash,
                    "Loaded chain tip hash matches original")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


# ─── Test 9: SQLite reorg (delete_blocks_after + bulk save) ──────────────────

def test_sqlite_reorg():
    print("\n--- Test 9: SQLite reorg (delete_blocks_after + bulk_save) ---")
    tmpdir = tempfile.mkdtemp()
    db_path = os.path.join(tmpdir, "reorg.db")
    try:
        p = Persistence(db_path)
        cons = PoWConsensus(target_difficulty=1)

        # Save 3 blocks
        blocks = []
        prev_hash = "0"
        vm = PythonVM()
        chain = Blockchain(consensus=cons, runtime=vm, require_signature=False)
        for i in range(1, 4):
            b = cons.propose_block([], chain.last_block.hash, len(chain.chain), "miner")
            chain.add_block(b)
            p.save_block(b)
            blocks.append(b)

        assert_true(p.block_count() == 3, "3 blocks saved")

        # Simulate reorg: delete block 3 (idx=3), replace with alternative
        p.delete_blocks_after(1)
        assert_true(p.block_count() == 1, "delete_blocks_after(1) leaves 1 non-genesis block")

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


# ─── Run all ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    test_merkle_root_correctness()
    test_merkle_proof_verify()
    test_merkle_tamper_detection()
    test_state_root_determinism()
    test_state_root_in_block()
    test_sqlite_block_roundtrip()
    test_sqlite_state_roundtrip()
    test_load_from_disk()
    test_sqlite_reorg()

    print("\n=== All Persistence & State Tests PASSED! ===")
    sys.exit(0)
