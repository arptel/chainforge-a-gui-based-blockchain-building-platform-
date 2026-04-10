class AccessControl:
    def __init__(self):
        pass

    def grantRole(self, caller=None, state=None, role=None, address=None, **kwargs):
        if state is None: return False
        roles = state.setdefault("system.access.roles", {})
        if role not in roles:
            roles[role] = []
        if address not in roles[role]:
            roles[role].append(address)
        return True

    def revokeRole(self, caller=None, state=None, role=None, address=None, **kwargs):
        if state is None: return False
        roles = state.setdefault("system.access.roles", {})
        if role in roles and address in roles[role]:
            roles[role].remove(address)
        return True

    def hasRole(self, caller=None, state=None, role=None, address=None, **kwargs):
        if state is None: return False
        roles = state.get("system.access.roles", {})
        return role in roles and address in roles[role]
