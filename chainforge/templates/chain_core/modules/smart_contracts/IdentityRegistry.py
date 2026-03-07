class IdentityRegistry:
    def __init__(self):
        self.identities = {}

    def registerIdentity(self, address, metadata):
        self.identities[address] = metadata
        return True

    def getIdentity(self, address):
        return self.identities.get(address)
