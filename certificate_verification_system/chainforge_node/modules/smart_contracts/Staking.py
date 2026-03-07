class Staking:
    def __init__(self):
        self.stakes = {}

    def stake(self, address, amount):
        if address not in self.stakes:
            self.stakes[address] = 0
        self.stakes[address] += amount
        return True

    def unstake(self, address, amount):
        if address in self.stakes and self.stakes[address] >= amount:
            self.stakes[address] -= amount
            return True
        raise Exception("Insufficient stake")

    def getStake(self, address):
        return self.stakes.get(address, 0)
