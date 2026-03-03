"""
test_mempool.py

Tests for Mempool & Transaction Integrity:
1. Replay attack prevention (duplicate nonce)
2. Stale nonce rejection
3. Future nonce rejection
4. Gas fee enforcement (min_gas_price)
5. Priority ordering (higher gas_price first)
6. Gas fee deduction from sender balance
7. Nonce auto-advance after block confirmation
8. Existing tests still pass (backward compat via pending_transactions shim)
"""
import sys
sys.path.insert(0, ".")

from core.chain import Blockchain
from core.mempool import Mempool
from modules.consensus.pow import PoWConsensus
from modules.vm.python_vm import PythonVM


# ─── Helpers ────────────────────────────────────────────────────────────────

def make_tx(sender, receiver, amount, nonce, gas_price=1, gas_limit=1):
    return {
        "from": sender,
        "to": receiver,
        "amount": amount,
        "nonce": nonce,
        "gas_price": gas_price,
        "gas_limit": gas_limit,
        "type": "transfer",
    }

def assert_true(condition, msg):
    if not condition:
        print(f"  [FAIL] {msg}")
        sys.exit(1)
    print(f"  [PASS] {msg}")

# ─── Test 1: Basic add ───────────────────────────────────────────────────────

def test_basic_add():
    print("\n--- Test 1: Basic add ---")
    m = Mempool(min_gas_price=0)
    tx = make_tx("alice", "bob", 10, nonce=1, gas_price=5)
    ok, reason = m.add(tx)
    assert_true(ok, f"First tx should be accepted (reason: {reason})")
    assert_true(m.size() == 1, "Pool should have 1 tx")

# ─── Test 2: Replay attack prevention ─────────────────────────────────────

def test_replay_prevention():
    print("\n--- Test 2: Replay attack prevention ---")
    m = Mempool(min_gas_price=0)
    tx1 = make_tx("alice", "bob", 10, nonce=1)
    m.add(tx1)

    # Same nonce — replay attack
    tx_replay = make_tx("alice", "charlie", 5, nonce=1)
    ok, reason = m.add(tx_replay)
    assert_true(not ok, "Replay tx with same nonce should be rejected")
    print(f"  (reason: {reason})")

    # Put tx in confirmed block
    m.remove([tx1])
    tx_stale = make_tx("alice", "dave", 1, nonce=1)
    ok2, reason2 = m.add(tx_stale)
    assert_true(not ok2, "Stale nonce (below confirmed) should be rejected")
    print(f"  (reason: {reason2})")

# ─── Test 3: Future nonce too far ahead ─────────────────────────────────

def test_future_nonce():
    print("\n--- Test 3: Future nonce too far ahead ---")
    m = Mempool(min_gas_price=0)
    # Nonce 100 when nothing confirmed — beyond the 10 lookahead
    tx = make_tx("alice", "bob", 1, nonce=100)
    ok, reason = m.add(tx)
    assert_true(not ok, "Far-future nonce should be rejected")
    print(f"  (reason: {reason})")

    # Nonce 5 should be fine (within 10 lookahead from pending=0)
    tx_ok = make_tx("alice", "bob", 1, nonce=5)
    ok2, reason2 = m.add(tx_ok)
    assert_true(ok2, f"Near-future nonce 5 should be accepted (reason: {reason2})")

# ─── Test 4: Gas fee enforcement ────────────────────────────────────────

def test_gas_enforcement():
    print("\n--- Test 4: Gas fee enforcement ---")
    m = Mempool(min_gas_price=10)

    tx_cheap = make_tx("alice", "bob", 1, nonce=1, gas_price=5)
    ok, reason = m.add(tx_cheap)
    assert_true(not ok, "Gas price 5 below min 10 should be rejected")
    print(f"  (reason: {reason})")

    tx_ok = make_tx("alice", "bob", 1, nonce=1, gas_price=10)
    ok2, reason2 = m.add(tx_ok)
    assert_true(ok2, f"Gas price 10 = min 10 should be accepted (reason: {reason2})")

# ─── Test 5: Priority ordering ───────────────────────────────────────────

