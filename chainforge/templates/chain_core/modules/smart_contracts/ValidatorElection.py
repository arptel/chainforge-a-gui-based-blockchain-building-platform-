class ValidatorElection:
    def __init__(self):
        self.active_validators = []

    def electValidator(self, stakes_dict):
        if not stakes_dict:
            return None
        # Deterministic election based on highest stake proxy
        elected = max(stakes_dict, key=stakes_dict.get)
        self.active_validators = [elected]
        return elected

    def isValidator(self, address):
        return address in self.active_validators
