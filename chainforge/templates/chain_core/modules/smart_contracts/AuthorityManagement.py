class AuthorityManagement:
    def __init__(self):
        self.authorities = []

    def addAuthority(self, address):
        if address not in self.authorities:
            self.authorities.append(address)
        return True

    def removeAuthority(self, address):
        if address in self.authorities:
            self.authorities.remove(address)
        return True

    def isAuthority(self, address):
        return address in self.authorities
