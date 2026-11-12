from __future__ import annotations

import sqlite3
from pathlib import Path
import pytest

from src.database import Database, DatabaseConfig
from src.repository import RepositoryError, TaskRepository


@pytest.fixture()
def repo(tmp_path: Path) -> TaskRepository:
    db = Database(DatabaseConfig(path=str(tmp_path / "repository.db")))
    db.init_schema()
    return TaskRepository(db)


def test_create_get_and_ids_are_stable(repo: TaskRepository) -> None:
    first = repo.create_task(title="First")
    second = repo.create_task(title="Second")
    assert first.id != second.id
    assert repo.get_task(first.id) == first


def test_create_and_read_persist_after_reopen(tmp_path: Path) -> None:
    path = tmp_path / "restart.db"
    first_repo = TaskRepository(Database(DatabaseConfig(str(path))))
    first_repo.db.init_schema()
    created = first_repo.create_task(title="Persist", status="done")
    reopened = TaskRepository(Database(DatabaseConfig(str(path))))
    loaded = reopened.get_task(created.id)
    assert loaded is not None
    assert loaded.title == "Persist"
    assert loaded.status == "done"
    assert loaded.id == created.id


def test_update_changes_only_requested_fields_and_timestamp(repo: TaskRepository) -> None:
    created = repo.create_task(title="Original", description="keep", due_date="2030-01-01")
    updated = repo.update_task(created.id, title="Changed")
    assert updated is not None
    assert updated.title == "Changed"
    assert updated.description == "keep"
    assert updated.due_date == "2030-01-01"
    assert updated.created_at == created.created_at
    assert updated.updated_at > created.updated_at


def test_update_can_atomically_clear_date_and_change_other_fields(repo: TaskRepository) -> None:
    created = repo.create_task(title="Original", due_date="2030-01-01")
    updated = repo.update_task(created.id, title="Changed", clear_due_date=True)
    assert updated is not None
    assert updated.title == "Changed"
    assert updated.due_date is None


def test_update_missing_task_returns_none(repo: TaskRepository) -> None:
    assert repo.update_task(999, title="missing") is None


def test_delete_removes_only_selected_record(repo: TaskRepository) -> None:
    first = repo.create_task(title="First")
    second = repo.create_task(title="Second")
    assert repo.delete_task(first.id)
    assert repo.get_task(first.id) is None
    assert repo.get_task(second.id) == second
    assert not repo.delete_task(first.id)


def test_search_matches_title_only_with_unicode_casefold_and_literal_query(repo: TaskRepository) -> None:
    repo.create_task(title="Straße 100%", description="not the title")
    repo.create_task(title="Strasse 1000")
    assert [task.title for task in repo.list_tasks(q="STRASSE")] == ["Straße 100%", "Strasse 1000"]
    assert [task.title for task in repo.list_tasks(q="100%") ] == ["Straße 100%"]
    assert repo.list_tasks(q="not the title") == []


def test_status_filter_and_query_combine(repo: TaskRepository) -> None:
    repo.create_task(title="Alpha active", status="pending")
    done = repo.create_task(title="Alpha complete", status="done")
    repo.create_task(title="Beta complete", status="done")
    result = repo.list_tasks(q="alpha", status="done")
    assert [task.id for task in result] == [done.id]


def test_sort_allowlist_blocks_sql_injection(repo: TaskRepository) -> None:
    with pytest.raises(RepositoryError):
        repo.list_tasks(sort_by="id; DROP TABLE tasks")
    with pytest.raises(RepositoryError):
        repo.list_tasks(sort_dir="asc; DROP TABLE tasks")
    assert repo.create_task(title="Still intact")


@pytest.mark.parametrize("kwargs", [{"limit": -1}, {"offset": -1}, {"limit": True}, {"offset": "1"}])
def test_rejects_bad_pagination(repo: TaskRepository, kwargs: dict) -> None:
    with pytest.raises(RepositoryError):
        repo.list_tasks(**kwargs)


def test_database_constraints_reject_invalid_values(repo: TaskRepository) -> None:
    with pytest.raises(RepositoryError):
        repo.create_task(title=" " * 2)
    with pytest.raises(RepositoryError):
        repo.create_task(title="x" * 256)
    with pytest.raises(RepositoryError):
        repo.create_task(title="valid", status="invalid")


def test_database_errors_are_wrapped_without_raw_sql(repo: TaskRepository) -> None:
    with pytest.raises(RepositoryError):
        repo.list_tasks(sort_by="unknown")


def test_in_memory_database_schema_is_available_during_session() -> None:
    # Separate plain :memory: connections do not share state. This test documents
    # the current supported contract: initialize and use one connection/database
    # instance through an explicitly shared-cache URI is not currently supported.
    db = Database(DatabaseConfig(":memory:"))
    db.init_schema()
    with db.session() as connection:
        assert connection.execute("SELECT name FROM sqlite_master WHERE name='tasks'").fetchone()


def test_database_initialization_is_idempotent(tmp_path: Path) -> None:
    db = Database(DatabaseConfig(str(tmp_path / "idempotent.db")))
    db.init_schema()
    db.init_schema()
    with db.session() as connection:
        assert connection.execute("SELECT count(*) AS n FROM sqlite_master WHERE name='tasks'").fetchone()["n"] == 1
