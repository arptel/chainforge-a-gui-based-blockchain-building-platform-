class ValidatorCouncil:
    def __init__(self):
        pass

    def addValidator(self, caller=None, state=None, address=None, weight=1, **kwargs):
        if state is None: return False
        validators = state.setdefault("system.council.validators", {})
        validators[address] = weight
        return True

    def removeValidator(self, caller=None, state=None, address=None, **kwargs):
        if state is None: return False
        validators = state.setdefault("system.council.validators", {})
        if address in validators:
            del validators[address]
        return True

    def getValidators(self, caller=None, state=None, **kwargs):
        if state is None: return {}
        return state.get("system.council.validators", {})

