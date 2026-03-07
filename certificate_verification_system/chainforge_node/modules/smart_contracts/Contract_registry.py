# contracts_registry.py

SYSTEM_CONTRACTS = {

    # --------------------------------------------------
    # BASE CONTRACTS (ALWAYS INCLUDED)
    # --------------------------------------------------

    "base": {
        "DataStore": {
            "file": "datastore.wasm",
            "methods": ["add", "get", "exists"]
        },

        "Validation": {
            "file": "validation.wasm",
            "methods": ["validate", "validateSignature"]
        },

        "AccessControl": {
            "file": "access_control.wasm",
            "methods": ["grantRole", "revokeRole", "hasRole"]
        },

        "IdentityRegistry": {
            "file": "identity.wasm",
            "methods": ["registerIdentity", "getIdentity"]
        },

        "AuditLog": {
            "file": "audit.wasm",
            "methods": ["logAction", "getLogs"]
        }
    },


    # --------------------------------------------------
    # PUBLIC NETWORK CONTRACTS
    # --------------------------------------------------

    "public": {

        "Participation": {
            "file": "participation.wasm",
            "methods": ["registerNode", "deregisterNode"]
        }
    },


    # --------------------------------------------------
    # CONSENSUS CONTRACTS
    # --------------------------------------------------

    "pow": {

        "MiningReward": {
            "file": "mining_reward.wasm",
            "methods": ["claimReward", "getReward"]
        }
    },

    "poa": {

        "AuthorityManagement": {
            "file": "authority.wasm",
            "methods": ["addAuthority", "removeAuthority", "isAuthority"]
        }
    },

    "pos": {

        "Staking": {
            "file": "staking.wasm",
            "methods": ["stake", "unstake", "getStake"]
        },

        "ValidatorElection": {
            "file": "validator.wasm",
            "methods": ["electValidator", "isValidator"]
        }
    },


    # --------------------------------------------------
    # TOKEN / ECONOMICS
    # --------------------------------------------------

    "token": {

        "NativeToken": {
            "file": "native_token.wasm",
            "methods": ["transfer", "balanceOf", "approve"]
        }
    },


    # --------------------------------------------------
    # SYNC MODE
    # --------------------------------------------------

    "light_sync": {

        "ProofVerifier": {
            "file": "light_proof.wasm",
            "methods": ["verifyProof", "getMerkleProof"]
        }
    },


    # --------------------------------------------------
    # PERMISSIONED (CENTRALIZED)
    # --------------------------------------------------

    "centralized": {

        "AdminControl": {
            "file": "admin.wasm",
            "methods": ["approveNode", "removeNode", "rotateLeader"]
        },

        "Whitelist": {
            "file": "whitelist.wasm",
            "methods": ["addToWhitelist", "removeFromWhitelist", "isWhitelisted"]
        }
    },


    # --------------------------------------------------
    # PERMISSIONED (CONSORTIUM)
    # --------------------------------------------------

    "consortium": {

        "ValidatorCouncil": {
            "file": "council.wasm",
            "methods": ["addValidator", "removeValidator", "getValidators"]
        },

        "MultiSig": {
            "file": "multisig.wasm",
            "methods": ["propose", "approve", "execute"]
        },

        "CertificateAuthority": {
            "file": "ca.wasm",
            "methods": ["issueCert", "revokeCert", "verifyCert"]
        }
    }
}