import hashlib
import sys
import os

try:
    from interfaces.vm import VMInterface  # type: ignore
except ImportError:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
    from interfaces.vm import VMInterface  # type: ignore

try:
    import wasmtime
    WASMTIME_AVAILABLE = True
except ImportError:
    wasmtime, WASMTIME_AVAILABLE = None, False

class WASMRuntime(VMInterface):
    def __init__(self):
        self._contracts = {}
        self.contracts = {}  # System contracts registry
        self._engine = wasmtime.Engine() if WASMTIME_AVAILABLE else None
        self.default_gas_limit = 100000

    def deploy_contract(self, code, sender, state=None):
        code_bytes = code.encode() if isinstance(code, str) else bytes(code or b"")
        contract_address = "0xwasm_" + hashlib.sha256(f"{sender}:{hashlib.sha256(code_bytes).hexdigest()}".encode()).hexdigest()[:34]
        if WASMTIME_AVAILABLE and code_bytes:
            try:
                store = wasmtime.Store(self._engine)
                module = wasmtime.Module(self._engine, code_bytes)
                instance = wasmtime.Instance(store, module, [])
                self._contracts[contract_address] = {"instance": instance, "store": store}
                if state: state[f"wasm_{contract_address}"] = code_bytes
                return contract_address
            except Exception: pass
        self._contracts[contract_address] = {"simulated": True}
        return contract_address

    def execute_transaction(self, tx, state):
        tx_type, sender = tx.get("type", ""), tx.get("from", "")
        if tx_type == "contract_deploy":
            addr = self.deploy_contract(tx.get("code", b""), sender, state)
            tx["contract_address"] = addr
            return True
        elif tx_type == "contract_call":
            if "contract_id" in tx:
                return self._exec_system_contract_call(tx, state)
            contract_addr, func_name = tx.get("to", ""), tx.get("method", "")
            if contract_addr not in self._contracts: return False
            contract = self._contracts[contract_addr]
            if WASMTIME_AVAILABLE and not contract.get("simulated"):
                try:
                    func = contract["instance"].exports(contract["store"]).get(func_name)
                    if func: 
                        func(contract["store"], *[int(a) if isinstance(a, (int, str)) and str(a).isdigit() else 0 for a in tx.get("args", [])])
                        return True
                except Exception: pass
            state[f"{contract_addr}_invocations"] = state.get(f"{contract_addr}_invocations", 0) + 1
            return True
        return False

    def _exec_system_contract_call(self, tx, state) -> bool:
        contract_id = tx.get("contract_id")
        method = tx.get("method")
        args = tx.get("args", {})
        sender = tx.get("from", tx.get("sender"))
        sys_contracts = getattr(self, "contracts", {})
        
        if contract_id not in sys_contracts:
            print(f"[WASM] Error: System contract {contract_id} not found.")
            return False
            
        contract_instance = sys_contracts[contract_id]
        if not hasattr(contract_instance, method):
            print(f"[WASM] Error: Method {method} not found on systemic {contract_id}.")
            return False
            
        try:
            func = getattr(contract_instance, method)
            import inspect
            if "state" in inspect.signature(func).parameters:
                result = func(caller=sender, state=state, **args)
            else:
                result = func(caller=sender, **args)
            
            if isinstance(result, dict) and "error" in result:
                print(f"[WASM] System Contract Error: {result['error']}")
                return False
            return True
        except Exception as e:
            import traceback
            print(f"[WASM] Pre-deployed system contract failed:\n{traceback.format_exc()}")
            return False
