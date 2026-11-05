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


DEFAULT_DB_PATH = os.environ.get("TODO_DB_PATH", "todo.db")


def _dict_factory(cursor: sqlite3.Cursor, row: tuple) -> dict:
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


class Database:
    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig(path=DEFAULT_DB_PATH)

    def connect(self) -> sqlite3.Connection:
        if self.config.path not in (":memory:", ""):
            Path(self.config.path).parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(
            self.config.path,
            timeout=10,
            isolation_level=None,
            check_same_thread=False,
        )
        conn.row_factory = _dict_factory
        with conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("PRAGMA synchronous = NORMAL;")
        return conn

    @contextmanager
    def session(self) -> Iterator[sqlite3.Connection]:
        conn = self.connect()
        try:
            yield conn
        except sqlite3.Error as e:
            raise DatabaseError(str(e)) from e
        finally:
            conn.close()

    def init_schema(self) -> None:
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
            CHECK (status IN ('pending','done')),
            CHECK (priority BETWEEN 0 AND 5)
        );

        CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
        CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date);
        CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);
        CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at);
        """
        try:
            with self.session() as conn:
                conn.execute("BEGIN;")
                try:
                    conn.executescript(ddl)
                    conn.execute("COMMIT;")
                except sqlite3.Error:
                    conn.execute("ROLLBACK;")
                    raise
        except (sqlite3.Error, DatabaseError) as e:
            raise DatabaseError(f"Failed to initialize schema: {e}") from e

