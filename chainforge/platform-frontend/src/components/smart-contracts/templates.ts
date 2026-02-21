export const SMART_CONTRACT_TEMPLATES = {
    python: [
        {
            name: "Simple Storage",
            code: `class SimpleStorage:
    def set(self, value: int):
        self.ctx.state['storage_value'] = value

    def get(self) -> int:
        return self.ctx.state.get('storage_value', 0)`
        },
        {
            name: "Token (ERC20-like)",
            code: `class Token:
    def mint(self, to_address: str, amount: int):
        balances = self.ctx.state.get('balances', {})
        total_supply = self.ctx.state.get('total_supply', 0)
        
        balances[to_address] = balances.get(to_address, 0) + amount
        total_supply += amount
        
        self.ctx.state['balances'] = balances
        self.ctx.state['total_supply'] = total_supply

    def transfer(self, from_address: str, to_address: str, amount: int) -> bool:
        balances = self.ctx.state.get('balances', {})
        if balances.get(from_address, 0) < amount:
            return False
            
        balances[from_address] -= amount
        balances[to_address] = balances.get(to_address, 0) + amount
        self.ctx.state['balances'] = balances
        return True

    def balance_of(self, address: str) -> int:
        balances = self.ctx.state.get('balances', {})
        return balances.get(address, 0)`
        },
        {
            name: "Logger",
            code: `class Logger:
    def log_message(self, sender: str, message: str):
        logs = self.ctx.state.get('logs', [])
        logs.append({"sender": sender, "message": message, "timestamp": "now"})
        self.ctx.state['logs'] = logs

    def get_logs(self):
        return self.ctx.state.get('logs', [])`
        }
    ],
    solidity: [
        {
            name: "Storage",
            code: `// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract Storage {
    uint256 number;

    function store(uint256 num) public {
        number = num;
    }

    function retrieve() public view returns (uint256) {
        return number;
    }
}`
        }
    ]
};
