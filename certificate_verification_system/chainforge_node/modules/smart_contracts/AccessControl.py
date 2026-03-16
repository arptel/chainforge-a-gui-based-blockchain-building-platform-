class AccessControl:
    def __init__(self):
        self.roles = {} # role -> list of addresses

    def grantRole(self, role, address):
        if role not in self.roles:
            self.roles[role] = []
        if address not in self.roles[role]:
            self.roles[role].append(address)
        return True

    def revokeRole(self, role, address):
        if role in self.roles and address in self.roles[role]:
            self.roles[role].remove(address)
        return True

    def hasRole(self, role, address):
        return role in self.roles and address in self.roles[role]
