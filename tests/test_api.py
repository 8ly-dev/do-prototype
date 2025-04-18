import pytest
from httpx import AsyncClient, ASGITransport
from flowstate.api.main import app

# This fixture ensures pytest runs async tests with asyncio
@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest.fixture
async def async_client():
    async with AsyncClient(
        transport=ASGITransport(app=app),  # ⬅️ Key change
        base_url="http://test"
    ) as ac:
        yield ac

@pytest.mark.anyio
async def test_root(async_client):
    response = await async_client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello, World!"}  # Adjust to your actual root response

@pytest.mark.anyio
async def test_create_project(async_client):
    # Example: Create a user first if required, then create a project
    # user_id = ... (create or fetch user)
    resp = await async_client.post("/projects", json={"user_id": 1, "name": "Test Project"})
    assert resp.status_code == 200 or resp.status_code == 201
    data = resp.json()
    assert "id" in data
    assert data["name"] == "Test Project"

@pytest.mark.anyio
async def test_list_projects(async_client):
    resp = await async_client.get("/projects?user_id=1")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

@pytest.mark.anyio
async def test_create_and_get_task(async_client):
    # Create a milestone first if required
    # milestone_id = ... (create or fetch milestone)
    resp = await async_client.post("/tasks", json={
        "milestone_id": 1,
        "title": "Test Task",
        "description": "Test Desc",
        "due_date": "2025-05-01T12:00:00",
        "priority": 1,
        "task_type": "generic"
    })
    assert resp.status_code == 200 or resp.status_code == 201
    task = resp.json()
    assert task["title"] == "Test Task"

    # Get the task by ID
    resp2 = await async_client.get(f"/tasks/{task['id']}")
    assert resp2.status_code == 200
    assert resp2.json()["id"] == task["id"]

@pytest.mark.anyio
async def test_protected_route_requires_auth(async_client):
    # Try to access a protected endpoint without a token
    resp = await async_client.get("/protected")
    assert resp.status_code == 401
    assert False, "Need to implement this test"
