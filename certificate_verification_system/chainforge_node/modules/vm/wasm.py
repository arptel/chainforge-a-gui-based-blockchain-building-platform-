import hashlib
try:
    from interfaces.vm import VMInterface
except ImportError:
    from chainforge.templates.chain_core.interfaces.vm import VMInterface

try:
    import wasmtime
    WASMTIME_AVAILABLE = True
except ImportError:
    wasmtime, WASMTIME_AVAILABLE = None, False

class WASMRuntime(VMInterface):
    def __init__(self):
        self._contracts = {}
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
