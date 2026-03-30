class DataStore:
    def __init__(self):
        self.store = {}

    def add(self, key, value):
        if key in self.store:
            raise Exception("Key already exists")
        self.store[key] = value
        return True

    def update(self, key, value):
        if key not in self.store:
            raise Exception("Key does not exist")
        self.store[key] = value
        return True

    def get(self, key):
        return self.store.get(key)

    def exists(self, key):
        return key in self.store
