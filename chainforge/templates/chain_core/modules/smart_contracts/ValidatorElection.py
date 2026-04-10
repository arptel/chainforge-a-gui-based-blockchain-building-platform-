class ValidatorElection:
    def __init__(self):
        pass

    def electValidator(self, caller=None, state=None, stakes_dict=None, **kwargs):
        if state is None: return None
        # Either use passed stakes or canonical
        stakes = stakes_dict or state.get("system.staking", {})
        if not stakes:
            return None
        # Deterministic election based on highest stake proxy
        elected = max(stakes, key=stakes.get)
        
        validators = state.setdefault("system.validators", [])
        if elected not in validators:
            validators.append(elected)
            
        # Update active leader
        state["system.validators.leader"] = elected
        return elected

    def isValidator(self, caller=None, state=None, address=None, **kwargs):
        if state is None: return False
        validators = state.get("system.validators", [])
        return address in validators

