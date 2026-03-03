"""
test_vm_security.py

Tests for PythonVM Smart Contract Security:
1. Valid contract executes successfully within gas limit
2. Infinite loop is halted by OutOfGasException (Gas Metering)
3. AST sandboxing blocks 'import os'
4. AST sandboxing blocks 'with open(...)'
5. Restricted builtins prevent '__import__', 'eval', 'exec', etc.
6. Gas fees are correctly deducted based on gas_limit
"""
import sys
import os

sys.path.insert(0, ".")

from modules.vm.python_vm import PythonVM

def assert_true(condition, msg):
    if not condition:
        print(f"  [FAIL] {msg}")
        sys.exit(1)
    print(f"  [PASS] {msg}")


def assert_false(condition, msg):
    assert_true(not condition, msg)


# ─── Test 1: Valid Execution ─────────────────────────────────────────────────

def test_valid_execution():
    print("\n--- Test 1: Valid Execution within Gas Limit ---")
    vm = PythonVM()
    state = {"alice": 2000, "bob": 0}
    
    code = """
def calculate():
    sum = 0
    for i in range(5):
        sum += i
    state['bob'] += sum
calculate()
"""
    tx = {
        "from": "alice",
        "to": "contract",
        "type": "contract_call",
        "code": code,
        "gas_price": 1,
        "gas_limit": 1000 # Plentiful gas
    }
    
    import io
    from contextlib import redirect_stdout
    f = io.StringIO()
    with redirect_stdout(f):
        ok = vm.execute_transaction(tx, state)
    
    if not ok:
        print(f"DEBUG OUT: {f.getvalue()}")
        
    assert_true(ok, "Valid contract executes successfully")
    assert_true(state["bob"] == 10, f"State updated correctly (bob={state['bob']})")
    assert_true(state["alice"] == 2000 - (1 * 1000), "Gas fee deducted correctly")


# ─── Test 2: Infinite Loop / Out of Gas ──────────────────────────────────────

def test_infinite_loop():
    print("\n--- Test 2: Infinite Loop halted by OutOfGasException ---")
    vm = PythonVM()
    state = {"alice": 100}
    
    # This loop would freeze the node if not for gas metering
    code = """
while True:
    pass
"""
    tx = {
        "from": "alice",
        "to": "contract",
        "type": "contract_call",
        "code": code,
        "gas_price": 0,
        "gas_limit": 50 # Will run out after ~50 instructions
    }
    
    import io
    from contextlib import redirect_stdout
    with redirect_stdout(io.StringIO()):
        ok = vm.execute_transaction(tx, state)
    assert_false(ok, "Infinite loop execution failed and halted as expected")


# ─── Test 3: AST Block Imports ───────────────────────────────────────────────

def test_ast_block_imports():
    print("\n--- Test 3: AST Sandboxing blocks 'import' ---")
    vm = PythonVM()
    state = {"alice": 100}
    
    code1 = "import os\nos.system('echo Hacked')"
    tx1 = {"from": "alice", "type": "contract_call", "code": code1, "gas_limit": 1000}
    ok1 = vm.execute_transaction(tx1, state)
    assert_false(ok1, "Direct 'import os' blocked by AST validation")

    code2 = "from os import system\nsystem('echo Hacked')"
    tx2 = {"from": "alice", "type": "contract_call", "code": code2, "gas_limit": 1000}
    ok2 = vm.execute_transaction(tx2, state)
    assert_false(ok2, "'from os import...' blocked by AST validation")


# ─── Test 4: AST Block 'with' ────────────────────────────────────────────────

def test_ast_block_with():
    print("\n--- Test 4: AST Sandboxing blocks 'with' (file access) ---")
    vm = PythonVM()
    state = {"alice": 100}
    
    code = """
with open('secret.txt', 'w') as f:
    f.write('hacked')
"""
    tx = {"from": "alice", "type": "contract_call", "code": code, "gas_limit": 100000}
    import io
    from contextlib import redirect_stdout
    with redirect_stdout(io.StringIO()):
        ok = vm.execute_transaction(tx, state)
    assert_false(ok, "'with open(...)' blocked by AST validation")


# ─── Test 5: Restricted Builtins ─────────────────────────────────────────────

def test_restricted_builtins():
    print("\n--- Test 5: Restricted Builtins prevent __import__ / eval ---")
    vm = PythonVM()
    state = {"alice": 100}
    
    # Try to bypass import restriction using __import__
    code1 = """
os = __import__('os')
os.system('echo Hacked')
"""
    tx1 = {"from": "alice", "type": "contract_call", "code": code1, "gas_limit": 100000}
    import io
    from contextlib import redirect_stdout
    with redirect_stdout(io.StringIO()):
        ok1 = vm.execute_transaction(tx1, state)
    assert_false(ok1, "__import__ is completely removed from sandbox builtins")

    # Try to use eval
    code2 = """
eval("print('hacked')")
"""
    tx2 = {"from": "alice", "type": "contract_call", "code": code2, "gas_limit": 100000}
    with redirect_stdout(io.StringIO()):
        ok2 = vm.execute_transaction(tx2, state)
    assert_false(ok2, "eval() is completely removed from sandbox builtins")

    # Try access globals/locals
    code3 = """
g = globals()
"""
    tx3 = {"from": "alice", "type": "contract_call", "code": code3, "gas_limit": 100000}
    with redirect_stdout(io.StringIO()):
        ok3 = vm.execute_transaction(tx3, state)
    assert_false(ok3, "globals() is completely removed from sandbox builtins")


# ─── Run All ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    test_valid_execution()
    test_infinite_loop()
    test_ast_block_imports()
    test_ast_block_with()
    test_restricted_builtins()

    print("\n=== All VM Security Tests PASSED! ===")
    sys.exit(0)
