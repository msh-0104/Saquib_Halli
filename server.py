from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from src.database import Database, DatabaseConfig
from src.repository import TaskRepository
from src.service import TaskService, TaskCreate, TaskUpdate, ValidationError, NotFoundError

app = FastAPI(title="Brownfield Todo API", version="1.0.0")

# Initialize database and service
db = Database(DatabaseConfig(path="todo.db"))
db.init_schema()
repo = TaskRepository(db)
service = TaskService(repo)

class TaskCreateRequest(BaseModel):
    title: str
    description: str = ""
    status: str = "pending"
    priority: int = 0
    due_date: Optional[str] = None

class TaskUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[int] = None
    due_date: Optional[str] = None
    clear_due_date: bool = False

@app.post("/tasks", status_code=201)
def create_task(req: TaskCreateRequest):
    try:
        task = service.create(TaskCreate(**req.dict()))
        return task
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/tasks")
def list_tasks(q: Optional[str] = None, status: Optional[str] = None):
    try:
        return service.search(q=q, status=status)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/tasks/{task_id}")
def update_task(task_id: int, req: TaskUpdateRequest):
    try:
        return service.update(task_id, TaskUpdate(**req.dict()))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    try:
        service.delete(task_id)
        return None
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))