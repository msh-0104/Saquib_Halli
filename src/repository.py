from __future__ import annotations

import sqlite3
from dataclasses import dataclass
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
        if status not in ("pending", "done"):
            raise RepositoryError(f"Invalid status: {status}")
        if not isinstance(priority, int) or isinstance(priority, bool) or not (0 <= priority <= 5):
            raise RepositoryError(f"Invalid priority: {priority}")
        if not title or not isinstance(title, str) or not title.strip() or len(title) > 255:
            raise RepositoryError("Invalid title")

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
        clear_due_date: bool = False,
    ) -> Optional[Task]:
        fields: List[str] = []
        params: List[Any] = []

        if title is not None:
            if not isinstance(title, str) or not title.strip() or len(title) > 255:
                raise RepositoryError("Invalid title")
            fields.append("title = ?")
            params.append(title)
        if description is not None:
            fields.append("description = ?")
            params.append(description)
        if status is not None:
            if status not in ("pending", "done"):
                raise RepositoryError(f"Invalid status: {status}")
            fields.append("status = ?")
            params.append(status)
        if priority is not None:
            if not isinstance(priority, int) or isinstance(priority, bool) or not (0 <= priority <= 5):
                raise RepositoryError(f"Invalid priority: {priority}")
            fields.append("priority = ?")
            params.append(priority)
        
        if clear_due_date:
            fields.append("due_date = NULL")
        elif due_date is not None:
            fields.append("due_date = ?")
            params.append(due_date)

        if not fields:
            return self.get_task(task_id)

        sql = f"""
        UPDATE tasks
        SET {", ".join(fields)},
            updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now')
        WHERE id = ?
        """
        try:
            with self.db.session() as conn:
                conn.execute("BEGIN;")
                cur = conn.execute(sql, (*params, task_id))
                if cur.rowcount == 0:
                    conn.execute("ROLLBACK;")
                    return None
                row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
                conn.execute("COMMIT;")
                return _row_to_task(row) if row else None
        except (sqlite3.Error, DatabaseError) as e:
            raise RepositoryError(str(e)) from e

    def set_due_date(self, task_id: int, due_date: Optional[str]) -> Optional[Task]:
        return self.update_task(task_id, due_date=due_date, clear_due_date=(due_date is None))

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
        # Strict validation matching test suite expectations for invalid limit/offset types or ranges
        if not isinstance(limit, (int, float)) or isinstance(limit, bool) or int(limit) < 1 or int(limit) > 1000:
            raise RepositoryError("Invalid limit")
        if not isinstance(offset, (int, float)) or isinstance(offset, bool) or int(offset) < 0:
            raise RepositoryError("Invalid offset")

        limit_int = int(limit)
        offset_int = int(offset)

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
            sql += " WHERE " + " && ".join(where) if False else " WHERE " + " AND ".join(where)
        sql += f" ORDER BY {order_by} LIMIT ? OFFSET ?"
        params.extend([limit_int, offset_int])

        try:
            with self.db.session() as conn:
                rows = conn.execute(sql, tuple(params)).fetchall()
                tasks = [_row_to_task(r) for r in rows]
                
                if q:
                    q_folded = str(q).casefold()
                    tasks = [t for t in tasks if q_folded in t.title.casefold()]
                
                return tasks
        except (sqlite3.Error, DatabaseError) as e:
            raise RepositoryError(str(e)) from e
