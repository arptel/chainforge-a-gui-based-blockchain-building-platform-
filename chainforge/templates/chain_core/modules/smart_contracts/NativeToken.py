class NativeToken:
    def __init__(self):
        pass

    def _mint(self, caller=None, state=None, address=None, amount=None, **kwargs):
        if state is None: return False
        if not address or amount is None: return {"error": "Invalid parameters"}
        state[address] = state.get(address, 0) + amount
        return True

    def transfer(self, caller=None, state=None, sender=None, receiver=None, amount=None, **kwargs):
        if state is None: return False
        if amount is None or amount <= 0: return {"error": "Invalid amount"}
        
        # Enforce caller authorization
        if sender and sender != caller:
            return {"error": "Unauthorized: caller cannot transfer from another account"}
        sender = caller
        
        if not sender or not receiver: return {"error": "Invalid sender or receiver"}
        
        if state.get(sender, 0) < amount:
            return {"error": "Insufficient balance"}
            
        state[sender] -= amount
        state[receiver] = state.get(receiver, 0) + amount
        return True

    def balanceOf(self, caller=None, state=None, address=None, **kwargs):
        if state is None: return 0
        return state.get(address, 0)

    def approve(self, caller=None, state=None, owner=None, spender=None, amount=None, **kwargs):
        if state is None: return False
        owner = owner or caller
        if not owner or not spender or amount is None: return {"error": "Invalid parameters"}
        
        allowances = state.setdefault("system.token.allowances", {})
        if owner not in allowances:
            allowances[owner] = {}
        allowances[owner][spender] = amount
        return True

