class DataStore:
    def __init__(self):
        pass

    def add(self, caller=None, state=None, key=None, value=None, **kwargs):
        if state is None: return False
        store = state.setdefault("system.datastore", {})
        if key in store:
            return {"error": "Key already exists"}
        store[key] = value
        return True

    def update(self, caller=None, state=None, key=None, value=None, **kwargs):
        if state is None: return False
        store = state.setdefault("system.datastore", {})
        if key not in store:
            return {"error": "Key does not exist"}
        store[key] = value
        return True

    def get(self, caller=None, state=None, key=None, **kwargs):
        if state is None: return None
        return state.get("system.datastore", {}).get(key)

    def exists(self, caller=None, state=None, key=None, **kwargs):
        if state is None: return False
        return key in state.get("system.datastore", {})
