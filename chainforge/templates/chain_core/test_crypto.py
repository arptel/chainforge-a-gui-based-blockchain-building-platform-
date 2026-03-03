import sys
import os

# Add the templates directory to the path so imports work correctly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.crypto import generate_keypair, sign_transaction, verify_signature
from core.chain import Blockchain

def test_crypto_functions():
    print("--- Testing Cryptography Functions ---")
    
    # 1. Generate keys
    private_key, public_key = generate_keypair()
    print(f"Generated Private Key: {private_key[:10]}...")
    print(f"Generated Public Key:  {public_key[:10]}...")
    
    # 2. Create a dummy transaction
    tx_data = {
        "from": public_key,
        "to": "some_other_address",
        "amount": 100,
        "type": "transfer"
    }
    
    # 3. Sign the transaction
    signature = sign_transaction(tx_data, private_key)
    print(f"Signature: {signature[:20]}...")
    
    # Add signature to tx for full simulation
    tx_data["signature"] = signature
    
    # 4. Verify the valid signature
    is_valid = verify_signature(tx_data, signature, public_key)
    print(f"Signature is valid (expected True): {is_valid}")
    assert is_valid == True, "Valid signature verification failed!"
    
    # 5. Tamper with the transaction
    tampered_tx = tx_data.copy()
    tampered_tx["amount"] = 500
    is_valid_tampered = verify_signature(tampered_tx, signature, public_key)
    print(f"Tampered signature is valid (expected False): {is_valid_tampered}")
    assert is_valid_tampered == False, "Tampered signature verification failed!"
    
    # 6. Verify with wrong public key
    _, wrong_public_key = generate_keypair()
    is_valid_wrong_key = verify_signature(tx_data, signature, wrong_public_key)
    print(f"Wrong key signature is valid (expected False): {is_valid_wrong_key}")
    assert is_valid_wrong_key == False, "Wrong key signature verification failed!"
    
    print("Crypto functions tests passed!\n")

def test_chain_integration():
    print("--- Testing Blockchain Integration (require_signature=True) ---")
    
    chain = Blockchain(require_signature=True)
    
    # Generate test keys
    private_key, public_key = generate_keypair()
    
    # 1. Unsigned transaction
    unsigned_tx = {
        "from": public_key,
        "to": "recipient",
        "amount": 50
    }
    
    print("Adding unsigned transaction:")
    success1 = chain.add_transaction(unsigned_tx)
    assert success1 == False, "Unsigned transaction was accepted!"
    assert len(chain.pending_transactions) == 0, "Mempool should be empty"
    
    # 2. Signed transaction
    signed_tx = unsigned_tx.copy()
    signature = sign_transaction(signed_tx, private_key)
    signed_tx["signature"] = signature
    
    print("Adding valid signed transaction:")
    success2 = chain.add_transaction(signed_tx)
    assert success2 == True, "Signed transaction was rejected!"
    assert len(chain.pending_transactions) == 1, "Mempool should contain 1 transaction"
    
    # 3. Invalid signature transaction
    invalid_tx = signed_tx.copy()
    invalid_tx["amount"] = 999  # Tampered
    
    print("Adding tampered transaction:")
    success3 = chain.add_transaction(invalid_tx)
    assert success3 == False, "Tampered transaction was accepted!"
    assert len(chain.pending_transactions) == 1, "Mempool should still contain 1 transaction"

    print("Blockchain integration tests (Signature Required) passed!\n")
    
    print("--- Testing Blockchain Integration (require_signature=False) ---")
    
    open_chain = Blockchain(require_signature=False)
    
    print("Adding unsigned transaction to open chain:")
    success_open = open_chain.add_transaction(unsigned_tx)
    assert success_open == True, "Unsigned transaction was rejected on an open chain!"
    assert len(open_chain.pending_transactions) == 1, "Mempool should contain 1 transaction"
    
    print("Blockchain integration tests (Signature Disabled) passed!\n")

if __name__ == "__main__":
    test_crypto_functions()
    test_chain_integration()
    print("ALL TESTS PASSED SUCCESSFULLY!")
