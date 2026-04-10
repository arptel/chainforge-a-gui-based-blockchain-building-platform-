class AdminControl:
    def __init__(self):
        pass

    def setAdmin(self, caller=None, state=None, address=None, **kwargs):
        if state is None: return False
        admin = state.get("system.admin", None)
        # First caller sets it, or existing admin transfers it
        if admin is None or admin == caller:
            state["system.admin"] = address
            return True
        return {"error": "Unauthorized"}

    def approveNode(self, caller=None, state=None, address=None, **kwargs):
        if state is None: return False
        admin = state.get("system.admin", None)
        if caller != admin: return {"error": "Unauthorized"}
        
        nodes = state.setdefault("system.admin.approved_nodes", [])
        if address not in nodes:
            nodes.append(address)
        return True

    def removeNode(self, caller=None, state=None, address=None, **kwargs):
        if state is None: return False
        admin = state.get("system.admin", None)
        if caller != admin: return {"error": "Unauthorized"}
        
        nodes = state.setdefault("system.admin.approved_nodes", [])
        if address in nodes:
            nodes.remove(address)
        return True

    def rotateLeader(self, caller=None, state=None, new_leader=None, **kwargs):
        return self.setAdmin(caller=caller, state=state, address=new_leader)

