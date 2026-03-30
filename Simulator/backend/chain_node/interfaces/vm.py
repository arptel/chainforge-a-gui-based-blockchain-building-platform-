from abc import ABC, abstractmethod
from typing import Any, Dict, List

class VMInterface(ABC):
    """
    Interface for Smart Contract Virtual Machines (e.g., EVM, WASM).
    """

    @abstractmethod
    def execute_transaction(self, tx: Dict[str, Any], state: Any) -> Any:
        """
        Executes a transaction against the current state.
        """
        pass

    @abstractmethod
    def deploy_contract(self, code: bytes, sender: str) -> str:
        """
        Deploys a contract and returns its address.
        """
        pass
