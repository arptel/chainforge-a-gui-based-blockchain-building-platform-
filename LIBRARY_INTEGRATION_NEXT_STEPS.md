# Library Integration Next Steps (Agent Instructions)

This document tracks remaining work on integrating real libraries in the ChainForge project.

---

## 1) EVM / `py-evm` — ✅ COMPLETED

### What was done
- **File:** `chainforge/templates/chain_core/modules/vm/evm.py`
- **Contract deployment (CREATE):** Real py-evm CREATE transactions using empty `to` address. Contract address generated from sender + nonce. Bytecode stored in py-evm state.
- **Contract calls (CALL):** Real py-evm CALL transactions with calldata support. Handles revert detection, output extraction, and balance updates.
- **State root alignment:** `chain.py → _compute_state_root()` now uses the py-evm Patricia-Merkle-Trie `state_root` when the EVM runtime is active, falling back to SHA-256 JSON snapshot for other runtimes.
- **Gas handling:** CREATE uses 3M gas, CALL uses configurable gas limit, transfers use 21K gas.

---

## 2) Merkle Tree — ✅ COMPLETED (Custom retained)

### What was done
- **File:** `chainforge/templates/chain_core/core/merkle.py`
- Custom implementation retained (correct and stable).
- 20 comprehensive unit tests added in `tests/test_merkle.py` covering root computation, proof generation, verification, and edge cases. All passing.
- `pymerkle` was evaluated but its API is incompatible with ChainForge's block format. Decision documented.

---

## 3) WASM Runtime — ✅ COMPLETED

### What was done
- **File:** `chainforge/templates/chain_core/modules/vm/wasm.py`
- Replaced stubs with real `wasmtime` execution engine.
- Supports both binary WASM (`.wasm`) and WAT text format.
- Module compilation, instantiation, and exported function invocation.
- Graceful simulation fallback when `wasmtime` is not installed.
- Added `wasmtime` to `requirements.txt`.

---

## All Integration Tasks Complete

All items from this document have been implemented. The remaining library work is:
- **py-evm EVM tests**: Unit tests specific to the EVM CREATE/CALL flow should be added when py-evm is installed in the environment.
- **Vyper full execution**: The Vyper VM currently operates in simulation mode for method calls. Full bytecode execution would require integration with py-evm.
