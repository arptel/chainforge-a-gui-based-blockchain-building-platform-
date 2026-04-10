class MiningReward:
    def __init__(self):
        self.reward_amount = 50

    def claimReward(self, caller=None, state=None, miner_address=None, **kwargs):
        if state is None: return False
        if not miner_address:
            miner_address = caller
            
        current_balance = state.get(miner_address, 0)
        state[miner_address] = current_balance + self.reward_amount
        return True

    def getReward(self, caller=None, state=None, miner_address=None, **kwargs):
        # A bit of a semantic change: returns current total balance since we use canonical state
        if state is None: return 0
        return state.get(miner_address, 0)

