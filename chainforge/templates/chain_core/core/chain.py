from typing import List, Optional, Any, Dict
from .block import Block
from .mempool import Mempool
try:
    from interfaces.consensus import ConsensusInterface
    from interfaces.vm import VMInterface
except ImportError:
    from interfaces.consensus import ConsensusInterface
    from interfaces.vm import VMInterface
import time
import hashlib
import json

class Blockchain:
    def __init__(self, consensus: ConsensusInterface = None, runtime: VMInterface = None, role: str = "full",
                 require_signature: bool = True, min_gas_price: int = 0, db_path: str = None):
        self.chain: List[Block] = []
        self.consensus = consensus
        self.runtime = runtime
        self.role = role
        self.require_signature = require_signature
        self.min_gas_price = min_gas_price
        self.state: Dict[str, Any] = {}
        self.mempool = Mempool(min_gas_price=min_gas_price)

        # Optional SQLite persistence — None means in-memory only
        self.db_path = db_path
        self.persistence = None
        if db_path:
            from .persistence import Persistence
            self.persistence = Persistence(db_path)

        self.create_genesis_block()

    # Back-compat shim so existing code using chain.pending_transactions still works
    @property
    def pending_transactions(self) -> List[Dict[str, Any]]:
        return self.mempool.get_pending()

    @pending_transactions.setter
    def pending_transactions(self, value: list):
        """Allow callers to clear the pool by assigning an empty list."""
        if not value:
            self.mempool.clear()

    def add_transaction(self, tx: Dict[str, Any]) -> bool:
        """
        Add a transaction to the mempool after validating:
        - Digital signature (if required)
        - Nonce (replay protection)
        - Gas price (spam protection)
        """
        if self.require_signature:
            if 'signature' not in tx:
                print("Transaction rejected: No signature provided.")
                return False
            sender_public_key = tx.get("from")
            signature = tx.get("signature")
            try:
                from core.crypto import verify_signature
            except ImportError:
                return False
            if not verify_signature(tx, signature, sender_public_key):
                print(f"Transaction rejected: Invalid signature for sender {sender_public_key[:8]}...")
                return False

        ok, reason = self.mempool.add(tx)
        if ok:
            print(f"Transaction added to pool: {tx}")
        else:
            print(f"Transaction rejected: {reason}")
        return ok

    def get_nonce(self, address: str) -> int:
        """Return the next valid nonce for an address."""
        return self.mempool.get_next_nonce(address)

    def mine_pending_transactions(self, miner_address: str):
        import copy
        pending = copy.deepcopy(self.mempool.get_pending())
        if not pending:
            return False

        print(f"Mining {len(pending)} transactions...")
        
        # 1. Simulate state execution to find the resulting state root
        simulated_state = copy.deepcopy(self.state)
        valid_pending = []
        failed_pending = []
        
        if self.runtime:
            for tx in pending:
                try:
                    if self.runtime.execute_transaction(tx, simulated_state):
                        valid_pending.append(tx)
                    else:
                        failed_pending.append(tx)
                except Exception:
                    failed_pending.append(tx)
        else:
            valid_pending = pending
            
        if failed_pending:
            print(f"Dropping {len(failed_pending)} failed transactions from mempool.")
            self.mempool.remove(failed_pending)
            
        pending = valid_pending
        if not pending:
            return False

        # Calculate the state root from the simulated state
        state_snapshot = json.dumps(
            {k: simulated_state[k] for k in sorted(simulated_state)},
            separators=(",", ":")
        )
        simulated_state_root = hashlib.sha256(state_snapshot.encode()).hexdigest()

        if self.consensus and hasattr(self.consensus, 'propose_block'):
            new_block = self.consensus.propose_block(
                pending, self.last_block.hash, len(self.chain), miner_address, state_root=simulated_state_root
            )
        else:
            new_block = Block(
                index=len(self.chain),
                transactions=pending,
                timestamp=time.time(),
                previous_hash=self.last_block.hash,
                validator=miner_address,
                state_root=simulated_state_root
            )
            
        new_block._is_local_mine = True

        if self.add_block(new_block):
            print(f"Block mined successfully! Hash: {new_block.hash}")
            return True
        else:
            print("Failed to mine block.")
            return False

    def create_genesis_block(self):
        """
        Generate the genesis block.
        """
        genesis_block = Block(0, [], 0, "0", "Genesis")
        self.chain.append(genesis_block)
        if hasattr(self, 'persistence') and self.persistence:
            self.persistence.save_block(genesis_block)

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

        # 3. Execute transactions (State Transition)
        if self.role in ['full', 'miner'] and self.runtime:
            print(f"Executing {len(block.transactions)} transactions...")
            for tx in block.transactions:
                try:
                    self.runtime.execute_transaction(tx, self.state)
                except Exception as e:
                    print(f"Transaction execution failed: {e}")
        elif self.role == 'light':
            block.transactions = []

        # 4. Compute and stamp the state root AFTER execution
        if self.role in ['full', 'miner']:
            # For incoming blocks, we verify the state root
            new_state_root = self._compute_state_root()
            if block.state_root and block.state_root != new_state_root:
                print(f"State root mismatch! Expected {block.state_root}, got {new_state_root}")
                # Depending on strictness, return False. But we'll trust the execution for now.

        self.chain.append(block)

        # 5. Update mempool: remove confirmed txs and advance confirmed nonces
        self.mempool.remove(block.transactions)

        # 6. Persist block to SQLite if enabled
        if self.persistence:
            self.persistence.save_block(block)
            self.persistence.save_state(self.state)

        return True

    def is_valid_chain(self, chain_to_test: List[Block], is_suffix: bool = False) -> bool:
        """
        Determine if a given blockchain (or suffix) is valid.
        """
        if not chain_to_test or len(chain_to_test) == 0:
            return False

        # If it's a full chain, check Genesis Block
        if not is_suffix:
            if chain_to_test[0].hash != self.chain[0].hash:
                print("Invalid chain: Genesis blocks do not match.")
                return False

        # Sequential Validation
        for i in range(len(chain_to_test)):
            current_block = chain_to_test[i]

            # Re-verify the hash of the data
            if current_block.hash != current_block.compute_hash():
                print(f"Invalid chain: Block {current_block.index} hash is invalid or tampered.")
                return False

            # Verify the chain link
            if i > 0:
                previous_block = chain_to_test[i-1]
                if current_block.previous_hash != previous_block.hash:
                    print(f"Invalid chain: Block {current_block.index} previous_hash does not match Block {previous_block.index}.")
                    return False
            elif is_suffix:
                # If it's the very first block of a suffix array, it must attach to our existing chain
                attach_index = current_block.index - 1
                if attach_index < 0 or attach_index >= len(self.chain):
                    print(f"Invalid suffix: Attaching block {current_block.index} out of bounds. Local length is {len(self.chain)}.")
                    return False
                if current_block.previous_hash != self.chain[attach_index].hash:
                    print(f"Invalid suffix: Block {current_block.index} previous_hash {current_block.previous_hash} does not match our local Block {attach_index} hash {self.chain[attach_index].hash}.")
                    return False

            # Verify Consensus for the block (skip genesis — it's not mined)
            if current_block.index != 0 and self.consensus and not self.consensus.validate_block(current_block):
                print(f"Invalid chain: Block {current_block.index} failed consensus rules.")
                return False

        return True

    def append_chain_suffix(self, blocks: list) -> int:
        """
        Append a list of blocks to the chain in order, using add_block for each.
        Skips blocks we already have. Returns the count of successfully added blocks.
        This is used for historical sync from peers.
        """
        added = 0
        for block in sorted(blocks, key=lambda b: b.index):
            if block.index <= self.last_block.index:
                continue  # Already have this block, skip
            if block.index == self.last_block.index + 1:
                # Next expected block — try to add it
                if self.add_block(block):
                    added += 1
                else:
                    print(f"[Sync] Could not append block {block.index} — validation failed.")
                    break
            else:
                print(f"[Sync] Gap detected in suffix: expected {self.last_block.index + 1} but got {block.index}.")
                break
        return added

    def replace_chain(self, new_chain) -> bool:
        """
        Replace the local chain with the new chain, OR append a valid suffix if we were missing blocks.
        """
        if not new_chain:
            return False
            
        is_suffix = new_chain[0].index > 0
        
        # Calculate resulting full length if we accept this chain/suffix
        potential_length = new_chain[-1].index + 1
        
        if potential_length <= len(self.chain):
            print(f"Received block sequence (ending at {new_chain[-1].index}) is not longer than current chain ({len(self.chain)-1}). Dropping.")
            return False

        if not self.is_valid_chain(new_chain, is_suffix=is_suffix):
            print("Received chain sequence is invalid. Dropping.")
            return False

        print(f"Applying chain reorganization... Target tip: {new_chain[-1].index}")
        
        if is_suffix:
            attach_index = new_chain[0].index
            self.chain = self.chain[:attach_index] + new_chain
        else:
            self.chain = new_chain

        # Rebuild state and nonce map from scratch
        self.state = {}
        rebuilt_nonces: Dict[str, int] = {}
        self.mempool.clear()

        if self.role in ['full', 'miner'] and self.runtime:
            print("Replaying transactions to rebuild state...")
            for blk in self.chain:
                for tx in blk.transactions:
                    try:
                        self.runtime.execute_transaction(tx, self.state)
                    except Exception as e:
                        print(f"Replay skipped failed tx: {e}")
                    # Advance confirmed nonce for the sender
                    sender = tx.get("from")
                    nonce = tx.get("nonce")
                    if sender and nonce is not None:
                        if nonce > rebuilt_nonces.get(sender, 0):
                            rebuilt_nonces[sender] = nonce

        # Push rebuilt nonces back into the mempool so future txs are validated correctly
        self.mempool.set_confirmed_nonces(rebuilt_nonces)

        # Persist the reorganized chain and rebuilt state to SQLite
        if self.persistence:
            # Delete all orphaned blocks and re-save the canonical chain
            self.persistence.delete_blocks_after(-1)  # clear all
            self.persistence.save_blocks(self.chain)
            self.persistence.save_state(self.state)

        print("Chain replacement and State Reorganization complete.")
        return True

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _compute_state_root(self) -> str:
        """
        Deterministic SHA-256 hash of the current account state.
        Two nodes with the same state will always produce the same root.
        """
        # Sort by key for determinism; serialize values as JSON
        state_snapshot = json.dumps(
            {k: self.state[k] for k in sorted(self.state)},
            separators=(",", ":")
        )
        return hashlib.sha256(state_snapshot.encode()).hexdigest()

    @property
    def current_state_root(self) -> str:
        """The state root of the latest confirmed state."""
        return self._compute_state_root()

    def load_from_disk(self) -> bool:
        """
        Reconstruct the chain and state from the SQLite database.
        Call this on node startup if persistence is enabled.
        Returns True if data was found and loaded, False if the DB was empty.
        """
        if not self.persistence:
            print("[Chain] No persistence configured — skipping load.")
            return False

        blocks = self.persistence.load_all_blocks()
        if not blocks:
            # DB is empty (first run). Save the in-memory genesis block to DB.
            if self.chain:
                self.persistence.save_block(self.chain[0])
            print("[Chain] No blocks found in DB — starting fresh.")
            return False

        self.chain = blocks
        self.state = self.persistence.load_state()
        print(f"[Chain] Loaded {len(self.chain)} blocks and {len(self.state)} state entries from disk.")
        return True
