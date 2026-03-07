class MiningReward:
    def __init__(self):
        self.balances = {}
        self.reward_amount = 50

    def claimReward(self, miner_address):
        if miner_address not in self.balances:
            self.balances[miner_address] = 0
        self.balances[miner_address] += self.reward_amount
        return True

    def getReward(self, miner_address):
        return self.balances.get(miner_address, 0)
