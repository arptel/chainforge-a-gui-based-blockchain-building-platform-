import models
import database
import auth
from sqlalchemy.orm import Session

db = database.SessionLocal()
user = db.query(models.User).filter(models.User.username == "Arth").first()

if user:
    print(f"Updating password for user: {user.username}")
    user.hashed_password = auth.get_password_hash("Arth")
    db.commit()
    print("Password updated to 'Arth'")
else:
    print("User 'Arth' not found.")

db.close()
