from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
import schemas, database, crud, auth
from generator.builder import ChainBuilder

router = APIRouter(
    prefix="/generate",
    tags=["generate"],
)

@router.post("/{project_id}/download")
def download_chain(
    """
    Download the blockchain package for a given project.
    Checks project ownership and validates configuration before building.
    """
    project_id: int,
    db: Session = Depends(database.get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    project = db.query(crud.models.Project).filter(crud.models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Validate Config
    from generator.validator import ConfigValidator
    errors = ConfigValidator.validate(project.config)
    if errors:
        raise HTTPException(status_code=400, detail=f"Configuration error: {', '.join(errors)}")

    builder = ChainBuilder(project)
    zip_bytes = builder.build_package()

    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=chain_{project.id}.zip"}
    )

from fastapi import Body

@router.post("/default-contracts")
def get_default_contracts(
    config: dict = Body(...),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    """
    Returns the list of default system smart contracts that will be included 
    based on the provided network configuration.
    """
    try:
        contracts = ChainBuilder.get_default_contracts(config)
        return {"contracts": contracts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{project_id}/install")
def install_chain(
    project_id: int,
    db: Session = Depends(database.get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    """
    Triggers a local docker build of the generated chain.
    WARNING: This executes commands on the host machine.
    """
    import subprocess
    import os
    import tempfile
    
    project = db.query(crud.models.Project).filter(crud.models.Project.id == project_id).first()
    if not project:
         raise HTTPException(status_code=404, detail="Project not found")
    
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    builder = ChainBuilder(project)
    zip_bytes = builder.build_package()
    
    # Create a temp dir to extract and build
    try:
        with tempfile.TemporaryDirectory() as tmpdirname:
            # Extract zip
            import zipfile
            import io
            with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
                zf.extractall(tmpdirname)
            
            # Docker build command
            image_name = f"chainforge-node-{project.id}"
            print(f"DEBUG: Building docker image {image_name} in {tmpdirname}")
            
            # Check if docker is available
            try:
                subprocess.run(["docker", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except (subprocess.CalledProcessError, FileNotFoundError):
                 raise HTTPException(status_code=500, detail="Docker is not installed or not found in PATH on the server.")

            # Build
            process = subprocess.run(
                ["docker", "build", "-t", image_name, "."],
                cwd=tmpdirname,
                capture_output=True,
                text=True
            )
            
            if process.returncode != 0:
                print(f"DEBUG: Docker build failed: {process.stderr}")
                error_msg = process.stderr
                if "error during connect" in error_msg or "The system cannot find the file specified" in error_msg:
                     raise HTTPException(
                        status_code=500, 
                        detail="Docker is not running or not accessible. Please ensure Docker Desktop is running."
                    )
                raise HTTPException(status_code=500, detail=f"Docker build failed: {process.stderr}")
            
            return {"message": f"Successfully built Docker image: {image_name}", "image_name": image_name}
            
    except Exception as e:
        print(f"DEBUG: Install failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
