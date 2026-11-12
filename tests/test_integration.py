from __future__ import annotations

from pathlib import Path

from src.database import Database, DatabaseConfig
from src.repository import TaskRepository
from src.service import TaskCreate, TaskService, TaskUpdate


def test_create_edit_toggle_delete_survive_database_reopen(tmp_path: Path) -> None:
    path = tmp_path / "integration.db"
    first_db = Database(DatabaseConfig(path=str(path)))
    first_db.init_schema()
    first_service = TaskService(TaskRepository(first_db))

    created = first_service.create(TaskCreate(title="Persist through lifecycle"))
    edited = first_service.update(created.id, TaskUpdate(title="Edited", status="done"))
    assert edited.id == created.id
    assert edited.title == "Edited"
    assert edited.status == "done"

    reopened_db = Database(DatabaseConfig(path=str(path)))
    reopened_service = TaskService(TaskRepository(reopened_db))
    loaded = reopened_service.get(created.id)
    assert loaded == edited

    reopened_service.delete(created.id)
    final_service = TaskService(TaskRepository(Database(DatabaseConfig(path=str(path)))))
    assert final_service.search() == []


def test_multiple_tasks_keep_identity_when_one_is_deleted(tmp_path: Path) -> None:
    path = tmp_path / "identity.db"
    db = Database(DatabaseConfig(path=str(path)))
    db.init_schema()
    service = TaskService(TaskRepository(db))

    first = service.create(TaskCreate(title="First"))
    second = service.create(TaskCreate(title="Second"))
    service.delete(first.id)

    assert service.get(second.id).title == "Second"
    assert second.id != first.id


def test_uninitialized_database_read_is_not_reported_as_empty(tmp_path: Path) -> None:
    path = tmp_path / "uninitialized.db"
    service = TaskService(TaskRepository(Database(DatabaseConfig(path=str(path)))))

    try:
        result = service.search()
    except Exception:
        pass
    else:
        raise AssertionError(f"Expected a read failure, got {result!r}")
