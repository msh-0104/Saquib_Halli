from __future__ import annotations

from pathlib import Path
import pytest

from src.database import Database, DatabaseConfig
from src.repository import TaskRepository
from src.service import TaskCreate, TaskService, TaskUpdate, ValidationError, NotFoundError


@pytest.fixture()
def service(tmp_path: Path) -> TaskService:
    db = Database(DatabaseConfig(path=str(tmp_path / "service.db")))
    db.init_schema()
    return TaskService(TaskRepository(db))


def test_create_trims_and_persists_title(service: TaskService) -> None:
    task = service.create(TaskCreate(title="  Buy milk  "))
    assert task.title == "Buy milk"
    assert task.id > 0
    assert task.created_at
    assert task.updated_at


@pytest.mark.parametrize("title", ["", "   ", "\t\n"])
def test_create_rejects_missing_or_whitespace_title(service: TaskService, title: str) -> None:
    with pytest.raises(ValidationError):
        service.create(TaskCreate(title=title))


def test_create_rejects_non_string_and_missing_title(service: TaskService) -> None:
    with pytest.raises(ValidationError):
        service.create(TaskCreate(title=None))  # type: ignore[arg-type]
    with pytest.raises(ValidationError):
        service.create(TaskCreate(title=42))  # type: ignore[arg-type]


def test_title_length_boundaries(service: TaskService) -> None:
    min_title = service.create(TaskCreate(title="x"))
    max_title = service.create(TaskCreate(title="x" * 255))
    assert min_title.title == "x"
    assert len(max_title.title) == 255
    with pytest.raises(ValidationError):
        service.create(TaskCreate(title="x" * 256))


def test_update_rejects_invalid_title_and_preserves_saved_value(service: TaskService) -> None:
    task = service.create(TaskCreate(title="Original"))
    with pytest.raises(ValidationError):
        service.update(task.id, TaskUpdate(title=" " * 256))
    assert service.get(task.id).title == "Original"


def test_update_multiple_fields_and_clear_due_date(service: TaskService) -> None:
    task = service.create(TaskCreate(title="Before", due_date="2030-01-01"))
    updated = service.update(task.id, TaskUpdate(title="After", status="done", clear_due_date=True))
    assert updated.id == task.id
    assert updated.title == "After"
    assert updated.status == "done"
    assert updated.due_date is None


def test_update_none_due_date_preserves_existing_value(service: TaskService) -> None:
    task = service.create(TaskCreate(title="Due", due_date="2030-01-01"))
    updated = service.update(task.id, TaskUpdate(title="Renamed"))
    assert updated.due_date == task.due_date


def test_create_and_update_reject_invalid_status_priority_and_date(service: TaskService) -> None:
    with pytest.raises(ValidationError):
        service.create(TaskCreate(title="x", status="archived"))
    with pytest.raises(ValidationError):
        service.create(TaskCreate(title="x", priority=True))
    with pytest.raises(ValidationError):
        service.create(TaskCreate(title="x", priority=6))
    with pytest.raises(ValidationError):
        service.create(TaskCreate(title="x", due_date="not-a-date"))


def test_get_update_delete_missing_task(service: TaskService) -> None:
    with pytest.raises(NotFoundError):
        service.get(9000)
    with pytest.raises(NotFoundError):
        service.update(9000, TaskUpdate(title="missing"))
    with pytest.raises(NotFoundError):
        service.delete(9000)


def test_delete_only_removes_target(service: TaskService) -> None:
    first = service.create(TaskCreate(title="First"))
    second = service.create(TaskCreate(title="Second"))
    service.delete(first.id)
    assert service.get(second.id).title == "Second"


def test_search_title_only_casefold_filters_and_and_logic(service: TaskService) -> None:
    service.create(TaskCreate(title="Straße Alpha", status="done", description="needle"))
    service.create(TaskCreate(title="Straße Beta", status="pending"))
    service.create(TaskCreate(title="Other", status="done"))
    found = service.search(q="STRASSE", status="done")
    assert [task.title for task in found] == ["Straße Alpha"]
    assert service.search(q="needle") == []


def test_search_treats_query_as_literal_substring(service: TaskService) -> None:
    service.create(TaskCreate(title="100% ready"))
    service.create(TaskCreate(title="1000 ready"))
    assert [task.title for task in service.search(q="100%") ] == ["100% ready"]


def test_search_empty_query_and_no_match(service: TaskService) -> None:
    service.create(TaskCreate(title="One"))
    assert len(service.search(q="  ")) == 1
    assert service.search(q="missing") == []


@pytest.mark.parametrize("kwargs", [{"limit": -1}, {"offset": -1}, {"limit": True}, {"offset": "1"}])
def test_search_rejects_invalid_pagination(service: TaskService, kwargs: dict) -> None:
    with pytest.raises(ValidationError):
        service.search(**kwargs)


def test_search_rejects_invalid_sort_fields(service: TaskService) -> None:
    with pytest.raises(Exception):
        service.search(sort_by="; DROP TABLE tasks")
    with pytest.raises(Exception):
        service.search(sort_dir="sideways")


def test_search_rejects_invalid_ranges(service: TaskService) -> None:
    with pytest.raises(ValidationError):
        service.search(priority_min=5, priority_max=1)
    with pytest.raises(ValidationError):
        service.search(due_after="2030-02-01", due_before="2030-01-01")


def test_search_does_not_change_persisted_records(service: TaskService) -> None:
    service.create(TaskCreate(title="Alpha"))
    before = service.search()
    service.search(q="alpha", status="done")
    after = service.search()
    assert before == after
