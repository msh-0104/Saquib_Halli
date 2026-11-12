from __future__ import annotations

from pathlib import Path
import pytest

from src.database import Database, DatabaseConfig
from src.repository import TaskRepository


@pytest.fixture()
def repo(tmp_path: Path) -> TaskRepository:
    db_path = tmp_path / "test.db"
    db = Database(DatabaseConfig(path=str(db_path)))
    db.init_schema()
    return TaskRepository(db)


def test_create_and_get(repo: TaskRepository) -> None:
    created = repo.create_task(title="Buy milk")
    assert created.id > 0
    assert created.title == "Buy milk"

    fetched = repo.get_task(created.id)
    assert fetched is not None
    assert fetched.id == created.id


def test_list_tasks(repo: TaskRepository) -> None:
    repo.create_task(title="A")
    repo.create_task(title="B")
    tasks = repo.list_tasks()
    assert len(tasks) >= 2


def test_search_title_only_matches_title(repo: TaskRepository) -> None:
    repo.create_task(title="Alpha", description="target mention")
    found = repo.list_tasks(q="target")
    assert found == []

    found = repo.list_tasks(q="alpha")
    assert len(found) == 1
    assert found[0].title == "Alpha"


def test_update_task_keeps_other_fields_when_clearing_due_date(repo: TaskRepository) -> None:
    created = repo.create_task(title="Example", due_date="2030-01-01")
    updated = repo.update_task(created.id, title="Renamed", due_date=None)
    assert updated is not None
    assert updated.title == "Renamed"
    assert updated.due_date is None


def test_updated_at_moves_forward(repo: TaskRepository) -> None:
    created = repo.create_task(title="Loop")
    updated = repo.update_task(created.id, title="Loop 2")
    assert updated is not None
    assert updated.updated_at > created.updated_at


def test_list_tasks_applies_limit_and_offset(repo: TaskRepository) -> None:
    for idx in range(5):
        repo.create_task(title=f"Task {idx}")

    items = repo.list_tasks(limit=2, offset=1)
    assert len(items) == 2
    assert items[0].title == "Task 1"
    assert items[1].title == "Task 2"


def test_list_tasks_rejects_negative_pagination(repo: TaskRepository) -> None:
    with pytest.raises(Exception):
        repo.list_tasks(limit=-1)

    with pytest.raises(Exception):
        repo.list_tasks(offset=-1)



def test_db_path_override_works(tmp_path: Path) -> None:
    custom = tmp_path / "custom" / "todo.db"
    db = Database(DatabaseConfig(path=str(custom)))
    db.init_schema()
    assert custom.exists()
