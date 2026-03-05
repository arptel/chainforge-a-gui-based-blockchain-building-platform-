from ...interfaces.consensus import ConsensusInterface
from typing import Any, Dict
import time

class NoConsensus(ConsensusInterface):
    """
    No Consensus (Single Writer) Implementation.
    """
    def propose_block(self, transactions: list[Dict[str, Any]], previous_hash: str, index: int, miner_address: str, state_root: str = "") -> Any:
        print("[SingleWriter] Writing block directly...")
        return {"id": "block_hash", "txs": transactions}

    def validate_block(self, block: Any) -> bool:
        print("[SingleWriter] No validation needed (trusted source).")
        return True

    def commit_block(self, block: Any) -> bool:
        print("[SingleWriter] Block written.")
        return True