def test_priority_ordering():
    print("\n--- Test 5: Priority ordering (higher gas_price first) ---")
    m = Mempool(min_gas_price=0)
    m.add(make_tx("alice", "bob", 1, nonce=1, gas_price=3))   # low
    m.add(make_tx("alice", "bob", 1, nonce=2, gas_price=10))  # high
    m.add(make_tx("alice", "bob", 1, nonce=3, gas_price=7))   # mid

    pending = m.get_pending()
    prices = [t["gas_price"] for t in pending]
    assert_true(prices == sorted(prices, reverse=True),
                f"Txs should be ordered by gas_price desc, got: {prices}")

# ─── Test 6: Gas deduction in VM ─────────────────────────────────────────

def test_gas_deduction_vm():
    print("\n--- Test 6: Gas deduction in VM ---")
    vm = PythonVM()
    state = {"alice": 100, "miner": 0}

    tx = {
        "from": "alice",
        "to": "bob",
        "amount": 50,
        "nonce": 1,
        "gas_price": 2,
        "gas_limit": 3,   # gas_fee = 2 * 3 = 6
        "type": "transfer",
        "validator": "miner",
    }
    vm.execute_transaction(tx, state)
    # alice should have: 100 - 6 (gas) - 50 (transfer) = 44
    # miner should have: 0 + 6 = 6
    # bob should have: 50
    assert_true(state.get("alice") == 44, f"Alice should have 44 after gas+transfer, has {state.get('alice')}")
    assert_true(state.get("miner") == 6, f"Miner should have 6 gas fee, has {state.get('miner')}")
    assert_true(state.get("bob") == 50, f"Bob should have 50, has {state.get('bob')}")

# ─── Test 7: Nonce advance after block confirmation ─────────────────────

def test_nonce_advance_after_block():
    print("\n--- Test 7: Nonce advances after block confirmation ---")
    cons = PoWConsensus(target_difficulty=2)
    vm = PythonVM()
    chain = Blockchain(consensus=cons, runtime=vm, require_signature=False, min_gas_price=0)

    # Give alice some balance
    chain.state["alice"] = 1000

    tx1 = make_tx("alice", "bob", 10, nonce=1, gas_price=1)
    assert_true(chain.add_transaction(tx1), "Tx nonce=1 should be accepted")

    # Mine the block
    pending = chain.mempool.get_pending()
    b = cons.propose_block(pending, chain.last_block.hash, len(chain.chain), "miner")
    chain.add_block(b)

    # After confirmation, nonce=1 is now confirmed — next should be 2
    next_nonce = chain.get_nonce("alice")
    assert_true(next_nonce == 2, f"Next nonce for alice after 1 confirmation should be 2, got {next_nonce}")

    # Re-submitting nonce=1 should be rejected
    tx_replay = make_tx("alice", "charlie", 5, nonce=1)
    ok = chain.add_transaction(tx_replay)
    assert_true(not ok, "Resubmitting nonce=1 after confirmation should be rejected (replay)")

# ─── Test 8: Backward-compat shim ───────────────────────────────────────

def test_backward_compat_shim():
    print("\n--- Test 8: Backward-compat shim (pending_transactions property) ---")
    cons = PoWConsensus(target_difficulty=2)
    chain = Blockchain(consensus=cons, runtime=None, require_signature=False, min_gas_price=0)

    tx = make_tx("alice", "bob", 1, nonce=1)
    chain.add_transaction(tx)
    assert_true(len(chain.pending_transactions) == 1, "pending_transactions shim should return 1 tx")
    chain.pending_transactions = []  # clear via setter
    assert_true(len(chain.pending_transactions) == 0, "Assigning [] should clear the mempool")

# ─── Run all tests ───────────────────────────────────────────────────────

if __name__ == "__main__":
    test_basic_add()
    test_replay_prevention()
    test_future_nonce()
    test_gas_enforcement()
    test_priority_ordering()
    test_gas_deduction_vm()
    test_nonce_advance_after_block()
    test_backward_compat_shim()

    print("\n=== All Mempool & Transaction Integrity Tests PASSED! ===")
    sys.exit(0)
