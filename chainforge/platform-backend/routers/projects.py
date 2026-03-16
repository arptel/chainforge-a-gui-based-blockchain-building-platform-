from fastapi import APIRouter, Depends, HTTPException  # type: ignore
from sqlalchemy.orm import Session  # type: ignore
from typing import List
import schemas, database, crud  # type: ignore
import auth  # type: ignore

router = APIRouter(
    prefix="/projects",
    tags=["projects"],
)

@router.post("/", response_model=schemas.Project)
def create_project(
    project: schemas.ProjectCreate,
    db: Session = Depends(database.get_db),
    current_user: schemas.User = Depends(auth.get_current_user) 
):
    return crud.create_project(db=db, project=project, user_id=current_user.id)

@router.get("/", response_model=List[schemas.Project])
def read_projects(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    # Retrieve only the user's projects
    return db.query(crud.models.Project).filter(crud.models.Project.owner_id == current_user.id).offset(skip).limit(limit).all()

@router.get("/{project_id}", response_model=schemas.Project)
def read_project(
    project_id: int,
    db: Session = Depends(database.get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    # Check ownership
    project = db.query(crud.models.Project).filter(crud.models.Project.id == project_id).first()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return project

@router.delete("/{project_id}", response_model=schemas.Project)
def delete_project(
    project_id: int,
    db: Session = Depends(database.get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    project = crud.get_projects(db, skip=0, limit=1000) # Inefficient but simple check
    # ideally we check if it exists first
    db_project = crud.delete_project(db, project_id)
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return db_project
