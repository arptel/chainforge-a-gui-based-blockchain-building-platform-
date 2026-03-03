class Participation:
    def __init__(self):
        self.nodes = []

    def registerNode(self, address, node_type="full"):
        entry = {"address": address, "type": node_type}
        self.nodes.append(entry)
        return True

    def deregisterNode(self, address):
        self.nodes = [n for n in self.nodes if n["address"] != address]
        return True
