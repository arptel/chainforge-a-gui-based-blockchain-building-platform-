import time

class AuditLog:
    def __init__(self):
        self.logs = []

    def logAction(self, actor, action):
        entry = {"timestamp": time.time(), "actor": actor, "action": action}
        self.logs.append(entry)
        return True

    def getLogs(self, limit=10, offset=0):
        return self.logs[offset:offset+limit]
