from __future__ import annotations

import sqlite3
from pathlib import Path
import pytest

from src.database import Database, DatabaseConfig, DatabaseError


def test_database_initialization(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    db = Database(DatabaseConfig(path=str(db_path)))
    db.init_schema()
    
    with db.session() as conn:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='tasks';"
        )
        assert cursor.fetchone() is not None


def test_database_constraints_reject_invalid_task_fields(tmp_path: Path) -> None:
    db = Database(DatabaseConfig(path=str(tmp_path / "constraints.db")))
    db.init_schema()

    invalid_rows = [
        ("", "pending", 0),
        ("   ", "pending", 0),
        ("Valid", "unknown", 0),
        ("Valid", "pending", 6),
    ]
    for title, status, priority in invalid_rows:
        with pytest.raises(DatabaseError):
            with db.session() as connection:
                connection.execute("BEGIN;")
                try:
                    connection.execute(
                        "INSERT INTO tasks (title, status, priority) VALUES (?, ?, ?)",
                        (title, status, priority),
                    )
                    connection.execute("COMMIT;")
                except Exception:
                    connection.execute("ROLLBACK;")
                    raise
