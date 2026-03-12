from base_client import ChainForgeBaseClient, SmartContract
API_BASE_URL = "http://127.0.0.1:8080"


class DataStoreWrapper(SmartContract):
    def __init__(self, base_client):
        super().__init__("1000", base_client)

    def __getattr__(self, name):
        def method(user_address: str, private_key: str, **kwargs):
            return self.execute(user_address, private_key, name, **kwargs)
        return method

class ValidationWrapper(SmartContract):
    def __init__(self, base_client):
        super().__init__("1001", base_client)

    def __getattr__(self, name):
        def method(user_address: str, private_key: str, **kwargs):
            return self.execute(user_address, private_key, name, **kwargs)
        return method

class AccessControlWrapper(SmartContract):
    def __init__(self, base_client):
        super().__init__("1002", base_client)

    def __getattr__(self, name):
        def method(user_address: str, private_key: str, **kwargs):
            return self.execute(user_address, private_key, name, **kwargs)
        return method

class IdentityRegistryWrapper(SmartContract):
    def __init__(self, base_client):
        super().__init__("1003", base_client)

    def __getattr__(self, name):
        def method(user_address: str, private_key: str, **kwargs):
            return self.execute(user_address, private_key, name, **kwargs)
        return method

class AuditLogWrapper(SmartContract):
    def __init__(self, base_client):
        super().__init__("1004", base_client)

    def __getattr__(self, name):
        def method(user_address: str, private_key: str, **kwargs):
            return self.execute(user_address, private_key, name, **kwargs)
        return method

class ValidatorCouncilWrapper(SmartContract):
    def __init__(self, base_client):
        super().__init__("1005", base_client)

    def __getattr__(self, name):
        def method(user_address: str, private_key: str, **kwargs):
            return self.execute(user_address, private_key, name, **kwargs)
        return method

class MultiSigWrapper(SmartContract):
    def __init__(self, base_client):
        super().__init__("1006", base_client)

    def __getattr__(self, name):
        def method(user_address: str, private_key: str, **kwargs):
            return self.execute(user_address, private_key, name, **kwargs)
        return method

class CertificateAuthorityWrapper(SmartContract):
    def __init__(self, base_client):
        super().__init__("1007", base_client)

    def __getattr__(self, name):
        def method(user_address: str, private_key: str, **kwargs):
            return self.execute(user_address, private_key, name, **kwargs)
        return method

class CertificateRegistryWrapper(SmartContract):
    def __init__(self, base_client):
        super().__init__("7vjd6ku", base_client)

    def __getattr__(self, name):
        def method(user_address: str, private_key: str, **kwargs):
            return self.execute(user_address, private_key, name, **kwargs)
        return method

class Client(ChainForgeBaseClient):
    def __init__(self, base_url=None):
        super().__init__(base_url if base_url else API_BASE_URL)
        self.DataStore = DataStoreWrapper(self)
        self.Validation = ValidationWrapper(self)
        self.AccessControl = AccessControlWrapper(self)
        self.IdentityRegistry = IdentityRegistryWrapper(self)
        self.AuditLog = AuditLogWrapper(self)
        self.ValidatorCouncil = ValidatorCouncilWrapper(self)
        self.MultiSig = MultiSigWrapper(self)
        self.CertificateAuthority = CertificateAuthorityWrapper(self)
        self.CertificateRegistry = CertificateRegistryWrapper(self)
