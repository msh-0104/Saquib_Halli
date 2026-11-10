from __future__ import annotations

from pathlib import Path
import pytest

from src.database import Database, DatabaseConfig
from src.repository import TaskRepository
from src.service import TaskCreate, TaskService, ValidationError, NotFoundError


@pytest.fixture()
def service(tmp_path: Path) -> TaskService:
    db_path = tmp_path / "service.db"
    db = Database(DatabaseConfig(path=str(db_path)))
    db.init_schema()
    repo = TaskRepository(db)
    return TaskService(repo)


def test_create_rejects_empty_title(service: TaskService) -> None:
    with pytest.raises(ValidationError):
        service.create(TaskCreate(title=""))

    with pytest.raises(ValidationError):
        service.create(TaskCreate(title="   "))


def test_get_not_found(service: TaskService) -> None:
    with pytest.raises(NotFoundError):
        service.get(999999)