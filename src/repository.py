from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from .database import Database, DatabaseError


class RepositoryError(Exception):
    """Base exception for repository-related errors."""


@dataclass(frozen=True)
class Task:
    id: int
    title: str
    description: str
    status: str
    priority: int
    due_date: Optional[str]
    created_at: str
    updated_at: str


def _row_to_task(row: Dict[str, Any]) -> Task:
    return Task(
        id=row["id"],
        title=row["title"],
        description=row["description"],
        status=row["status"],
        priority=row["priority"],
        due_date=row["due_date"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _timestamp_now() -> datetime:
    return datetime.now(timezone.utc)


def _format_timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _next_timestamp(previous: Optional[str]) -> str:
    candidate = _timestamp_now()
    if previous:
        try:
            prior = datetime.fromisoformat(previous.replace("Z", "+00:00")).astimezone(timezone.utc)
        except ValueError:
            prior = None
        if prior is not None and candidate <= prior:
            candidate = prior + timedelta(microseconds=1)
    return _format_timestamp(candidate)


_ALLOWED_SORT_FIELDS = {"created_at", "updated_at", "due_date", "priority", "title", "status", "id"}
_ALLOWED_SORT_DIRS = {"asc", "desc"}


class TaskRepository:
    def __init__(self, db: Database):
        self.db = db

    def create_task(
        self,
        *,
        title: str,
        description: str = "",
        status: str = "pending",
        priority: int = 0,
        due_date: Optional[str] = None,
    ) -> Task:
        sql = """
        INSERT INTO tasks (title, description, status, priority, due_date)
        VALUES (?, ?, ?, ?, ?)
        """
        try:
            with self.db.session() as connection:
                connection.execute("BEGIN")
                cursor = connection.execute(sql, (title, description, status, priority, due_date))
                task_id = cursor.lastrowid
                row = connection.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
                connection.execute("COMMIT")
                if row is None:
                    raise RepositoryError("Created task could not be read back")
                return _row_to_task(row)
        except (sqlite3.Error, DatabaseError) as exc:
            raise RepositoryError("Unable to create task") from exc

    def get_task(self, task_id: int) -> Optional[Task]:
        try:
            with self.db.session() as connection:
                row = connection.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
                return _row_to_task(row) if row else None
        except (sqlite3.Error, DatabaseError) as exc:
            raise RepositoryError("Unable to load task") from exc

    def update_task(
        self,
        task_id: int,
        *,
        title: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[int] = None,
        due_date: Optional[str] = None,
        clear_due_date: bool = False,
    ) -> Optional[Task]:
        fields: List[str] = []
        values: List[Any] = []
        if title is not None:
            fields.append("title = ?")
            values.append(title)
        if description is not None:
            fields.append("description = ?")
            values.append(description)
        if status is not None:
            fields.append("status = ?")
            values.append(status)
        if priority is not None:
            fields.append("priority = ?")
            values.append(priority)
        if clear_due_date:
            fields.append("due_date = ?")
            values.append(None)
        elif due_date is not None:
            fields.append("due_date = ?")
            values.append(due_date)

        if not fields:
            return self.get_task(task_id)

        try:
            with self.db.session() as connection:
                connection.execute("BEGIN")
                current = connection.execute(
                    "SELECT updated_at FROM tasks WHERE id = ?", (task_id,)
                ).fetchone()
                if current is None:
                    connection.execute("ROLLBACK")
                    return None
                timestamp = _next_timestamp(current["updated_at"])
                assignments = ", ".join(fields + ["updated_at = ?"])
                values.extend((timestamp, task_id))
                cursor = connection.execute(
                    f"UPDATE tasks SET {assignments} WHERE id = ?", tuple(values)
                )
                if cursor.rowcount == 0:
                    connection.execute("ROLLBACK")
                    return None
                row = connection.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
                connection.execute("COMMIT")
                return _row_to_task(row) if row else None
        except (sqlite3.Error, DatabaseError) as exc:
            raise RepositoryError("Unable to update task") from exc

    def set_due_date(self, task_id: int, due_date: Optional[str]) -> Optional[Task]:
        return self.update_task(task_id, due_date=due_date, clear_due_date=due_date is None)

    def delete_task(self, task_id: int) -> bool:
        try:
            with self.db.session() as connection:
                connection.execute("BEGIN")
                cursor = connection.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
                connection.execute("COMMIT")
                return cursor.rowcount > 0
        except (sqlite3.Error, DatabaseError) as exc:
            raise RepositoryError("Unable to delete task") from exc

    def list_tasks(
        self,
        *,
        q: Optional[str] = None,
        status: Optional[str] = None,
        priority_min: Optional[int] = None,
        priority_max: Optional[int] = None,
        due_before: Optional[str] = None,
        due_after: Optional[str] = None,
        sort_by: str = "created_at",
        sort_dir: str = "desc",
        limit: int = 100,
        offset: int = 0,
    ) -> List[Task]:
        if not isinstance(limit, int) or isinstance(limit, bool) or limit < 0:
            raise RepositoryError("limit must be a non-negative integer")
        if not isinstance(offset, int) or isinstance(offset, bool) or offset < 0:
            raise RepositoryError("offset must be a non-negative integer")
        if sort_by not in _ALLOWED_SORT_FIELDS:
            raise RepositoryError("Invalid sort field")
        if not isinstance(sort_dir, str) or sort_dir.lower() not in _ALLOWED_SORT_DIRS:
            raise RepositoryError("Invalid sort direction")

        clauses: List[str] = []
        params: List[Any] = []
        if status:
            clauses.append("status = ?")
            params.append(status)
        if priority_min is not None:
            clauses.append("priority >= ?")
            params.append(priority_min)
        if priority_max is not None:
            clauses.append("priority <= ?")
            params.append(priority_max)
        if due_before is not None:
            clauses.append("due_date IS NOT NULL AND due_date <= ?")
            params.append(due_before)
        if due_after is not None:
            clauses.append("due_date IS NOT NULL AND due_date >= ?")
            params.append(due_after)

        direction = sort_dir.lower()
        order_by = f"{sort_by} {direction}"
        if sort_by == "due_date":
            order_by = f"(due_date IS NULL) ASC, due_date {direction}"
        sql = "SELECT * FROM tasks"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += f" ORDER BY {order_by}, id ASC"

        try:
            with self.db.session() as connection:
                rows = connection.execute(sql, tuple(params)).fetchall()
        except (sqlite3.Error, DatabaseError) as exc:
            raise RepositoryError("Unable to search tasks") from exc

        if q is not None:
            needle = q.strip().casefold()
            if needle:
                rows = [row for row in rows if needle in row["title"].casefold()]
        rows = rows[offset:offset + limit]
        return [_row_to_task(row) for row in rows]
