class DataStore:
    def store(self, key: str, value: str):
        _data = self.ctx.state.get('data', {})
        _data[key] = value
        self.ctx.state['data'] = _data
        self.ctx.emit_event('Stored', {'key': key, 'value': value})

    def retrieve(self, key: str) -> str:
        _data = self.ctx.state.get('data', {})
        return _data[key]