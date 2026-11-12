from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from src.database import Database, DatabaseConfig, DatabaseError


def test_init_schema_creates_expected_table_and_indexes(tmp_path: Path) -> None:
    db = Database(DatabaseConfig(path=str(tmp_path / "schema.db")))
    db.init_schema()

    with db.session() as connection:
        table = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'tasks'"
        ).fetchone()
        indexes = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'index' AND name LIKE 'idx_tasks_%'"
        ).fetchall()

    assert table is not None
    assert len(indexes) >= 1


def test_init_schema_is_idempotent_and_preserves_data(tmp_path: Path) -> None:
    db = Database(DatabaseConfig(path=str(tmp_path / "idempotent.db")))
    db.init_schema()
    with db.session() as connection:
        connection.execute("INSERT INTO tasks (title) VALUES (?)", ("Keep me",))

    db.init_schema()
    with db.session() as connection:
        rows = connection.execute("SELECT title FROM tasks").fetchall()

    assert rows == [{"title": "Keep me"}]


def test_database_constraints_reject_invalid_task_fields(tmp_path: Path) -> None:
    db = Database(DatabaseConfig(path=str(tmp_path / "constraints.db")))
    db.init_schema()

    invalid_rows = [
        ("", "pending", 0),
        ("   ", "pending", 0),
        ("x" * 256, "pending", 0),
        ("Valid", "unknown", 0),
        ("Valid", "pending", 6),
    ]
    for title, status, priority in invalid_rows:
        with pytest.raises(sqlite3.IntegrityError):
            with db.session() as connection:
                connection.execute(
                    "INSERT INTO tasks (title, status, priority) VALUES (?, ?, ?)",
                    (title, status, priority),
                )


def test_database_sets_timestamps_on_insert(tmp_path: Path) -> None:
    db = Database(DatabaseConfig(path=str(tmp_path / "timestamps.db")))
    db.init_schema()
    with db.session() as connection:
        connection.execute("INSERT INTO tasks (title) VALUES (?)", ("Timestamped",))
        row = connection.execute("SELECT created_at, updated_at FROM tasks").fetchone()

    assert row is not None
    assert row["created_at"]
    assert row["updated_at"]


def test_session_wraps_sqlite_errors_and_preserves_cause(tmp_path: Path) -> None:
    db = Database(DatabaseConfig(path=str(tmp_path / "errors.db")))
    with pytest.raises(DatabaseError) as error:
        with db.session() as connection:
            connection.execute("SELECT * FROM missing_table")

    assert isinstance(error.value.__cause__, sqlite3.Error)


def test_database_config_path_override_creates_parent_directory(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "app.db"
    db = Database(DatabaseConfig(path=str(path)))
    db.init_schema()
    assert path.is_file()


def test_memory_database_sessions_do_not_share_schema(tmp_path: Path) -> None:
    """Document current behavior: each :memory: connection has a separate DB."""
    db = Database(DatabaseConfig(path=":memory:"))
    db.init_schema()
    with db.session() as connection:
        with pytest.raises(sqlite3.OperationalError):
            connection.execute("SELECT * FROM tasks")
