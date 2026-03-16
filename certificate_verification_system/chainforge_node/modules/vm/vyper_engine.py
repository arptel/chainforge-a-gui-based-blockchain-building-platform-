"""
modules/vm/vyper_engine.py

Vyper Smart Contract VM Implementation for ChainForge.
Provides compilation, deployment, and method dispatch for Vyper contracts.

Requires: pip install vyper
"""
import hashlib
import json
import os
import subprocess
from typing import Dict, Any, Optional

try:
    from interfaces.vm import VMInterface
except ImportError:
    from chainforge.templates.chain_core.interfaces.vm import VMInterface

class VyperRuntime(VMInterface):
    """
    Vyper Smart Contract Engine.
    Handles source compilation to bytecode/ABI and manages contract execution.
    """
    def __init__(self):
        self._contracts: Dict[str, Dict[str, Any]] = {}
        self.default_gas_limit = 100000
        
    def deploy_contract(self, source_code: str, sender: str, state: dict = None) -> str:
        """
        Compile and deploy a Vyper contract.
        Returns a deterministic contract address.
        """
        print(f"[Vyper] Deploying contract from {sender}")
        
        # 1. Compile (using mock/simulation if vyper not installed)
        try:
            # Attempt real compilation if vyper CLI is available
            abi, bytecode = self._compile_vyper(source_code)
        except Exception as e:
            print(f"[Vyper] Real compilation failed, using simulation: {e}")
            abi, bytecode = self._simulate_compilation(source_code)

        # 2. Generate address
        seed = f"{sender}:{hashlib.sha256(source_code.encode()).hexdigest()}"
        contract_addr = "0xyp_" + hashlib.sha256(seed.encode()).hexdigest()[:34]
        
        # 3. Store in internal registry
        self._contracts[contract_addr] = {
            "abi": abi,
            "bytecode": bytecode,
            "source": source_code,
            "owner": sender
        }
        
        # 4. Reflect in shared state dict
        if state is not None:
            state[f"contract_{contract_addr}"] = bytecode
            
        print(f"[Vyper] Contract deployed at {contract_addr}")
        return contract_addr

    def execute_transaction(self, tx: dict, state: dict) -> bool:
        """Execute a Vyper transaction (deploy or call)."""
        tx_type = tx.get("type")
        
        if tx_type == "contract_deploy":
            source = tx.get("code", "")
            sender = tx.get("from", "")
            addr = self.deploy_contract(source, sender, state)
            tx["contract_address"] = addr
            return True
            
        elif tx_type == "contract_call":
            return self._execute_call(tx, state)
            
        return False

    def _execute_call(self, tx: dict, state: dict) -> bool:
        contract_addr = tx.get("to")
        method = tx.get("method")
        args = tx.get("args", [])
        
        if contract_addr not in self._contracts:
            print(f"[Vyper] Error: Contract {contract_addr} not found")
            return False
            
        contract = self._contracts[contract_addr]
        print(f"[Vyper] Calling {method}({args}) on {contract_addr}")
        
        # In a real environment, we would use an EVM executor (like py-evm)
        # to run the bytecode against the current state.
        # Here we simulate the state mutation for the demo.
        state[f"{contract_addr}_last_call"] = method
        return True

    def _compile_vyper(self, source: str):
        """Invoke vyper compiler CLI."""
        # Simple check for vyper installation
        result = subprocess.run(["vyper", "--version"], capture_output=True)
        if result.returncode != 0:
            raise RuntimeError("Vyper compiler not found")
            
        # Write to temp file
        with open("temp.vy", "w") as f:
            f.write(source)
            
        # Get ABI
        abi_proc = subprocess.run(["vyper", "-f", "abi", "temp.vy"], capture_output=True, text=True)
        # Get Bytecode
        bin_proc = subprocess.run(["vyper", "-f", "bytecode", "temp.vy"], capture_output=True, text=True)
        
        os.remove("temp.vy")
        return json.loads(abi_proc.stdout), bin_proc.stdout.strip()

    def _simulate_compilation(self, source: str):
        """Fallback simulation for environments without vyper installed."""
        # Extract function names for a fake ABI
        funcs = []
        for line in source.split("\n"):
            if "def " in line:
                name = line.split("def ")[1].split("(")[0]
                funcs.append({"name": name, "type": "function"})
        
        fake_bytecode = "0x" + hashlib.sha256(source.encode()).hexdigest()
        return funcs, fake_bytecode
