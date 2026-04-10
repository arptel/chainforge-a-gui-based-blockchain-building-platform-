class Staking:
    def __init__(self):
        pass

    def stake(self, caller=None, state=None, address=None, amount=None, **kwargs):
        if state is None: return False
        
        # Address validation
        if address and address != caller:
            return {"error": "Unauthorized: Can only stake own funds"}
        address = caller
        
        if amount is None or amount <= 0: return {"error": "Invalid amount"}
        
        # Check canonical balance
        if state.get(address, 0) < amount:
            return {"error": "Insufficient canonical balance to stake"}
            
        # Deduct from canonical balance
        state[address] -= amount
        
        # Add to locked stakes
        stakes = state.setdefault("system.staking", {})
        stakes[address] = stakes.get(address, 0) + amount
        return True

    def unstake(self, caller=None, state=None, address=None, amount=None, **kwargs):
        if state is None: return False
        
        if address and address != caller:
            return {"error": "Unauthorized: Can only unstake own funds"}
        address = caller
        
        if amount is None or amount <= 0: return {"error": "Invalid amount"}
        
        stakes = state.setdefault("system.staking", {})
        if address in stakes and stakes[address] >= amount:
            # Remove from stakes
            stakes[address] -= amount
            # Return to canonical balance
            state[address] = state.get(address, 0) + amount
            return True
            
        return {"error": "Insufficient staked balance"}

    def getStake(self, caller=None, state=None, address=None, **kwargs):
        if state is None: return 0
        return state.get("system.staking", {}).get(address, 0)

