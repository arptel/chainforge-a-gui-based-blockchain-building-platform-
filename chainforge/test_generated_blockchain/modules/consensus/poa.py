import time
from interfaces.consensus import ConsensusInterface
from core.block import Block

class PoAConsensus(ConsensusInterface):
    """
    Proof of Authority. Checks if the block creator holds active authority in the NodeRegistry.
    """
    def __init__(self, chain_state: dict = None):
        self.chain_state = chain_state if chain_state is not None else {}

    def validate_block(self, block: Block) -> bool:
        validator = block.validator
        
        # Rely heavily on the NodeRegistry contract deployed at genesis
        # In our generated network, authority is tracked via the "sys_noderegistry" key mappings
        # In EVM emulation, the mapping 'nodeRoles' is hashed in storage. For mock MWIs, we just check state directly
        is_authority = self.chain_state.get(f"auth_role_{validator}", False)
        
        if is_authority:
            print(f"[PoA] Authorized! Block {block.index} signed by valid Authority.")
            return True
        else:
            print(f"[PoA] REJECTED. Validator {validator} is not registered in NodeRegistry.")
            return False

    def propose_block(self, transactions: list, previous_hash: str, index: int, miner_address: str) -> Block:
        # PoA usually acts instantly for its designated block leader
        print(f"[PoA] Authority node sealing block {index}...")
        return Block(
            index=index,
            transactions=transactions,
            timestamp=time.time(),
            previous_hash=previous_hash,
            validator=miner_address
        )

    def commit_block(self, block: Block) -> bool:
        return True
