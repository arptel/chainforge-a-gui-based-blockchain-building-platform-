class MyStorage:
    def set(self, value):
        self.ctx.state['storage_value'] = value
