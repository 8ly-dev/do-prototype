from fastapi import APIRouter, Depends
from app.models.task import TaskCreate, TaskResponse
from app.dependencies import get_current_user, get_db

router = APIRouter()

@router.post("", response_model=TaskResponse)
def create_task(
    task: TaskCreate,
    db=Depends(get_db),
    user=Depends(get_current_user)
):
    # Implementation using your DB model
    pass

@router.get("/{task_id}", response_model=TaskResponse)
def get_task_details(task_id: int, db=Depends(get_db)):
    # Implementation
    pass
