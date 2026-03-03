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
        
        network_type = config.get("networkType")
        if network_type not in ConfigValidator.ALLOWED_NETWORKS:
            errors.append(f"Invalid network type: {network_type}")
            return errors # Fast fail since everything else depends on networkType
            
        if network_type == "public":
            if not config.get("publicConsensus"):
                errors.append("Public network requires a consensus selection.")
            if not config.get("publicRuntime"):
                errors.append("Public network requires a runtime selection.")
            if not config.get("publicNodeRoles") or len(config.get("publicNodeRoles")) == 0:
                errors.append("Public network requires at least one node role.")
                
        elif network_type == "permissioned":
            permissioned_type = config.get("permissionedType")
            if permissioned_type not in ["centralized", "consortium"]:
                errors.append(f"Invalid permissioned type: {permissioned_type}")
                return errors

            if permissioned_type == "centralized":
                if not config.get("centralizedAuthority"):
                    errors.append("Centralized network requires an authority structure.")
                if not config.get("centralizedConsensus"):
                    errors.append("Centralized network requires a consensus algorithm.")
            elif permissioned_type == "consortium":
                if not config.get("consortiumValidatorStruct"):
                    errors.append("Consortium network requires a validator structure.")
                if not config.get("consortiumConsensus"):
                    errors.append("Consortium network requires a BFT consensus algorithm.")

        if config.get("enableGas") is None:
            errors.append("Gas configuration must be explicitly enabled or disabled.")

        return errors
