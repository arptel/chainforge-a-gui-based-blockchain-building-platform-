from interfaces.vm import VMInterface

class PythonVM(VMInterface):
    """
    Executes Python smart contracts in a restricted environment.
    """
    def deploy_contract(self, code, state):
        print(f"[PythonVM] Deploying contract with {len(code)} bytes.")
        # Just return the code as the contract address for this prototype
        return str(hash(code))

    def execute_transaction(self, tx, state):
        if tx.get("type") == "transfer":
            # Native token transfer
            sender = tx.get("from")
            receiver = tx.get("to")
            amount = tx.get("amount", 0)
            
            sender_bal = state.get(sender, 0)
            if sender_bal >= amount:
                state[sender] = sender_bal - amount
                state[receiver] = state.get(receiver, 0) + amount
                print(f"[PythonVM] Transferred {amount} from {sender} to {receiver}")
            else:
                print(f"[PythonVM] Transfer failed: Insufficient balance for {sender}")
                
        elif tx.get("type") == "contract_call":
            if "contract_id" in tx:
                # Execution of pre-deployed GUI contracts
                contract_id = tx["contract_id"]
                method = tx["method"]
                args = tx.get("args", {})
                
                if not hasattr(self, 'contracts') or contract_id not in self.contracts:
                     print(f"[PythonVM] Error: Contract {contract_id} not found.")
                     return
                
                contract_instance = self.contracts[contract_id]
                if not hasattr(contract_instance, method):
                     print(f"[PythonVM] Error: Method {method} not found.")
                     return
                     
                func = getattr(contract_instance, method)
                try:
                     print(f"[PythonVM] Executing pre-deployed {contract_id}.{method}")
                     result = func(caller=tx.get("from"), **args)
                     print(f"[PythonVM] Result: {result}")
                except Exception as e:
                     print(f"[PythonVM] Pre-deployed contract execution failed: {e}")

            else:
                # Smart contract execution
                code = tx.get("code", "")
                if not code:
                    return
                    
                print(f"[PythonVM] Executing Smart Contract...")
                # Create a sandboxed local environment that exposes the state dictionary
                sandbox_locals = {
                    "state": state,
                    "tx": tx,
                    "msg_sender": tx.get("from")
                }
                
                try:
                    # Execute the python code inside the sandbox
                    exec(code, {"__builtins__": {}}, sandbox_locals)
                    print(f"[PythonVM] Smart Contract Execution Successful.")
                except Exception as e:
                    print(f"[PythonVM] Smart Contract Execution Failed: {e}")
