import requests
from .config import API_BASE_URL

class SmartContract:
    def __init__(self, contract_id, api_key):
        self.contract_id = contract_id
        self.api_key = api_key
        self.base_url = f"{API_BASE_URL}/api/v1/contracts/execute/{contract_id}"

    def _call(self, method, **kwargs):
        headers = {"x-api-key": self.api_key}
        payload = {"args": kwargs}
        response = requests.post(f"{self.base_url}/{method}", json=payload, headers=headers)
        if response.status_code == 200:
            return response.json().get("result")
        else:
            raise Exception(f"Error {response.status_code}: {response.text}")

    def __getattr__(self, name):
        def method(**kwargs):
            return self._call(name, **kwargs)
        return method


class DataStoreWrapper(SmartContract):
    def __init__(self):
        super().__init__("1000", "sys_key_datastore")

    # Note: We can't statically know methods without parsing AST, 
    # so we use __getattr__ for dynamic method calls or generate specific ones if we parsed it.
    # For now, we'll use __getattr__ to catch any method call and forward it.
    
    def __getattr__(self, name):
        def method(**kwargs):
            return self._call(name, **kwargs)
        return method

class ValidationWrapper(SmartContract):
    def __init__(self):
        super().__init__("1001", "sys_key_validation")

    # Note: We can't statically know methods without parsing AST, 
    # so we use __getattr__ for dynamic method calls or generate specific ones if we parsed it.
    # For now, we'll use __getattr__ to catch any method call and forward it.
    
    def __getattr__(self, name):
        def method(**kwargs):
            return self._call(name, **kwargs)
        return method

class AccessControlWrapper(SmartContract):
    def __init__(self):
        super().__init__("1002", "sys_key_accesscontrol")

    # Note: We can't statically know methods without parsing AST, 
    # so we use __getattr__ for dynamic method calls or generate specific ones if we parsed it.
    # For now, we'll use __getattr__ to catch any method call and forward it.
    
    def __getattr__(self, name):
        def method(**kwargs):
            return self._call(name, **kwargs)
        return method

class IdentityRegistryWrapper(SmartContract):
    def __init__(self):
        super().__init__("1003", "sys_key_identityregistry")

    # Note: We can't statically know methods without parsing AST, 
    # so we use __getattr__ for dynamic method calls or generate specific ones if we parsed it.
    # For now, we'll use __getattr__ to catch any method call and forward it.
    
    def __getattr__(self, name):
        def method(**kwargs):
            return self._call(name, **kwargs)
        return method

class AuditLogWrapper(SmartContract):
    def __init__(self):
        super().__init__("1004", "sys_key_auditlog")

    # Note: We can't statically know methods without parsing AST, 
    # so we use __getattr__ for dynamic method calls or generate specific ones if we parsed it.
    # For now, we'll use __getattr__ to catch any method call and forward it.
    
    def __getattr__(self, name):
        def method(**kwargs):
            return self._call(name, **kwargs)
        return method

class ValidatorCouncilWrapper(SmartContract):
    def __init__(self):
        super().__init__("1005", "sys_key_validatorcouncil")

    # Note: We can't statically know methods without parsing AST, 
    # so we use __getattr__ for dynamic method calls or generate specific ones if we parsed it.
    # For now, we'll use __getattr__ to catch any method call and forward it.
    
    def __getattr__(self, name):
        def method(**kwargs):
            return self._call(name, **kwargs)
        return method

class MultiSigWrapper(SmartContract):
    def __init__(self):
        super().__init__("1006", "sys_key_multisig")

    # Note: We can't statically know methods without parsing AST, 
    # so we use __getattr__ for dynamic method calls or generate specific ones if we parsed it.
    # For now, we'll use __getattr__ to catch any method call and forward it.
    
    def __getattr__(self, name):
        def method(**kwargs):
            return self._call(name, **kwargs)
        return method

class CertificateAuthorityWrapper(SmartContract):
    def __init__(self):
        super().__init__("1007", "sys_key_certificateauthority")

    # Note: We can't statically know methods without parsing AST, 
    # so we use __getattr__ for dynamic method calls or generate specific ones if we parsed it.
    # For now, we'll use __getattr__ to catch any method call and forward it.
    
    def __getattr__(self, name):
        def method(**kwargs):
            return self._call(name, **kwargs)
        return method

class AccessControlWrapper(SmartContract):
    def __init__(self):
        super().__init__("h4hscfu", "sk_9he4zo5b82ovje5nlwiui")

    # Note: We can't statically know methods without parsing AST, 
    # so we use __getattr__ for dynamic method calls or generate specific ones if we parsed it.
    # For now, we'll use __getattr__ to catch any method call and forward it.
    
    def __getattr__(self, name):
        def method(**kwargs):
            return self._call(name, **kwargs)
        return method

class CertificateRegistryWrapper(SmartContract):
    def __init__(self):
        super().__init__("7vjd6ku", "sk_9r9suqrmwe4e0ar5gvbe")

    # Note: We can't statically know methods without parsing AST, 
    # so we use __getattr__ for dynamic method calls or generate specific ones if we parsed it.
    # For now, we'll use __getattr__ to catch any method call and forward it.
    
    def __getattr__(self, name):
        def method(**kwargs):
            return self._call(name, **kwargs)
        return method

class Client:
    def __init__(self, base_url=None):
        if base_url:
            global API_BASE_URL
            API_BASE_URL = base_url
        self.DataStore = DataStoreWrapper()
        self.Validation = ValidationWrapper()
        self.AccessControl = AccessControlWrapper()
        self.IdentityRegistry = IdentityRegistryWrapper()
        self.AuditLog = AuditLogWrapper()
        self.ValidatorCouncil = ValidatorCouncilWrapper()
        self.MultiSig = MultiSigWrapper()
        self.CertificateAuthority = CertificateAuthorityWrapper()
        self.AccessControl = AccessControlWrapper()
        self.CertificateRegistry = CertificateRegistryWrapper()
