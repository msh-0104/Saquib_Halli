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


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _format_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%fZ")


def _ensure_later_timestamp(previous: Optional[str]) -> str:
    candidate = _utc_now()
    if previous:
        try:
            previous_dt = datetime.strptime(previous, "%Y-%m-%dT%H:%M:%fZ").replace(tzinfo=timezone.utc)
        except ValueError:
            try:
                previous_dt = datetime.fromisoformat(previous.replace("Z", "+00:00")).astimezone(timezone.utc)
            except ValueError:
                previous_dt = None
        if previous_dt is not None and candidate <= previous_dt:
            candidate = previous_dt + timedelta(microseconds=1)
    return _format_utc(candidate)


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
        title = (title or "").strip()
        sql = """
        INSERT INTO tasks (title, description, status, priority, due_date)
        VALUES (?, ?, ?, ?, ?)
        """
        try:
            with self.db.session() as conn:
                conn.execute("BEGIN;")
                cur = conn.execute(sql, (title, description, status, priority, due_date))
                task_id = cur.lastrowid
                row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
                conn.execute("COMMIT;")
                return _row_to_task(row)
        except (sqlite3.Error, DatabaseError) as e:
            raise RepositoryError(str(e)) from e

    def get_task(self, task_id: int) -> Optional[Task]:
        try:
            with self.db.session() as conn:
                row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
                return _row_to_task(row) if row else None
        except (sqlite3.Error, DatabaseError) as e:
            raise RepositoryError(str(e)) from e

    def update_task(
        self,
        task_id: int,
        *,
        title: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[int] = None,
        due_date: Optional[str] = None,
    ) -> Optional[Task]:
        fields: List[str] = []
        params: List[Any] = []

        if title is not None:
            fields.append("title = ?")
            params.append((title or "").strip())
        if description is not None:
            fields.append("description = ?")
            params.append(description)
        if status is not None:
            fields.append("status = ?")
            params.append(status)
        if priority is not None:
            fields.append("priority = ?")
            params.append(priority)
        if due_date is not None:
            fields.append("due_date = ?")
            params.append(due_date)

        if not fields:
            return self.get_task(task_id)

        try:
            with self.db.session() as conn:
                conn.execute("BEGIN;")
                current = conn.execute("SELECT updated_at FROM tasks WHERE id = ?", (task_id,)).fetchone()
                updated_at = _ensure_later_timestamp(current["updated_at"] if current else None)
                sql = f"""
                UPDATE tasks
                SET {', '.join(fields)},
                    updated_at = ?
                WHERE id = ?
                """
                cur = conn.execute(sql, (*params, updated_at, task_id))
                if cur.rowcount == 0:
                    conn.execute("ROLLBACK;")
                    return None
                row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
                conn.execute("COMMIT;")
                return _row_to_task(row) if row else None
        except (sqlite3.Error, DatabaseError) as e:
            raise RepositoryError(str(e)) from e

    def set_due_date(self, task_id: int, due_date: Optional[str]) -> Optional[Task]:
        try:
            with self.db.session() as conn:
                conn.execute("BEGIN;")
                current = conn.execute("SELECT updated_at FROM tasks WHERE id = ?", (task_id,)).fetchone()
                updated_at = _ensure_later_timestamp(current["updated_at"] if current else None)
                cur = conn.execute(
                    """
                    UPDATE tasks
                    SET due_date = ?,
                        updated_at = ?
                    WHERE id = ?
                    """,
                    (due_date, updated_at, task_id),
                )
                if cur.rowcount == 0:
                    conn.execute("ROLLBACK;")
                    return None
                row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
                conn.execute("COMMIT;")
                return _row_to_task(row) if row else None
        except (sqlite3.Error, DatabaseError) as e:
            raise RepositoryError(str(e)) from e

    def delete_task(self, task_id: int) -> bool:
        try:
            with self.db.session() as conn:
                conn.execute("BEGIN;")
                cur = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
                conn.execute("COMMIT;")
                return cur.rowcount > 0
        except (sqlite3.Error, DatabaseError) as e:
            raise RepositoryError(str(e)) from e

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
        if limit < 0:
            raise RepositoryError("limit must be non-negative")
        if offset < 0:
            raise RepositoryError("offset must be non-negative")

        where: List[str] = []
        params: List[Any] = []

        if status:
            where.append("status = ?")
            params.append(status)
        if priority_min is not None:
            where.append("priority >= ?")
            params.append(priority_min)
        if priority_max is not None:
            where.append("priority <= ?")
            params.append(priority_max)
        if due_before is not None:
            where.append("due_date IS NOT NULL AND due_date <= ?")
            params.append(due_before)
        if due_after is not None:
            where.append("due_date IS NOT NULL AND due_date >= ?")
            params.append(due_after)

        if sort_by not in _ALLOWED_SORT_FIELDS:
            raise RepositoryError(f"Invalid sort_by: {sort_by}")
        sort_dir_l = sort_dir.lower()
        if sort_dir_l not in _ALLOWED_SORT_DIRS:
            raise RepositoryError(f"Invalid sort_dir: {sort_dir}")

        order_by = f"{sort_by} {sort_dir_l}"
        if sort_by == "due_date":
            order_by = f"(due_date IS NULL) ASC, due_date {sort_dir_l}"

        sql = "SELECT * FROM tasks"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += f" ORDER BY {order_by}"

        try:
            with self.db.session() as conn:
                rows = conn.execute(sql, tuple(params)).fetchall()
        except (sqlite3.Error, DatabaseError) as e:
            raise RepositoryError(str(e)) from e

        if q is not None:
            needle = q.strip().casefold()
            if needle:
                rows = [row for row in rows if needle in (row["title"] or "").casefold()]
            else:
                rows = list(rows)
        rows = rows[offset:offset + limit]
        return [_row_to_task(row) for row in rows]
