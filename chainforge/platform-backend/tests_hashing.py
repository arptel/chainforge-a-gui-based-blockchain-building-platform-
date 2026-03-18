import sys
import os

# Add the current directory to sys.path
sys.path.append(os.path.abspath(os.path.dirname(__file__) + "/.."))

from auth import get_password_hash, verify_password
from passlib.context import CryptContext

def test_hashing():
    print("Testing Password Hashing Standardization...")
    
    # 1. Test New Hashing (should be bcrypt)
    password = "secure_password123"
    bcrypt_hash = get_password_hash(password)
    print(f"New Hash: {bcrypt_hash}")
    assert bcrypt_hash.startswith("$2b$") or bcrypt_hash.startswith("$2a$"), "Hash should be bcrypt"
    assert verify_password(password, bcrypt_hash), "Bcrypt verification failed"
    print("✓ New bcrypt hashing works")

    # 2. Test Old Hashing (pbkdf2_sha256) compatibility
    # Manually create a pbkdf2 hash using the old scheme
    old_context = CryptContext(schemes=["pbkdf2_sha256"])
    old_hash = old_context.hash(password)
    print(f"Old Hash (PBKDF2): {old_hash}")
    assert old_hash.startswith("$pbkdf2-sha256$"), "Initial mock hash should be pbkdf2"
    
    # Verify the old hash using the new context (via auth.verify_password)
    assert verify_password(password, old_hash), "PBKDF2 backward compatibility failed"
    print("✓ PBKDF2 backward compatibility works")

    # 3. Test multi-scheme verification
    assert not verify_password("wrong_password", bcrypt_hash), "Verification should fail for wrong password"
    print("✓ Verification failure works as expected")

if __name__ == "__main__":
    try:
        test_hashing()
        print("\nALL HASHING TESTS PASSED!")
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        sys.exit(1)
