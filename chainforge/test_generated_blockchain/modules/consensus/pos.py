import time
from interfaces.consensus import ConsensusInterface
from core.block import Block

class PoSConsensus(ConsensusInterface):
    """
    Proof of Stake. Checks if block creator has token balance > 0 to validate blocks.
    """
    def __init__(self, chain_state: dict = None):
        self.chain_state = chain_state if chain_state is not None else {}

    def validate_block(self, block: Block) -> bool:
        validator = block.validator
        
        # In this prototype, we check the global chain state for any token balance
        # If they have any generic balance, we consider them a "staker".
        staked_balance = self.chain_state.get(validator, 0)
        
        if staked_balance > 0:
            print(f"[PoS] Block {block.index} validated. Validator {validator} has {staked_balance} staked tokens.")
            return True
        else:
            print(f"[PoS] Block {block.index} REJECTED. Validator {validator} has 0 stake!")
            return False

    def propose_block(self, transactions: list, previous_hash: str, index: int, miner_address: str) -> Block:
        # In a generic PoS, it waits for its specific time slot.
        # We mock this behavior by simply waiting 1 second before proposing.
        print(f"[PoS] Selected as block proposer. Waiting for slot duration...")
        time.sleep(1) 
        
        return Block(
            index=index,
            transactions=transactions,
            timestamp=time.time(),
            previous_hash=previous_hash,
            validator=miner_address
        )

    def commit_block(self, block: Block) -> bool:
        return True
