from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional


class DatabaseError(Exception):
    """Base exception for database-related errors."""


@dataclass(frozen=True)
class DatabaseConfig:
    path: str


DEFAULT_DB_PATH = os.environ.get(
    "TODO_DB_PATH",
    str(Path.home() / ".todo_app" / "todo.db"),
)


def _dict_factory(cursor: sqlite3.Cursor, row: tuple) -> dict:
    return {column[0]: row[index] for index, column in enumerate(cursor.description)}


class Database:
    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig(path=DEFAULT_DB_PATH)

    def connect(self) -> sqlite3.Connection:
        raw_path = self.config.path
        if raw_path not in (":memory:", ""):
            path = Path(raw_path).expanduser()
            path.parent.mkdir(parents=True, exist_ok=True)
            resolved_path = str(path)
        else:
            resolved_path = raw_path

        try:
            connection = sqlite3.connect(
                resolved_path,
                timeout=5,
                isolation_level=None,
                check_same_thread=False,
            )
            connection.row_factory = _dict_factory
            connection.execute("PRAGMA busy_timeout = 5000;")
            connection.execute("PRAGMA foreign_keys = ON;")
            if resolved_path != ":memory:":
                connection.execute("PRAGMA journal_mode = WAL;")
            connection.execute("PRAGMA synchronous = NORMAL;")
            return connection
        except (OSError, sqlite3.Error) as exc:
            raise DatabaseError("Unable to open the todo database") from exc

    @contextmanager
    def session(self) -> Iterator[sqlite3.Connection]:
        connection = self.connect()
        try:
            yield connection
        except sqlite3.Error as exc:
            raise DatabaseError("Database operation failed") from exc
        finally:
            connection.close()

    def init_schema(self) -> None:
        """Create the existing task schema and indexes if absent."""
        ddl = """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'pending',
            priority INTEGER NOT NULL DEFAULT 0,
            due_date TEXT NULL,
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
            updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
            CHECK (length(trim(title)) > 0),
            CHECK (length(trim(title)) <= 255),
            CHECK (status IN ('pending','done')),
            CHECK (priority BETWEEN 0 AND 5)
        );
        CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
        CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date);
        CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);
        CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at);
        """
        try:
            with self.session() as connection:
                connection.executescript(ddl)
        except (sqlite3.Error, DatabaseError) as exc:
            raise DatabaseError("Failed to initialize database schema") from exc
