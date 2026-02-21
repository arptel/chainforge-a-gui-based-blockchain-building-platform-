import os
import sys

# Adjust path to import platform-backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from default_contracts import get_default_contracts

def test_defaults():
    print("Testing PUBLIC + PoW (Default):")
    contracts = get_default_contracts({"networkType": "public", "consensus": "pow"})
    names = [c["name"] for c in contracts]
    print(f"Contracts included: {names}")
    assert "NodeRegistry" not in names, "NodeRegistry should not be in public PoW"
    assert "SimpleToken" not in names, "SimpleToken should not be in public PoW"

    print("\nTesting PUBLIC + PoS:")
    contracts = get_default_contracts({"networkType": "public", "consensus": "pos"})
    names = [c["name"] for c in contracts]
    print(f"Contracts included: {names}")
    assert "SimpleToken" in names, "SimpleToken MUST be in PoS"

    print("\nTesting PRIVATE + PoW:")
    contracts = get_default_contracts({"networkType": "private", "consensus": "pow"})
    names = [c["name"] for c in contracts]
    print(f"Contracts included: {names}")
    assert "NodeRegistry" in names, "NodeRegistry MUST be in private networks"

    print("\nTesting CONSORTIUM + PBFT:")
    contracts = get_default_contracts({"networkType": "consortium", "consensus": "pbft"})
    names = [c["name"] for c in contracts]
    print(f"Contracts included: {names}")
    assert "NodeRegistry" in names, "NodeRegistry MUST be in consortium"

    print("\nAll tests passed successfully!")

if __name__ == "__main__":
    test_defaults()
