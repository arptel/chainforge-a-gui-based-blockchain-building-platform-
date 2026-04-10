class Whitelist:
    def __init__(self):
        pass

    def addToWhitelist(self, caller=None, state=None, address=None, **kwargs):
        if state is None: return False
        whitelist = state.setdefault("system.whitelist", [])
        if address not in whitelist:
            whitelist.append(address)
        return True

    def removeFromWhitelist(self, caller=None, state=None, address=None, **kwargs):
        if state is None: return False
        whitelist = state.setdefault("system.whitelist", [])
        if address in whitelist:
            whitelist.remove(address)
        return True

    def isWhitelisted(self, caller=None, state=None, address=None, **kwargs):
        if state is None: return False
        whitelist = state.get("system.whitelist", [])
        return address in whitelist

