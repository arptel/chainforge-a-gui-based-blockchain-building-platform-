import models
import database
from sqlalchemy.orm import Session

db = database.SessionLocal()
users = db.query(models.User).all()

print(f"Found {len(users)} users:")
for user in users:
    print(f"User: {user.username}, Hash: {user.hashed_password[:20]}...")
    
# Try to verify the password 'Arth' (assuming user meant username Arth, password 4 chars)
# or username 'Arth', password 'test' etc.
    
import auth
try:
    # Test hashing
    h = auth.get_password_hash("test")
    print(f"Test hash generation successful: {h[:20]}...")
except Exception as e:
    print(f"Test hash generation failed: {e}")

db.close()
