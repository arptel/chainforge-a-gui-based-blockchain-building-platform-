def get_default_contracts(config: dict = None):
    if config is None:
        config = {}

    network_type = config.get("networkType", "public").lower()
    consensus = config.get("consensus", "pow").lower()

    contracts = [
        {
            "id": "sys_datastore",
            "name": "DataStore",
            "type": "solidity",
            "apiKey": "sk_sys_datastore",
            "code": """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract DataStore {
    mapping(string => string) private data;

    event Stored(string key, string value);

    function store(string memory key, string memory value) public {
        data[key] = value;
        emit Stored(key, value);
    }

    function retrieve(string memory key) public view returns (string memory) {
        return data[key];
    }
}""".strip()
        },
        {
            "id": "sys_governance",
            "name": "Governance",
            "type": "solidity",
            "apiKey": "sk_sys_governance",
            "code": """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract Governance {
    struct Proposal {
        string description;
        uint256 voteCount;
        bool exists;
    }

    mapping(uint256 => Proposal) public proposals;

    function propose(uint256 proposalId, string memory description) public {
        require(!proposals[proposalId].exists, "Proposal already exists");
        proposals[proposalId] = Proposal(description, 0, true);
    }

    function vote(uint256 proposalId) public {
        require(proposals[proposalId].exists, "Proposal does not exist");
        proposals[proposalId].voteCount += 1;
    }

    function getProposal(uint256 proposalId) public view returns (string memory description, uint256 voteCount) {
        require(proposals[proposalId].exists, "Proposal does not exist");
        return (proposals[proposalId].description, proposals[proposalId].voteCount);
    }
}""".strip()
        }
    ]

    # Include SimpleToken if Pos or not explicitly excluded (for default richness)
    # We will conditionally include it if they use PoS as it heavily relies on staking tokens
    if consensus == "pos":
        contracts.append({
            "id": "sys_token",
            "name": "SimpleToken",
            "type": "solidity",
            "apiKey": "sk_sys_token",
            "code": """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract SimpleToken {
    mapping(address => uint256) public balances;
    uint256 public totalSupply;

    event Transfer(address indexed from, address indexed to, uint256 value);
    event Mint(address indexed to, uint256 value);

    function mint(address to, uint256 amount) public {
        balances[to] += amount;
        totalSupply += amount;
        emit Mint(to, amount);
    }

    function transfer(address to, uint256 amount) public {
        require(balances[msg.sender] >= amount, "Insufficient balance");
        balances[msg.sender] -= amount;
        balances[to] += amount;
        emit Transfer(msg.sender, to, amount);
    }
}""".strip()
        })

    # Include NodeRegistry if permissioned network or authority-based consensus
    if network_type in ["private", "consortium"] or consensus in ["poa", "pbft"]:
        contracts.append({
            "id": "sys_noderegistry",
            "name": "NodeRegistry",
            "type": "solidity",
            "apiKey": "sk_sys_noderegistry",
            "code": """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract NodeRegistry {
    address public admin;

    // Mapping from node address to role (e.g., "full", "miner", "light")
    mapping(address => string) public nodeRoles;
    mapping(address => bool) public isRegistered;

    event NodeRegistered(address indexed node, string role);
    event NodeRemoved(address indexed node);

    modifier onlyAdmin() {
        require(msg.sender == admin, "Only admin can perform this action");
        _;
    }

    constructor() {
        admin = msg.sender;
    }

    function addNodeRole(address node, string memory role) public onlyAdmin {
        nodeRoles[node] = role;
        isRegistered[node] = true;
        emit NodeRegistered(node, role);
    }

    function removeNode(address node) public onlyAdmin {
        isRegistered[node] = false;
        nodeRoles[node] = "";
        emit NodeRemoved(node);
    }

    function hasRole(address node, string memory role) public view returns (bool) {
        if (!isRegistered[node]) return false;
        return (keccak256(abi.encodePacked(nodeRoles[node])) == keccak256(abi.encodePacked(role)));
    }
}""".strip()
        })

    return contracts
