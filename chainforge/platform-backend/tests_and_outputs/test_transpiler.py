import sys
import os

# Add paths to enable testing standalone
sys.path.append(os.path.dirname(__file__))

from generator.solidity_transpiler import transpile

def test_transpiler():
    solidity_code = """// SPDX-License-Identifier: MIT
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
}
"""

    print("--- Original Solidity ---")
    print(solidity_code)
    print("\n\n--- Transpiling with Gemini ---")
    
    try:
        python_code = transpile(solidity_code, "SimpleToken")
        print("\n\n--- Transpiled Python Output ---")
        print(python_code)
    except Exception as e:
        print(f"\n[ERROR] Transpilation failed: {e}")

if __name__ == "__main__":
    test_transpiler()
