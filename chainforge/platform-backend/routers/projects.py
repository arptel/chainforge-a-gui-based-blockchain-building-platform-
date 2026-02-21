from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import schemas, database, crud, auth

router = APIRouter(
    prefix="/projects",
    tags=["projects"],
)

@router.post("/", response_model=schemas.Project)
def create_project(
    project: schemas.ProjectCreate,
    db: Session = Depends(database.get_db),
    # AUTH BYPASS: Allow creating projects without login for now
    # current_user: schemas.User = Depends(auth.get_current_user) 
):
    # Default to user_id=1 (admin/test user) if no auth
    user_id = 1 
    return crud.create_project(db=db, project=project, user_id=user_id)

@router.get("/", response_model=List[schemas.Project])
def read_projects(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db),
    # current_user: schemas.User = Depends(auth.get_current_user)
):
    # In a real app, filter by user or admin status
    return crud.get_projects(db, skip=skip, limit=limit)

@router.get("/{project_id}", response_model=schemas.Project)
def read_project(
    project_id: int,
    db: Session = Depends(database.get_db),
    # current_user: schemas.User = Depends(auth.get_current_user)
):
    # Check ownership in real app
    project = db.query(crud.models.Project).filter(crud.models.Project.id == project_id).first()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
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
