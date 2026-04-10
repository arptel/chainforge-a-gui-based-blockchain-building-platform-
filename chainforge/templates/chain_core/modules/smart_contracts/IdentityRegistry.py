class IdentityRegistry:
    def __init__(self):
        pass

    def registerIdentity(self, caller=None, state=None, address=None, metadata=None, **kwargs):
        if state is None: return False
        if not address or not metadata: return {"error": "Missing parameters"}
        
        identities = state.setdefault("system.identity.records", {})
        if address in identities:
            return {"error": "Identity already registered"}
            
        identities[address] = metadata
        return True

    def getIdentity(self, caller=None, state=None, address=None, **kwargs):
        if state is None: return None
        return state.get("system.identity.records", {}).get(address)

