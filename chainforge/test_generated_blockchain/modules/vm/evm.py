from interfaces.vm import VMInterface

class EVMRuntime(VMInterface):
    """
    Simulates the Ethereum Virtual Machine (EVM).
    """
    def deploy_contract(self, code, state):
        print(f"[EVM] Deploying generic solidity verified bytecode...")
        # Placeholder for py-evm or actual runtime bytecode storage
        contract_addr = str(hash(code))
        state[contract_addr] = code
        return contract_addr

    def execute_transaction(self, tx, state):
        if tx.get("type") == "transfer":
            sender = tx.get("from")
            receiver = tx.get("to")
            amount = tx.get("amount", 0)
            gas_fee = 21000 # Typical EVM transfer fee offset 
            
            sender_bal = state.get(sender, 0)
            if sender_bal >= (amount + gas_fee):
                state[sender] = sender_bal - amount - gas_fee
                state[receiver] = state.get(receiver, 0) + amount
                print(f"[EVM] Transferred {amount} to {receiver} (Paid {gas_fee} Gas)")
            else:
                print(f"[EVM] Execution Reverted: Insufficient funds for {sender}")
                
        elif tx.get("type") == "contract_call":
            contract = tx.get("to")
            print(f"[EVM] Calling opcode function on smart contract 0x{contract}...")
            # Here we would map OpCodes (e.g. SLOAD, SSTORE) functionally 
            # In a lightweight stub, we simply update state to show successful execution
            state[f"evm_{contract}_latest_caller"] = tx.get("from") 
            print(f"[EVM] Execution completed. Consumed generic gas.")
