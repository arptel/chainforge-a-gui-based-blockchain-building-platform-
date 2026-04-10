class AuthorityManagement:
    def __init__(self):
        pass

    def addAuthority(self, caller=None, state=None, address=None, **kwargs):
        if state is None: return False
        
        admin = state.get("system.admin")
        if not admin or caller != admin:
            return {"error": "Unauthorized: Only system admin can manage authorities"}
            
        authorities = state.setdefault("system.authorities", [])
        if address not in authorities:
            authorities.append(address)
        return True

    def removeAuthority(self, caller=None, state=None, address=None, **kwargs):
        if state is None: return False
        
        admin = state.get("system.admin")
        if not admin or caller != admin:
            return {"error": "Unauthorized: Only system admin can manage authorities"}
            
        authorities = state.setdefault("system.authorities", [])
        if address in authorities:
            authorities.remove(address)
        return True

    def isAuthority(self, caller=None, state=None, address=None, **kwargs):
        if state is None: return False
        authorities = state.get("system.authorities", [])
        return address in authorities

