class NativeToken:
    def __init__(self):
        self.balances = {}
        self.allowances = {}

    def _mint(self, address, amount):
        if address not in self.balances:
            self.balances[address] = 0
        self.balances[address] += amount

    def transfer(self, sender, receiver, amount):
        if self.balances.get(sender, 0) < amount:
            raise Exception("Insufficient balance")
        self.balances[sender] -= amount
        if receiver not in self.balances:
            self.balances[receiver] = 0
        self.balances[receiver] += amount
        return True

    def balanceOf(self, address):
        return self.balances.get(address, 0)

    def approve(self, owner, spender, amount):
        if owner not in self.allowances:
            self.allowances[owner] = {}
        self.allowances[owner][spender] = amount
        return True
