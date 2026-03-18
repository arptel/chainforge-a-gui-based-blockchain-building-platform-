from passlib.context import CryptContext

def test_isolated_hashing():
    print("Testing Isolated Hashing Logic...")
    
    # This matches our new configuration in auth.py
    pwd_context = CryptContext(schemes=["bcrypt", "pbkdf2_sha256"], deprecated="auto")
    
    password = "secure_password123"
    
    # 1. Test Bcrypt (New default)
    bcrypt_hash = pwd_context.hash(password)
    print(f"Bcrypt Hash: {bcrypt_hash}")
    assert bcrypt_hash.startswith("$2b$") or bcrypt_hash.startswith("$2a$"), "Should be bcrypt"
    assert pwd_context.verify(password, bcrypt_hash), "Bcrypt verification failed"
    print("✓ Bcrypt works")

    # 2. Test PBKDF2 (Old fallback)
    old_context = CryptContext(schemes=["pbkdf2_sha256"])
    old_hash = old_context.hash(password)
    print(f"PBKDF2 Hash: {old_hash}")
    assert old_hash.startswith("$pbkdf2-sha256$"), "Should be pbkdf2"
    
    # Verify using the multi-scheme context
    assert pwd_context.verify(password, old_hash), "PBKDF2 fallback verification failed"
    print("✓ PBKDF2 compatibility works")

if __name__ == "__main__":
    try:
        test_isolated_hashing()
        print("\nISOLATED HASHING TESTS PASSED!")
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
