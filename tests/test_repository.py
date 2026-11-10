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