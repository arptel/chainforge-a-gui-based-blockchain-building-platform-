class Participation:
    def __init__(self):
        pass

    def registerNode(self, caller=None, state=None, address=None, node_type="full", **kwargs):
        if state is None: return False
        nodes = state.setdefault("system.participation.nodes", [])
        # Check if already registered
        if any(n.get("address") == address for n in nodes):
            return {"error": "Node already registered"}
            
        entry = {"address": address, "type": node_type}
        nodes.append(entry)
        return True

    def deregisterNode(self, caller=None, state=None, address=None, **kwargs):
        if state is None: return False
        nodes = state.get("system.participation.nodes", [])
        state["system.participation.nodes"] = [n for n in nodes if n.get("address") != address]
        return True

