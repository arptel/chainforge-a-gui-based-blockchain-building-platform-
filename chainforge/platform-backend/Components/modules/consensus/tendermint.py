from ...interfaces.consensus import ConsensusInterface
from typing import Any, Dict
import time

class TendermintConsensus(ConsensusInterface):
    """
    Tendermint-style Consensus Implementation (Stub).
    Fast finality BFT.
    """
    def propose_block(self, transactions: list[Dict[str, Any]]) -> Any:
        print("[Tendermint] Proposer broadcasting block...")
        time.sleep(0.1)
        return {"id": "block_hash", "txs": transactions, "round": 1}

    def validate_block(self, block: Any) -> bool:
        print("[Tendermint] Prevote and Precommit phases...")
        return True

    def commit_block(self, block: Any) -> bool:
        print("[Tendermint] Block finalized.")
        return True
