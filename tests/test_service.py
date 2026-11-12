from __future__ import annotations

from pathlib import Path
import pytest

from src.database import Database, DatabaseConfig, DatabaseError
from src.repository import RepositoryError, TaskRepository
from src.service import NotFoundError, TaskCreate, TaskService, TaskUpdate, ValidationError


@pytest.fixture()
def service(tmp_path: Path) -> TaskService:
    db = Database(DatabaseConfig(path=str(tmp_path / "service.db")))
    db.init_schema()
    return TaskService(TaskRepository(db))


def test_create_rejects_empty_and_whitespace_titles(service: TaskService) -> None:
    for value in ("", "   ", "\t\n", "\u00a0"):
        with pytest.raises(ValidationError):
            service.create(TaskCreate(title=value))


def test_create_trims_title_and_enforces_maximum(service: TaskService) -> None:
    assert service.create(TaskCreate(title="  ok  ")).title == "ok"
    assert len(service.create(TaskCreate(title="x" * 255)).title) == 255
    with pytest.raises(ValidationError):
        service.create(TaskCreate(title="x" * 256))


def test_update_missing_and_invalid_input(service: TaskService) -> None:
    with pytest.raises(NotFoundError):
        service.get(1)
    with pytest.raises(NotFoundError):
        service.update(1, TaskUpdate(title="valid"))
    with pytest.raises(ValidationError):
        service.create(TaskCreate(title="valid", priority=True))
    with pytest.raises(ValidationError):
        service.create(TaskCreate(title="valid", due_date="2025-99-99"))


def test_read_write_failures_are_reported_as_repository_errors(tmp_path: Path) -> None:
    db = Database(DatabaseConfig(str(tmp_path / "does-not-exist" / "db.sqlite")))
    repo = TaskRepository(db)
    # A missing schema represents a storage/schema failure, not an empty list.
    with pytest.raises(RepositoryError):
        repo.list_tasks()


def test_database_session_wraps_sqlite_errors(tmp_path: Path) -> None:
    db = Database(DatabaseConfig(str(tmp_path / "errors.db")))
    with pytest.raises(DatabaseError):
        with db.session() as connection:
            connection.execute("SELECT * FROM nonexistent_table")


def test_service_maps_repository_not_found(service: TaskService) -> None:
    with pytest.raises(NotFoundError):
        service.delete(123456)


def test_service_search_validates_query_status_and_pagination(service: TaskService) -> None:
    with pytest.raises(ValidationError):
        service.search(q=object())
    with pytest.raises(ValidationError):
        service.search(status="archived")
    with pytest.raises(ValidationError):
        service.search(offset=-2)
    with pytest.raises(ValidationError):
        service.search(limit="100")


def test_service_search_handles_empty_filter_values(service: TaskService) -> None:
    service.create(TaskCreate(title="One"))
    assert len(service.search(q="  ", status="")) == 1


def test_service_update_can_clear_due_date_and_update_title(service: TaskService) -> None:
    task = service.create(TaskCreate(title="Before", due_date="2030-01-01"))
    updated = service.update(task.id, TaskUpdate(title="After", clear_due_date=True))
    assert updated.title == "After"
    assert updated.due_date is None
