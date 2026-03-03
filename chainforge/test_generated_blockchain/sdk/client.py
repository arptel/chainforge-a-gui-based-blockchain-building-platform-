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


class TokenWrapper(SmartContract):
    def __init__(self):
        super().__init__("c1", "test-key")

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
        self.Token = TokenWrapper()
        self.DataStore = SmartContract('sys_datastore', 'sk_sys_datastore')
        self.Governance = SmartContract('sys_governance', 'sk_sys_governance')
