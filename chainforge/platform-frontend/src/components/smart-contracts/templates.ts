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
    ],
    "c++": [
        {
            name: "Simple Storage",
            code: `static int storage_value = 0;

extern "C" {
    void set(int value) {
        storage_value = value;
    }
    
    int get() {
        return storage_value;
    }
}`
        },
        {
            name: "Token (ERC20-like)",
            code: `#include <map>
#include <string>

static std::map<std::string, int> balances;
static int total_supply = 0;

extern "C" {
    void mint(const char* to, int amount) {
        balances[std::string(to)] += amount;
        total_supply += amount;
    }

    bool transfer(const char* from, const char* to, int amount) {
        if(balances[std::string(from)] < amount) return false;
        balances[std::string(from)] -= amount;
        balances[std::string(to)] += amount;
        return true;
    }

    int balance_of(const char* address) {
        return balances[std::string(address)];
    }
}`
        },
        {
            name: "Logger",
            code: `#include <string>
#include <vector>

static std::vector<std::string> logs;

extern "C" {
    void log_message(const char* message) {
        logs.push_back(std::string(message));
    }
}`
        }
    ]
};
