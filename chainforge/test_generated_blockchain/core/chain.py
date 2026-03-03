from typing import List, Optional, Any, Dict
from .block import Block
try:
    from interfaces.consensus import ConsensusInterface
    from interfaces.vm import VMInterface
except ImportError:
    # Compile-time/IDE fallback
    from interfaces.consensus import ConsensusInterface
    from interfaces.vm import VMInterface
import time

class Blockchain:
    def __init__(self, consensus: ConsensusInterface = None, runtime: VMInterface = None, role: str = "full"):
        self.chain: List[Block] = []
        self.consensus = consensus
        self.runtime = runtime
        self.role = role
        self.state: Dict[str, Any] = {} # Simple state 
        self.pending_transactions: List[Dict[str, Any]] = []
        self.create_genesis_block()

    def add_transaction(self, tx: Dict[str, Any]):
        """
        Add a transaction to the mempool.
        """
        self.pending_transactions.append(tx)
        print(f"Transaction added to pool: {tx}")

    def mine_pending_transactions(self, miner_address: str):
        if not self.pending_transactions:
            return False

        print(f"Mining {len(self.pending_transactions)} transactions...")
        
        # In a real blockchain, add a reward tx for miner here
        
        new_block = Block(
            index=len(self.chain),
            transactions=self.pending_transactions.copy(),
            timestamp=time.time(),
            previous_hash=self.last_block.hash,
            validator=miner_address
        )

        # Clear pool if successful
        if self.add_block(new_block):
            self.pending_transactions = []
            print(f"Block mined successfully! Hash: {new_block.hash}")
            return True
        else:
            print("Failed to mine block.")
            return False

    def create_genesis_block(self):
        """
        Generate the genesis block.
        """
        genesis_block = Block(0, [], time.time(), "0", "Genesis")
        self.chain.append(genesis_block)

    @property
    def last_block(self) -> Block:
        return self.chain[-1]

    def add_block(self, block: Block) -> bool:
        """
        Add a block to the chain if valid.
        """
        # 1. Basic validation
        if block.previous_hash != self.last_block.hash:
            print(f"Block validation failed: Invalid previous hash {block.previous_hash} != {self.last_block.hash}")
            return False
        
        # 2. Consensus validation
        if self.consensus and not self.consensus.validate_block(block):
            print("Block validation failed: Consensus check failed")
            return False

        # 3. Execute transactions (State Transition) - Only full/miner nodes do this
        if self.role in ['full', 'miner'] and self.runtime:
            print(f"Executing {len(block.transactions)} transactions...")
            for tx in block.transactions:
                try:
                    self.runtime.execute_transaction(tx, self.state)
                except Exception as e:
                    print(f"Transaction execution failed: {e}")
                    # Decide: fail block or skip tx? For now, just log.
        elif self.role == 'light':
            # Light nodes do not store the transactions! Just keep headers.
            # We strip transactions to save space.
            block.transactions = []
        
        self.chain.append(block)
        return True
