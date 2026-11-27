import pytest
from fastapi.testclient import TestClient
from server import app
from src.database import Database, DatabaseConfig
from src.repository import TaskRepository
from src.service import TaskService, TaskCreate, TaskUpdate

client = TestClient(app)

def test_list_tasks_endpoint():
    """Verify that listing tasks returns a 200 OK and a list."""
    response = client.get("/tasks")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_create_task_endpoint():
    """Verify creating a new task successfully."""
    response = client.post("/tasks", json={
        "title": "Capstone API Test Task",
        "description": "Testing FastAPI backend with pytest",
        "status": "pending",
        "priority": 1
    })
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Capstone API Test Task"
    assert data["status"] == "pending"
    assert "id" in data

def test_create_and_delete_task_lifecycle():
    """Verify full task lifecycle: Create, get, and delete (Gherkin US2)."""
    create_res = client.post("/tasks", json={
        "title": "Lifecycle Task",
        "status": "pending"
    })
    assert create_res.status_code == 201
    task_id = create_res.json()["id"]

    del_res = client.delete(f"/tasks/{task_id}")
    assert del_res.status_code == 204

def test_edit_task_title_and_whitespace():
    """Verify editing task title and whitespace trimming (Gherkin US2)."""
    create_res = client.post("/tasks", json={"title": "Original Title"})
    task_id = create_res.json()["id"]

    # Update with whitespace trimming
    update_res = client.put(f"/tasks/{task_id}", json={"title": "  Trimmed Title  "})
    assert update_res.status_code == 200
    assert update_res.json()["title"] == "Trimmed Title"

    client.delete(f"/tasks/{task_id}")

def test_edit_rejects_empty_title():
    """Verify that updating a task with an empty or whitespace title fails (Gherkin US2)."""
    create_res = client.post("/tasks", json={"title": "Valid Title"})
    task_id = create_res.json()["id"]

    empty_res = client.put(f"/tasks/{task_id}", json={"title": ""})
    assert empty_res.status_code == 400

    space_res = client.put(f"/tasks/{task_id}", json={"title": "   "})
    assert space_res.status_code == 400

    client.delete(f"/tasks/{task_id}")

def test_non_existent_task_operations():
    """Verify 404 Not Found for non-existent task operations (Gherkin US2)."""
    fake_id = 999999
    
    assert client.get("/tasks").status_code == 200
    assert client.delete(f"/tasks/{fake_id}").status_code == 404
    assert client.put(f"/tasks/{fake_id}", json={"status": "done"}).status_code == 404

def test_search_and_status_filtering():
    """Verify multi-condition search and status filtering (Gherkin US3)."""
    # Create test tasks
    t1 = client.post("/tasks", json={"title": "Write report", "status": "pending"}).json()
    t2 = client.post("/tasks", json={"title": "Write tests", "status": "done"}).json()

    # Search query & status filter
    res = client.get("/tasks?q=Write&status=pending")
    assert res.status_code == 200
    tasks = res.json()
    assert any(t["id"] == t1["id"] for t in tasks)
    assert not any(t["id"] == t2["id"] for t in tasks)

    # Invalid status filtering
    bad_res = client.get("/tasks?status=unknown")
    assert bad_res.status_code == 400

    # Cleanup
    client.delete(f"/tasks/{t1['id']}")
    client.delete(f"/tasks/{t2['id']}")

def test_sqlite_persistence_across_restart():
    """Verify that persisted updates and tasks remain available after app restart (Gherkin US1)."""
    # Simulate persistence by instantiating a fresh repository/service instance against the same todo.db
    db = Database(DatabaseConfig(path="todo.db"))
    repo = TaskRepository(db)
    service = TaskService(repo)

    # Create task via service layer
    created = service.create(TaskCreate(title="Persistent Gherkin Task", status="pending"))
    task_id = created.id

    # Update status to done
    service.update(task_id, TaskUpdate(status="done"))

    # "Restart" by initializing a brand new service instance reading from todo.db
    new_db = Database(DatabaseConfig(path="todo.db"))
    new_repo = TaskRepository(new_db)
    new_service = TaskService(new_repo)

    # Retrieve and verify persistence of both existence and updated status
    retrieved = new_service.get(task_id)
    assert retrieved is not None
    assert retrieved.title == "Persistent Gherkin Task"
    assert retrieved.status == "done"

    # Cleanup
    new_service.delete(task_id)