import sys
import os

try:
    from interfaces.vm import VMInterface  # type: ignore
except ImportError:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
    from interfaces.vm import VMInterface  # type: ignore

from eth.chains.mainnet import MainnetChain, MAINNET_GENESIS_HEADER
from eth.db.atomic import AtomicDB
from eth_keys import keys
from eth_utils import keccak


class EVMRuntime(VMInterface):
    """EVM runtime backed by py-evm.

    This implementation maintains an in-memory py-evm chain and uses it to execute
    transfer, contract deployment (CREATE), and contract call (CALL) transactions.
    """

    def __init__(self):
        self._db = AtomicDB()
        self._chain = None
        self._chain_id = None
        self._name_to_address = {}
        self._contracts = {}
        self.contracts = {}  # System contracts registry
        self.default_gas_limit = 100000

    def _init_chain(self, state: dict):
        if self._chain is not None:
            return

        genesis_params = {
            "coinbase": MAINNET_GENESIS_HEADER.coinbase,
            "difficulty": MAINNET_GENESIS_HEADER.difficulty,
            "gas_limit": max(MAINNET_GENESIS_HEADER.gas_limit, 10_000_000),
            "timestamp": MAINNET_GENESIS_HEADER.timestamp,
            "nonce": MAINNET_GENESIS_HEADER.nonce,
            "extra_data": MAINNET_GENESIS_HEADER.extra_data,
            "transaction_root": MAINNET_GENESIS_HEADER.transaction_root,
            "receipt_root": MAINNET_GENESIS_HEADER.receipt_root,
            "mix_hash": MAINNET_GENESIS_HEADER.mix_hash,
        }

        self._chain = MainnetChain.from_genesis(
            self._db,
            genesis_params=genesis_params,
            genesis_state=self._build_genesis_state(state),
        )
        self._chain_id = self._chain.chain_id

    def _build_genesis_state(self, state: dict) -> dict:
        genesis_state = {}
        for k, v in state.items():
            if not isinstance(v, int):
                continue
            address = self._normalize_address(k)
            genesis_state[address] = {
                "balance": v,
                "nonce": 0,
                "code": b"",
                "storage": {},
            }
        return genesis_state

    def _normalize_address(self, identifier):
        if isinstance(identifier, bytes) and len(identifier) == 20:
            return identifier
        if isinstance(identifier, str):
            if identifier.startswith("0x") and len(identifier) == 42:
                return bytes.fromhex(identifier[2:])
            if identifier in self._name_to_address:
                return self._name_to_address[identifier]
            priv = keys.PrivateKey(keccak(text=identifier))
            addr = priv.public_key.to_canonical_address()
            self._name_to_address[identifier] = addr
            return addr
        raise ValueError(f"Unsupported address type: {type(identifier)}")

    def _ensure_state_synced(self, state: dict):
        vm = self._chain.get_vm()
        for k, v in state.items():
            if not isinstance(v, int):
                continue
            addr = self._normalize_address(k)
            vm.state.set_balance(addr, v)

    def _get_private_key(self, identifier):
        raw = keccak(text=str(identifier))
        return keys.PrivateKey(raw)

    def _addr_hex(self, addr_bytes: bytes) -> str:
        return "0x" + addr_bytes.hex()

    def get_state_root(self) -> str:
        if self._chain is None:
            return ""
        try:
            vm = self._chain.get_vm()
            root = vm.state.state_root
            return root.hex() if isinstance(root, bytes) else str(root)
        except Exception:
            return ""

    def deploy_contract(self, code, sender_key, state=None):
        if state is not None:
            self._init_chain(state)
            self._ensure_state_synced(state)

        if self._chain is None:
            return None

        sender_addr = self._normalize_address(sender_key)
        header = self._chain.get_canonical_head()
        vm = self._chain.get_vm(header)

        if isinstance(code, str):
            code_bytes = bytes.fromhex(code.replace("0x", ""))
        else:
            code_bytes = bytes(code)

        nonce = vm.state.get_nonce(sender_addr)
        unsigned_tx = vm.get_transaction_builder().create_unsigned_transaction(
            nonce=nonce, gas_price=1, gas=3_000_000, to=b"", value=0, data=code_bytes,
        )

        signer = self._get_private_key(sender_key)
        signed_tx = unsigned_tx.as_signed_transaction(signer, chain_id=self._chain_id)

        try:
            receipt, computation = vm.apply_transaction(header, signed_tx)
            vm.state.persist()
            contract_addr = computation.msg.storage_address
            addr_hex = self._addr_hex(contract_addr)
            if state is not None:
                state[sender_key] = vm.state.get_balance(sender_addr)
            self._contracts[addr_hex] = {"bytecode": vm.state.get_code(contract_addr), "address": contract_addr}
            return addr_hex
        except Exception:
            return None

    def execute_transaction(self, tx, state):
        self._init_chain(state)
        self._ensure_state_synced(state)
        tx_type = tx.get("type")
        if tx_type == "transfer":
            return self._exec_transfer(tx, state)
        elif tx_type == "contract_deploy":
            code = tx.get("code", tx.get("bytecode", b""))
            sender_key = tx.get("from", "")
            addr = self.deploy_contract(code, sender_key, state)
            if addr:
                tx["contract_address"] = addr
                return True
            return False
        elif tx_type == "contract_call":
            if "contract_id" in tx:
                return self._exec_system_contract_call(tx, state)
            return self._exec_contract_call(tx, state)
        return False

    def _exec_transfer(self, tx, state) -> bool:
        sender_key, receiver_key = tx.get("from"), tx.get("to")
        amount = int(tx.get("amount", 0))
        sender_addr, receiver_addr = self._normalize_address(sender_key), self._normalize_address(receiver_key)
        header, vm = self._chain.get_canonical_head(), self._chain.get_vm()
        signed_tx = vm.get_transaction_builder().create_unsigned_transaction(
            nonce=vm.state.get_nonce(sender_addr), gas_price=1, gas=21000, to=receiver_addr, value=amount, data=b"",
        ).as_signed_transaction(self._get_private_key(sender_key), chain_id=self._chain_id)
        try:
            vm.apply_transaction(header, signed_tx)
            vm.state.persist()
            state[sender_key], state[receiver_key] = vm.state.get_balance(sender_addr), vm.state.get_balance(receiver_addr)
            return True
        except Exception:
            return False

    def _exec_contract_call(self, tx, state) -> bool:
        sender_key, contract_key = tx.get("from", ""), tx.get("to", "")
        calldata, value = tx.get("data", b""), int(tx.get("value", 0))
        sender_addr = self._normalize_address(sender_key)
        contract_addr = self._contracts[contract_key]["address"] if contract_key in self._contracts else self._normalize_address(contract_key)
        header, vm = self._chain.get_canonical_head(), self._chain.get_vm()
        signed_tx = vm.get_transaction_builder().create_unsigned_transaction(
            nonce=vm.state.get_nonce(sender_addr), gas_price=1, gas=1_000_000, to=contract_addr, value=value, data=bytes.fromhex(calldata.replace("0x","")) if isinstance(calldata, str) else bytes(calldata or b""),
        ).as_signed_transaction(self._get_private_key(sender_key), chain_id=self._chain_id)
        try:
            computation = vm.apply_transaction(header, signed_tx)[1]
            vm.state.persist()
            state[sender_key] = vm.state.get_balance(sender_addr)
            return not (hasattr(computation, 'is_error') and computation.is_error)
        except Exception:
            return False

    def _exec_system_contract_call(self, tx, state) -> bool:
        contract_id = tx.get("contract_id")
        method = tx.get("method")
        args = tx.get("args", {})
        sender = tx.get("from", tx.get("sender"))
        sys_contracts = getattr(self, "contracts", {})
        
        if contract_id not in sys_contracts:
            print(f"[EVM] Error: System contract {contract_id} not found.")
            return False
            
        contract_instance = sys_contracts[contract_id]
        if not hasattr(contract_instance, method):
            print(f"[EVM] Error: Method {method} not found on systemic {contract_id}.")
            return False
            
        try:
            func = getattr(contract_instance, method)
            import inspect
            if "state" in inspect.signature(func).parameters:
                result = func(caller=sender, state=state, **args)
            else:
                result = func(caller=sender, **args)
            
            if isinstance(result, dict) and "error" in result:
                print(f"[EVM] System Contract Error: {result['error']}")
                return False
            return True
        except Exception as e:
            import traceback
            print(f"[EVM] Pre-deployed system contract failed:\n{traceback.format_exc()}")
            return False
