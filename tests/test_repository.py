from __future__ import annotations

from pathlib import Path

import pytest

from src.database import Database, DatabaseConfig
from src.repository import RepositoryError, TaskRepository


@pytest.fixture()
def repo(tmp_path: Path) -> TaskRepository:
    db = Database(DatabaseConfig(path=str(tmp_path / "repository.db")))
    db.init_schema()
    return TaskRepository(db)


def test_create_get_and_stable_unique_ids(repo: TaskRepository) -> None:
    first = repo.create_task(title="First")
    second = repo.create_task(title="Second")

    assert first.id > 0
    assert first.id != second.id
    assert repo.get_task(first.id) == first
    assert repo.get_task(second.id) == second


def test_get_missing_task_returns_none(repo: TaskRepository) -> None:
    assert repo.get_task(999999) is None


def test_update_changes_only_requested_fields_and_preserves_id(repo: TaskRepository) -> None:
    created = repo.create_task(title="Original", description="Keep", due_date="2030-01-01")
    updated = repo.update_task(created.id, title="Updated")

    assert updated is not None
    assert updated.id == created.id
    assert updated.title == "Updated"
    assert updated.description == "Keep"
    assert updated.due_date == "2030-01-01"
    assert updated.created_at == created.created_at
    assert updated.updated_at >= created.updated_at


def test_update_missing_task_returns_none(repo: TaskRepository) -> None:
    assert repo.update_task(999999, title="Missing") is None


def test_update_can_clear_due_date_without_dropping_other_fields(repo: TaskRepository) -> None:
    created = repo.create_task(title="Original", due_date="2030-01-01")
    updated = repo.update_task(created.id, title="Updated", clear_due_date=True)

    assert updated is not None
    assert updated.title == "Updated"
    assert updated.due_date is None


def test_empty_update_returns_current_task(repo: TaskRepository) -> None:
    created = repo.create_task(title="No changes")
    assert repo.update_task(created.id) == created


def test_delete_removes_only_selected_task(repo: TaskRepository) -> None:
    first = repo.create_task(title="First")
    second = repo.create_task(title="Second")

    assert repo.delete_task(first.id) is True
    assert repo.get_task(first.id) is None
    assert repo.get_task(second.id) == second
    assert repo.delete_task(first.id) is False


def test_list_applies_status_and_additional_filters(repo: TaskRepository) -> None:
    active = repo.create_task(title="Write active", status="pending", priority=2)
    completed = repo.create_task(title="Write completed", status="done", priority=4)
    repo.create_task(title="Other completed", status="done", priority=4)

    found = repo.list_tasks(q="write", status="done", priority_min=3)
    assert [task.id for task in found] == [completed.id]
    assert active.id not in [task.id for task in found]


def test_search_is_title_only_case_insensitive_and_literal(repo: TaskRepository) -> None:
    repo.create_task(title="Café 100%", description="secret keyword")
    repo.create_task(title="Different title", description="Café 100%")

    assert len(repo.list_tasks(q="café")) == 1
    assert len(repo.list_tasks(q="100%")) == 1
    assert repo.list_tasks(q="secret keyword") == []


def test_search_uses_unicode_casefold_semantics(repo: TaskRepository) -> None:
    repo.create_task(title="Straße")
    assert len(repo.list_tasks(q="STRASSE")) == 1


def test_sort_fields_are_allowlisted(repo: TaskRepository) -> None:
    with pytest.raises(RepositoryError):
        repo.list_tasks(sort_by="id; DROP TABLE tasks")
    with pytest.raises(RepositoryError):
        repo.list_tasks(sort_dir="asc; DROP TABLE tasks")

    assert repo.create_task(title="Table remains")


@pytest.mark.parametrize(
    "kwargs",
    [
        {"limit": -1},
        {"offset": -1},
        {"limit": True},
        {"offset": "1"},
    ],
)
def test_pagination_rejects_invalid_values(repo: TaskRepository, kwargs: dict) -> None:
    with pytest.raises(RepositoryError):
        repo.list_tasks(**kwargs)


def test_pagination_returns_requested_slice(repo: TaskRepository) -> None:
    for number in range(5):
        repo.create_task(title=f"Task {number}")

    result = repo.list_tasks(sort_by="id", sort_dir="asc", limit=2, offset=1)
    assert [task.title for task in result] == ["Task 1", "Task 2"]


def test_create_rejects_invalid_values_without_partial_rows(repo: TaskRepository) -> None:
    for kwargs in (
        {"title": "   "},
        {"title": "x" * 256},
        {"title": "Valid", "status": "invalid"},
        {"title": "Valid", "priority": 99},
    ):
        with pytest.raises(RepositoryError):
            repo.create_task(**kwargs)

    assert repo.list_tasks() == []


def test_missing_schema_is_an_error_not_an_empty_list(tmp_path: Path) -> None:
    repo = TaskRepository(Database(DatabaseConfig(path=str(tmp_path / "uninitialized.db"))))
    with pytest.raises(RepositoryError):
        repo.list_tasks()
