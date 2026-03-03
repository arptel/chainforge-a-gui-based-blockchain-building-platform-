class ValidatorCouncil:
    def __init__(self):
        self.validators = {} # address -> weight

    def addValidator(self, address, weight=1):
        self.validators[address] = weight
        return True

    def removeValidator(self, address):
        if address in self.validators:
            del self.validators[address]
        return True

    def getValidators(self):
        return self.validators
