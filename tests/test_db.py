import os
import tempfile
import pytest

from do.db_models import DoDB  # Replace with your actual module name

@pytest.fixture
def temp_db():
    # Use a temporary file for the database
    fd, path = tempfile.mkstemp()
    os.close(fd)
    db = DoDB(db_path=path)
    yield db
    os.remove(path)

def test_user_crud(temp_db):
    db = temp_db
    username = "testuser"
    user_id = db.insert_user(username)
    assert isinstance(user_id, int)
    user = db.get_user_by_username(username)
    assert user is not None
    assert user.username == username

def test_project_crud(temp_db):
    db = temp_db
    user_id = db.insert_user("projuser")
    project_id = db.insert_project(user_id, "Test Project")
    assert isinstance(project_id, int)
    projects = db.get_projects_by_user(user_id)
    assert any(p.id == project_id for p in projects)

def test_task_crud(temp_db):
    db = temp_db
    user_id = db.insert_user("taskuser")
    project_id = db.insert_project(user_id, "Task Project")
    task_id = db.insert_task(
        project_id,
        "Test Task",
        "Task Description",
        "2025-04-20T12:00:00",
        1,
        "email"
    )
    assert isinstance(task_id, int)
    tasks = db.get_tasks_by_project(project_id)
    assert any(t.id == task_id for t in tasks)

def test_update_and_delete(temp_db):
    db = temp_db
    user_id = db.insert_user("updateuser")
    project_id = db.insert_project(user_id, "Update Project")
    task_id = db.insert_task(
        project_id, "Update Task", None, None, 2, "generic"
    )
    # Update task
    db.update_task(task_id, title="Updated Task", priority=5)
    tasks = db.get_tasks_by_project(project_id)
    updated = [t for t in tasks if t.id == task_id][0]
    assert updated.title == "Updated Task"
    assert updated.priority == 5
    # Delete task
    db.delete_task(task_id)
    tasks = db.get_tasks_by_project(project_id)
    assert not any(t.id == task_id for t in tasks)
    # Delete project
    db.delete_project(project_id)
    projects = db.get_projects_by_user(user_id)
    assert not any(p.id == project_id for p in projects)
