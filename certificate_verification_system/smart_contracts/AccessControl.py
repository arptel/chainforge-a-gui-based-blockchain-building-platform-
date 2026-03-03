# AccessControl Smart Contract
# Designed to be pasted into the ChainForge Platform GUI

class AccessControl:
    def __init__(self):
        # Maps user_id -> list of roles e.g., ["ISSUER", "VERIFIER"]
        self.roles = {}
        # Simple admin identity
        self.admin = "system_admin"
        
        # Pre-populate admin
        self.roles[self.admin] = ["ADMIN"]

    def grant_role(self, caller: str, user_id: str, role: str) -> dict:
        """Grants a role to a user. Only an ADMIN can grant roles."""
        caller_roles = self.roles.get(caller, [])
        if "ADMIN" not in caller_roles and caller != self.admin:
            return {"error": "Unauthorized: Only ADMIN can grant roles"}
            
        if user_id not in self.roles:
            self.roles[user_id] = []
            
        role_upper = role.upper()
        if role_upper not in self.roles[user_id]:
            self.roles[user_id].append(role_upper)
            
        return {"status": "success", "message": f"Role {role_upper} granted to {user_id}"}

    def revoke_role(self, caller: str, user_id: str, role: str) -> dict:
        """Revokes a role from a user. Only an ADMIN can revoke roles."""
        caller_roles = self.roles.get(caller, [])
        if "ADMIN" not in caller_roles and caller != self.admin:
            return {"error": "Unauthorized: Only ADMIN can revoke roles"}
            
        role_upper = role.upper()
        if user_id in self.roles and role_upper in self.roles[user_id]:
            self.roles[user_id].remove(role_upper)
            return {"status": "success", "message": f"Role {role_upper} revoked from {user_id}"}
            
        return {"error": "User does not have this role"}

    def has_role(self, caller: str, user_id: str, role: str) -> dict:
        """Checks if a user has a specific role. Anyone can check roles."""
        role_upper = role.upper()
        user_roles = self.roles.get(user_id, [])
        
        has_it = role_upper in user_roles
        return {"status": "success", "has_role": has_it, "roles": user_roles}
    
    def get_all_roles(self, caller: str, user_id: str) -> dict:
        """Returns all roles for a given user."""
        return {"status": "success", "roles": self.roles.get(user_id, [])}
