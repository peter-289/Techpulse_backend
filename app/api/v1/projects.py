from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.core.unit_of_work import UnitOfWork
from app.database.db_setup import get_db
from app.schemas.project import ProjectRead
from app.services.project_hub_service import ProjectHubService

router = APIRouter(prefix="/api/v1/projects", tags=["Project Hub"])


def get_service(db: Session = Depends(get_db)) -> ProjectHubService:
    return ProjectHubService(UnitOfWork(session=db))


@router.post("", response_model=ProjectRead, status_code=201)
def create_project(
    name: str = Form(...),
    description: str = Form(...),
    version: str | None = Form(None),
    is_public: bool = Form(True),
    file: UploadFile = File(...),
    service: ProjectHubService = Depends(get_service),
    current_user: dict = Depends(get_current_user),
):
    content = file.file.read()
    return service.create_project(
        user_id=int(current_user["user_id"]),
        name=name,
        description=description,
        version=version,
        is_public=is_public,
        filename=file.filename or "project.bin",
        content=content,
    )


@router.get("", response_model=list[ProjectRead], status_code=200)
def list_projects(
    cursor: int | None = Query(None, ge=1),
    limit: int = Query(50, ge=1, le=200),
    service: ProjectHubService = Depends(get_service),
    current_user: dict = Depends(get_current_user),
):
    return service.list_projects(user_id=int(current_user["user_id"]), cursor=cursor, limit=limit)


@router.get("/{project_id}", response_model=ProjectRead, status_code=200)
def get_project(
    project_id: int,
    service: ProjectHubService = Depends(get_service),
    current_user: dict = Depends(get_current_user),
):
    return service.get_project_for_user(user_id=int(current_user["user_id"]), project_id=project_id)


@router.get("/{project_id}/download", status_code=200)
def download_project(
    project_id: int,
    service: ProjectHubService = Depends(get_service),
    current_user: dict = Depends(get_current_user),
):
    project = service.register_download(user_id=int(current_user["user_id"]), project_id=project_id)
    path = Path(project.file_path)
    return FileResponse(path=path, filename=project.file_name, media_type="application/octet-stream")


@router.delete("/{project_id}", status_code=204)
def delete_project(
    project_id: int,
    service: ProjectHubService = Depends(get_service),
    current_user: dict = Depends(get_current_user),
):
    service.delete_project(user_id=int(current_user["user_id"]), project_id=project_id)
    return None
