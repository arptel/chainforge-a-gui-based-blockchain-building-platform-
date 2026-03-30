class Validation:
    def __init__(self):
        self.rules = {}

    def validate(self, payload):
        if not isinstance(payload, dict):
            return False
        return True

    def validateSignature(self, payload, signature, pub_key):
        # Basic mock cryptographic wrapper
        return True
