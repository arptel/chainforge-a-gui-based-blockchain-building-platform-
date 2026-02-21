import sys
import os
import time

# Add templates directory to path (parent of chain_core)
template_parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../templates"))
sys.path.append(template_parent_dir)

# Mock interfaces if necessary, or import real ones
try:
    from chain_core.core.chain import Blockchain
    from chain_core.core.block import Block
    from chain_core.modules.consensus.pow import PoWConsensus
    from chain_core.modules.vm.evm import EVMRuntime
except ImportError as e:
    print(f"Failed to import modules: {e}")
    sys.exit(1)

def verify_integration():
    print("Verifying Core Integration...")
    
    # 1. Instantiate Modules
    consensus = PoWConsensus(difficulty=1) # Low difficulty for test
    runtime = EVMRuntime()
    
    # 2. Instantiate Blockchain with dependencies
    print("Instantiating Blockchain with Consensus and Runtime...")
    chain = Blockchain(consensus=consensus, runtime=runtime)
    
    if chain.consensus is not consensus:
        print("FAILED: Consensus not injected correctly")
        return False
        
    if chain.runtime is not runtime:
        print("FAILED: Runtime not injected correctly")
        return False
        
    print("PASS: Dependencies injected.")
    
    # 3. Create a Block
    last_block = chain.last_block
    new_block = Block(
        index=last_block.index + 1,
        transactions=[{"to": "0x123", "value": 10}],
        timestamp=time.time(),
        previous_hash=last_block.hash,
        validator="0xTestValidator"
    )
    
    # Mine it (since consensus is active)
    print("Mining block...")
    mined_block = consensus.mine_block(new_block)
    
    # 4. Debug Validation
    print(f"Mined Block Hash: {mined_block.hash}")
    computed = mined_block.compute_hash()
    print(f"Computed Hash:    {computed}")
    print(f"Difficulty: {consensus.difficulty}")
    print(f"Target Prefix: {'0' * consensus.difficulty}")
    
    if mined_block.hash != computed:
        print("MISMATCH: Hash does not match content!")
    
    if not mined_block.hash.startswith('0' * consensus.difficulty):
        print("MISMATCH: Hash does not meet difficulty!")

    # 5. Add Block (should trigger validation and execution)
    print("Adding block...")
    if chain.add_block(mined_block):
        print("PASS: Block added successfully.")
        return True
    else:
        print("FAILED: Block addition failed.")
        return False

if __name__ == "__main__":
    if verify_integration():
        print("\nIntegration Verified!")
        sys.exit(0)
    else:
        print("\nIntegration FAILED!")
        sys.exit(1)
