from sqlalchemy.orm import Session
import models, schemas, default_contracts
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate):
    # Validate password is not empty
    if not user.password or len(user.password.strip()) == 0:
        raise ValueError("Password cannot be empty")
    
    # Bcrypt has a max length of 72 bytes, truncate if needed
    password_to_hash = user.password[:72] if len(user.password) > 72 else user.password
    
    try:
        hashed_password = pwd_context.hash(password_to_hash)
    except Exception as e:
        raise ValueError(f"Password hashing failed: {str(e)}")
    
    db_user = models.User(username=user.username, email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_projects(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Project).offset(skip).limit(limit).all()


def create_project(db: Session, project: schemas.ProjectCreate, user_id: int):
    # Ensure config exists BEFORE getting defaults
    if not project.config:
        project.config = {}
        
    # Inject Default Contracts conditionally based on config
    defaults = default_contracts.get_default_contracts(project.config)
    
    # Ensure smartContracts list exists
    if "smartContracts" not in project.config:
        project.config["smartContracts"] = []
        
    # Append defaults (avoiding duplicates if already present, though simple append is safer for now)
    # We filter out if they already have same ID to prevent duplicates on potential re-runs if logic changes
    existing_ids = [c["id"] for c in project.config["smartContracts"]]
    for d in defaults:
        if d["id"] not in existing_ids:
            project.config["smartContracts"].append(d)
    
    # Force update of the dict to ensure SQLAlchemy detects change (if needed for JSON types)
    # project.config = project.config.copy() 

    db_project = models.Project(**project.dict(), owner_id=user_id)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

def delete_project(db: Session, project_id: int):
    db_project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if db_project:
        db.delete(db_project)
        db.commit()
    return db_project
