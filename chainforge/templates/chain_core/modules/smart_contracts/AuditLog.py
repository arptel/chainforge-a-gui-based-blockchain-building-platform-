import time

class AuditLog:
    def __init__(self):
        pass

    def logAction(self, caller=None, state=None, actor=None, action=None, **kwargs):
        if state is None: return False
        actor = actor or caller
        
        logs = state.setdefault("system.audit.entries", [])
        entry = {"timestamp": time.time(), "actor": actor, "action": action}
        logs.append(entry)
        return True

    def getLogs(self, caller=None, state=None, limit=10, offset=0, **kwargs):
        if state is None: return []
        logs = state.get("system.audit.entries", [])
        return logs[offset:offset+limit]

