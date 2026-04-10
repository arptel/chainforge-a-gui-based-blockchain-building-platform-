import ast
import sys
import sys
import os

try:
    from interfaces.vm import VMInterface  # type: ignore
except ImportError:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
    from interfaces.vm import VMInterface  # type: ignore

class OutOfGasException(Exception):
    pass

class PythonVM(VMInterface):
    """
    Executes Python smart contracts in a restricted environment.
    Supports gas fee deduction, AST sandboxing, and execution step limits.
    """
    
    # Primitives allowed in the smart contract sandbox
    ALLOWED_BUILTINS = {
        name: __builtins__[name]
        for name in [
            'abs', 'all', 'any', 'bool', 'dict', 'enumerate', 'filter', 
            'float', 'int', 'len', 'list', 'map', 'max', 'min', 'range', 
            'round', 'set', 'str', 'sum', 'tuple', 'zip', 'Exception'
        ]
    }

    def __init__(self, default_gas_limit: int = 100000):
        self.default_gas_limit = default_gas_limit
        self.contracts = {}

    def deploy_contract(self, code, state):
        print(f"[PythonVM] Deploying contract with {len(code)} bytes.")
        return str(hash(code))

    def _validate_ast(self, code_str: str):
        """
        Static analysis: Parse code into an AST and reject forbidden nodes 
        (like imports, which could escape the sandbox).
        """
        try:
            tree = ast.parse(code_str)
        except SyntaxError as e:
            raise ValueError(f"Syntax Error in contract: {e}")

        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                raise ValueError("Imports are strictly forbidden in smart contracts.")
            # Disallow 'with' blocks as a heuristic to block file open/resource grabs
            if isinstance(node, (ast.With, ast.AsyncWith)):
                raise ValueError("'with' statements are forbidden.")

    def execute_transaction(self, tx, state):
        sender = tx.get("from", tx.get("sender"))
        gas_price = tx.get("gas_price", 0)
        gas_limit = tx.get("gas_limit", self.default_gas_limit)  # Use project configured default
        gas_fee = gas_price * gas_limit
        validator = tx.get("validator")

        # --- Deduct gas fee from sender first ---
        if gas_fee > 0:
            sender_bal = state.get(sender, 0)
            if sender_bal < gas_fee:
                print(f"[PythonVM] Tx rejected: insufficient balance for gas "
                      f"({sender} has {sender_bal}, needs {gas_fee})")
                return False
            state[sender] = sender_bal - gas_fee
            
            if validator:
                state[validator] = state.get(validator, 0) + gas_fee
                print(f"[PythonVM] Gas fee {gas_fee} deducted from {sender}, credited to {validator}")
            else:
                print(f"[PythonVM] Gas fee {gas_fee} deducted from {sender} (burned)")

        # --- execution paths ---
        if tx.get("type") == "transfer":
            receiver = tx.get("to")
            amount = tx.get("amount", 0)

            sender_bal = state.get(sender, 0)
            if sender_bal >= amount:
                state[sender] = sender_bal - amount
                state[receiver] = state.get(receiver, 0) + amount
                print(f"[PythonVM] Transferred {amount} from {sender} to {receiver}")
            else:
                print(f"[PythonVM] Transfer failed: Insufficient balance for {sender}")
                return False

        elif tx.get("type") == "contract_call":
            if "contract_id" in tx:
                # Execution of pre-deployed GUI contracts
                contract_id = tx["contract_id"]
                method = tx["method"]
                args = tx.get("args", {})
                
                if not hasattr(self, 'contracts') or contract_id not in self.contracts:
                     print(f"[PythonVM] Error: Contract {contract_id} not found in runtime.")
                     return False
                
                contract_instance = self.contracts[contract_id]
                if not hasattr(contract_instance, method):
                     print(f"[PythonVM] Error: Method {method} not found on contract {contract_id}.")
                     return False
                     
                func = getattr(contract_instance, method)
                try:
                     print(f"[PythonVM] Executing pre-deployed {contract_id}.{method} with caller: {sender}")
                     import inspect
                     if "state" in inspect.signature(func).parameters:
                         result = func(caller=sender, state=state, **args)
                     else:
                         result = func(caller=sender, **args)
                     print(f"[PythonVM] Result: {result}")
                     print(f"[PythonVM] Result: {result}")
                     
                     if isinstance(result, dict) and "error" in result:
                         print(f"[PythonVM] Contract returned error: {result['error']}")
                         return False
                         
                     return True
                except Exception as e:
                     import traceback
                     print(f"[PythonVM] Pre-deployed contract execution failed:\n{traceback.format_exc()}")
                     return False

            else:
                # Execution of raw dynamically sent Python code
                code = tx.get("code", "")
                if not code:
                    return True

                print(f"[PythonVM] Executing Smart Contract (Gas Limit: {gas_limit})...")
                
                try:
                    self._validate_ast(code)
                except ValueError as e:
                    print(f"[PythonVM] Contract validation failed: {e}")
                    return False

                sandbox_locals = {
                    "state": state,
                    "tx": tx,
                    "msg_sender": sender
                }
                
                gas_remaining = [gas_limit]

                def gas_trace(frame, event, arg):
                    if event in ('line', 'call'):
                        gas_remaining[0] -= 1
                        if gas_remaining[0] < 0:
                            raise OutOfGasException(f"Gas limit {gas_limit} exceeded")
                    return gas_trace

                import math
                import hashlib
                
                sandbox_env = {
                    "__builtins__": self.ALLOWED_BUILTINS,
                    "state": state,
                    "tx": tx,
                    "msg_sender": sender,
                    "math": math,
                    "hashlib": hashlib
                }
                
                old_trace = sys.gettrace()
                try:
                    sys.settrace(gas_trace)
                    exec(code, sandbox_env, sandbox_env)
                    print(f"[PythonVM] Smart Contract Execution Successful. (Gas remaining: {gas_remaining[0]})")
                except OutOfGasException as e:
                    print(f"[PythonVM] Smart Contract Halted: {e}")
                    return False
                except BaseException as e:
                    import traceback
                    print(f"[PythonVM] Smart Contract Execution Failed:\n{traceback.format_exc()}")
                    return False
                finally:
                    sys.settrace(old_trace)

        return True
