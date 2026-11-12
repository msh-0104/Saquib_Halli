from __future__ import annotations

from pathlib import Path

import pytest

from src.database import Database, DatabaseConfig
from src.repository import RepositoryError, TaskRepository
from src.service import (
    NotFoundError,
    TaskCreate,
    TaskService,
    TaskUpdate,
    ValidationError,
)


@pytest.fixture()
def service(tmp_path: Path) -> TaskService:
    db = Database(DatabaseConfig(path=str(tmp_path / "service.db")))
    db.init_schema()
    repo = TaskRepository(db)
    return TaskService(repo)


def test_create_task_happy_path(service: TaskService) -> None:
    task = service.create(
        TaskCreate(
            title="  Buy milk  ",
            description="  2 liters  ",
            status="pending",
            priority=2,
            due_date="2030-01-01",
        )
    )

    assert task.id > 0
    assert task.title == "Buy milk"
    assert task.description == "2 liters"
    assert task.status == "pending"
    assert task.priority == 2
    assert task.due_date == "2030-01-01"
    assert task.created_at
    assert task.updated_at


@pytest.mark.parametrize("title", ["", "   ", "\t", "\n", "\u00a0"])
def test_create_rejects_blank_or_whitespace_only_title(
    service: TaskService, title: str
) -> None:
    with pytest.raises(ValidationError):
        service.create(TaskCreate(title=title))


def test_create_rejects_non_string_and_too_long_title(service: TaskService) -> None:
    with pytest.raises(ValidationError):
        service.create(TaskCreate(title=None))  # type: ignore[arg-type]

    with pytest.raises(ValidationError):
        service.create(TaskCreate(title=123))  # type: ignore[arg-type]

    with pytest.raises(ValidationError):
        service.create(TaskCreate(title="x" * 256))


def test_create_rejects_invalid_status_priority_due_date(service: TaskService) -> None:
    with pytest.raises(ValidationError):
        service.create(TaskCreate(title="Task", status="archived"))

    with pytest.raises(ValidationError):
        service.create(TaskCreate(title="Task", priority=True))  # type: ignore[arg-type]

    with pytest.raises(ValidationError):
        service.create(TaskCreate(title="Task", priority=6))

    with pytest.raises(ValidationError):
        service.create(TaskCreate(title="Task", due_date="not-a-date"))


def test_get_missing_task_raises_not_found(service: TaskService) -> None:
    with pytest.raises(NotFoundError):
        service.get(999999)


def test_update_happy_path(service: TaskService) -> None:
    created = service.create(TaskCreate(title="Original", description="old"))
    updated = service.update(
        created.id,
        TaskUpdate(
            title="Updated",
            description="new description",
            status="done",
            priority=4,
            due_date="2030-02-02",
        ),
    )

    assert updated.id == created.id
    assert updated.title == "Updated"
    assert updated.description == "new description"
    assert updated.status == "done"
    assert updated.priority == 4
    assert updated.due_date == "2030-02-02"


def test_update_keeps_other_fields_when_clearing_due_date(service: TaskService) -> None:
    created = service.create(TaskCreate(title="Before", due_date="2030-01-01"))
    updated = service.update(
        created.id,
        TaskUpdate(title="Renamed", clear_due_date=True),
    )

    assert updated.title == "Renamed"
    assert updated.due_date is None
    assert updated.description == created.description
    assert updated.status == created.status


def test_update_preserves_existing_value_when_no_new_value_is_provided(
    service: TaskService,
) -> None:
    created = service.create(TaskCreate(title="Before", due_date="2030-01-01"))
    updated = service.update(created.id, TaskUpdate(title="After"))
    assert updated.due_date == "2030-01-01"


def test_update_rejects_invalid_title_and_preserves_current_record(
    service: TaskService,
) -> None:
    created = service.create(TaskCreate(title="Original"))
    with pytest.raises(ValidationError):
        service.update(created.id, TaskUpdate(title="   "))

    assert service.get(created.id).title == "Original"


def test_update_missing_task_raises_not_found(service: TaskService) -> None:
    with pytest.raises(NotFoundError):
        service.update(999999, TaskUpdate(title="Missing"))


def test_delete_missing_task_raises_not_found(service: TaskService) -> None:
    with pytest.raises(NotFoundError):
        service.delete(999999)


def test_delete_only_removes_selected_task(service: TaskService) -> None:
    first = service.create(TaskCreate(title="First"))
    second = service.create(TaskCreate(title="Second"))

    service.delete(first.id)

    assert service.get(second.id).title == "Second"
    with pytest.raises(NotFoundError):
        service.get(first.id)


def test_search_query_filters_title_only_and_is_case_insensitive(
    service: TaskService,
) -> None:
    service.create(TaskCreate(title="Straße Alpha", description="needle in description"))
    service.create(TaskCreate(title="STRASSE Beta", status="done"))
    service.create(TaskCreate(title="Other task", status="done"))

    assert [t.title for t in service.search(q="strasse")] == ["Straße Alpha", "STRASSE Beta"]
    assert [t.title for t in service.search(q="needle")] == []
    assert [t.title for t in service.search(q="  ")] == ["Straße Alpha", "STRASSE Beta", "Other task"]


def test_search_status_and_query_are_combined_with_and_logic(
    service: TaskService,
) -> None:
    service.create(TaskCreate(title="Alpha pending", status="pending"))
    service.create(TaskCreate(title="Alpha done", status="done"))
    service.create(TaskCreate(title="Beta done", status="done"))

    found = service.search(q="alpha", status="done")
    assert [t.title for t in found] == ["Alpha done"]


def test_search_rejects_invalid_sort_direction_and_unknown_field(
    service: TaskService,
) -> None:
    with pytest.raises(Exception):
        service.search(sort_by="; DROP TABLE tasks")

    with pytest.raises(Exception):
        service.search(sort_dir="sideways")


@pytest.mark.parametrize(
    "kwargs",
    [
        {"limit": -1},
        {"offset": -1},
        {"limit": True},
        {"offset": "1"},
    ],
)
def test_search_rejects_invalid_pagination(service: TaskService, kwargs: dict) -> None:
    with pytest.raises(ValidationError):
        service.search(**kwargs)


def test_search_rejects_invalid_range_values(service: TaskService) -> None:
    with pytest.raises(ValidationError):
        service.search(priority_min=5, priority_max=1)

    with pytest.raises(ValidationError):
        service.search(due_after="2030-02-01", due_before="2030-01-01")


def test_search_does_not_mutate_persisted_records(service: TaskService) -> None:
    service.create(TaskCreate(title="Alpha"))
    before = service.search()
    service.search(q="alpha")
    after = service.search()
    assert before == after
