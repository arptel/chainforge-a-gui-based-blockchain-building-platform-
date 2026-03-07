class Whitelist:
    def __init__(self):
        self.whitelist = []

    def addToWhitelist(self, address):
        if address not in self.whitelist:
            self.whitelist.append(address)
        return True

    def removeFromWhitelist(self, address):
        if address in self.whitelist:
            self.whitelist.remove(address)
        return True

    def isWhitelisted(self, address):
        return address in self.whitelist
