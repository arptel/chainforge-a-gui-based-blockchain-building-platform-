from passlib.context import CryptContext

# Configuration
# Note: SECRET_KEY and other JWT settings remain in auth.py for now
# or could be moved here if needed.

pwd_context = CryptContext(schemes=["bcrypt", "pbkdf2_sha256"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)
