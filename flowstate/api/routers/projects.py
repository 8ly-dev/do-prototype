from fastapi import APIRouter, Depends
from app.models.project import ProjectCreate, ProjectResponse
from app.dependencies import get_current_user, get_db

router = APIRouter()

@router.post("", response_model=ProjectResponse)
def create_new_project(
    project: ProjectCreate,
    db=Depends(get_db),
    user=Depends(get_current_user)
):
    return db.insert_project(user.id, project)


@router.get("", response_model=list[ProjectResponse])
def list_user_projects(
    db=Depends(get_db),
    user=Depends(get_current_user)
):
    return db.get_projects_by_user(user.id)
