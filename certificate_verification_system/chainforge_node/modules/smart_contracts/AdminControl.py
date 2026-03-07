class AdminControl:
    def __init__(self):
        self.admin = None
        self.approved_nodes = []

    def setAdmin(self, address):
        self.admin = address

    def approveNode(self, address):
        if address not in self.approved_nodes:
            self.approved_nodes.append(address)
        return True

    def removeNode(self, address):
        if address in self.approved_nodes:
            self.approved_nodes.remove(address)
        return True

    def rotateLeader(self, new_leader):
        self.admin = new_leader
        return True
