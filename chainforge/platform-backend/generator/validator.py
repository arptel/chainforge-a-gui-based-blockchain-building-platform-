from typing import Dict, Any, List

class ConfigValidator:
    """
    Validates blockchain configuration before generation.
    """
    
    ALLOWED_NETWORKS = ["public", "permissioned"]
    ALLOWED_CONSENSUS = ["pow", "raft", "pbft"]
    ALLOWED_GOVERNANCE = ["centralized", "consortium"]
    
    @staticmethod
    def validate(config: Dict[str, Any]) -> List[str]:
        errors = []
        
        if config.get("networkType") not in ConfigValidator.ALLOWED_NETWORKS:
            errors.append(f"Invalid network type: {config.get('networkType')}")
            
        if config.get("consensus") not in ConfigValidator.ALLOWED_CONSENSUS:
             errors.append(f"Invalid consensus algorithm: {config.get('consensus')}")

        if config.get("governance") not in ConfigValidator.ALLOWED_GOVERNANCE:
             errors.append(f"Invalid governance model: {config.get('governance')}")
             
        node_count = config.get("nodeCount")
        if not isinstance(node_count, int) or node_count < 1:
            errors.append("Node count must be a positive integer")
            
        if config.get("consensus") == "raft" and node_count < 3:
             errors.append("Raft consensus requires at least 3 nodes")
             
        return errors
