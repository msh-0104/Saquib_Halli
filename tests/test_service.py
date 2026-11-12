from __future__ import annotations

from pathlib import Path

import pytest

from src.database import Database, DatabaseConfig
from src.repository import RepositoryError, TaskRepository
from src.service import NotFoundError, TaskCreate, TaskService, TaskUpdate, ValidationError


@pytest.fixture()
def service(tmp_path: Path) -> TaskService:
    db = Database(DatabaseConfig(path=str(tmp_path / "service.db")))
    db.init_schema()
    return TaskService(TaskRepository(db))


def test_create_happy_path_trims_and_persists(service: TaskService) -> None:
    task = service.create(TaskCreate(title="  Buy milk  ", description="  2 liters  "))
    assert task.id > 0
    assert task.title == "Buy milk"
    assert task.description == "2 liters"
    assert task.status == "pending"
    assert task.created_at
    assert task.updated_at


@pytest.mark.parametrize("title", [None, 42, "", "  ", "\t\n", "\u00a0"])
def test_create_rejects_missing_invalid_or_blank_title(
    service: TaskService, title: object
) -> None:
    with pytest.raises(ValidationError):
        service.create(TaskCreate(title=title))  # type: ignore[arg-type]


def test_create_title_length_boundaries(service: TaskService) -> None:
    assert len(service.create(TaskCreate(title="x")).title) == 1
    assert len(service.create(TaskCreate(title="x" * 255)).title) == 255
    with pytest.raises(ValidationError):
        service.create(TaskCreate(title="x" * 256))


@pytest.mark.parametrize(
    "data",
    [
        TaskCreate(title="Valid", status="archived"),
        TaskCreate(title="Valid", priority=True),
        TaskCreate(title="Valid", priority=-1),
        TaskCreate(title="Valid", priority=6),
        TaskCreate(title="Valid", due_date="not-a-date"),
    ],
)
def test_create_rejects_invalid_optional_fields(
    service: TaskService, data: TaskCreate
) -> None:
    with pytest.raises(ValidationError):
        service.create(data)


def test_create_missing_required_dataclass_field_raises_type_error() -> None:
    with pytest.raises(TypeError):
        TaskCreate()  # type: ignore[call-arg]


def test_get_missing_task_raises_not_found(service: TaskService) -> None:
    with pytest.raises(NotFoundError):
        service.get(999999)


def test_update_happy_path_preserves_id_and_changes_fields(service: TaskService) -> None:
    created = service.create(TaskCreate(title="Before", due_date="2030-01-01"))
    updated = service.update(created.id, TaskUpdate(title="After", status="done"))

    assert updated.id == created.id
    assert updated.title == "After"
    assert updated.status == "done"
    assert updated.due_date == "2030-01-01"
    assert updated.created_at == created.created_at


def test_update_can_clear_due_date_and_apply_other_fields(service: TaskService) -> None:
    created = service.create(TaskCreate(title="Before", due_date="2030-01-01"))
    updated = service.update(
        created.id,
        TaskUpdate(title="After", status="done", clear_due_date=True),
    )

    assert updated.title == "After"
    assert updated.status == "done"
    assert updated.due_date is None


def test_update_invalid_title_preserves_last_saved_value(service: TaskService) -> None:
    task = service.create(TaskCreate(title="Original"))
    for invalid in ("", "   ", "x" * 256):
        with pytest.raises(ValidationError):
            service.update(task.id, TaskUpdate(title=invalid))
        assert service.get(task.id).title == "Original"


def test_update_missing_task_raises_not_found(service: TaskService) -> None:
    with pytest.raises(NotFoundError):
        service.update(999999, TaskUpdate(title="Missing"))


def test_empty_update_returns_existing_task(service: TaskService) -> None:
    task = service.create(TaskCreate(title="Unchanged"))
    assert service.update(task.id, TaskUpdate()) == task


def test_delete_happy_path_and_missing_id(service: TaskService) -> None:
    task = service.create(TaskCreate(title="Delete me"))
    service.delete(task.id)
    with pytest.raises(NotFoundError):
        service.get(task.id)
    with pytest.raises(NotFoundError):
        service.delete(task.id)


def test_search_combines_query_and_status_and_does_not_mutate(service: TaskService) -> None:
    service.create(TaskCreate(title="Alpha active", status="pending"))
    completed = service.create(TaskCreate(title="Alpha completed", status="done"))
    service.create(TaskCreate(title="Beta completed", status="done"))

    before = service.search()
    result = service.search(q="alpha", status="done")
    after = service.search()

    assert [task.id for task in result] == [completed.id]
    assert before == after


def test_search_empty_query_is_unfiltered_and_no_match_is_empty(service: TaskService) -> None:
    service.create(TaskCreate(title="One"))
    service.create(TaskCreate(title="Two"))
    assert len(service.search(q="  ")) == 2
    assert service.search(q="not present") == []


@pytest.mark.parametrize(
    "kwargs",
    [
        {"q": object()},
        {"status": "archived"},
        {"limit": -1},
        {"offset": -1},
        {"limit": True},
        {"offset": "1"},
        {"sort_dir": "sideways"},
    ],
)
def test_search_rejects_invalid_inputs(service: TaskService, kwargs: dict) -> None:
    with pytest.raises((ValidationError, RepositoryError)):
        service.search(**kwargs)


def test_service_surfaces_repository_read_failure(tmp_path: Path) -> None:
    service = TaskService(
        TaskRepository(Database(DatabaseConfig(path=str(tmp_path / "not-initialized.db"))))
    )
    with pytest.raises(RepositoryError):
        service.search()
