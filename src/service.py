from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import List, Optional

from .repository import RepositoryError, Task, TaskRepository


class ValidationError(ValueError):
    """Raised when input validation fails."""


class NotFoundError(LookupError):
    """Raised when a requested task does not exist."""


_STATUS_ALLOWED = {"pending", "done"}
_MAX_TITLE_LENGTH = 255


def _validate_title(title: str) -> str:
    if title is None:
        raise ValidationError("title is required")
    if not isinstance(title, str):
        raise ValidationError("title must be a string")
    cleaned = title.strip()
    if not cleaned:
        raise ValidationError("title must be non-empty")
    if len(cleaned) > _MAX_TITLE_LENGTH:
        raise ValidationError(f"title must be at most {_MAX_TITLE_LENGTH} characters")
    return cleaned


def _validate_description(description: str) -> str:
    if description is None:
        return ""
    if not isinstance(description, str):
        raise ValidationError("description must be a string")
    return description.strip()


def _validate_status(status: str) -> str:
    if not isinstance(status, str) or status not in _STATUS_ALLOWED:
        raise ValidationError("status must be 'pending' or 'done'")
    return status


def _validate_priority(priority: int) -> int:
    if priority is None:
        return 0
    if not isinstance(priority, int) or isinstance(priority, bool):
        raise ValidationError("priority must be an integer")
    if not 0 <= priority <= 5:
        raise ValidationError("priority must be between 0 and 5")
    return priority


def _validate_due_date(due_date: Optional[str]) -> Optional[str]:
    if due_date is None:
        return None
    if not isinstance(due_date, str):
        raise ValidationError("due_date must be a string in YYYY-MM-DD format or None")
    try:
        date.fromisoformat(due_date)
    except ValueError as exc:
        raise ValidationError("due_date must be in YYYY-MM-DD format") from exc
    return due_date


def _validate_non_negative_int(value: int, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValidationError(f"{name} must be a non-negative integer")
    return value


@dataclass(frozen=True)
class TaskCreate:
    title: str
    description: str = ""
    status: str = "pending"
    priority: int = 0
    due_date: Optional[str] = None


@dataclass(frozen=True)
class TaskUpdate:
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[int] = None
    due_date: Optional[str] = None
    clear_due_date: bool = False


class TaskService:
    def __init__(self, repo: TaskRepository):
        self.repo = repo

    def create(self, data: TaskCreate) -> Task:
        return self.repo.create_task(
            title=_validate_title(data.title),
            description=_validate_description(data.description),
            status=_validate_status(data.status),
            priority=_validate_priority(data.priority),
            due_date=_validate_due_date(data.due_date),
        )

    def get(self, task_id: int) -> Task:
        task = self.repo.get_task(task_id)
        if task is None:
            raise NotFoundError(f"Task {task_id} not found")
        return task

    def update(self, task_id: int, data: TaskUpdate) -> Task:
        payload = {}
        if data.title is not None:
            payload["title"] = _validate_title(data.title)
        if data.description is not None:
            payload["description"] = _validate_description(data.description)
        if data.status is not None:
            payload["status"] = _validate_status(data.status)
        if data.priority is not None:
            payload["priority"] = _validate_priority(data.priority)
        if data.clear_due_date:
            payload["clear_due_date"] = True
        elif data.due_date is not None:
            payload["due_date"] = _validate_due_date(data.due_date)

        updated = self.repo.update_task(task_id, **payload)
        if updated is None:
            raise NotFoundError(f"Task {task_id} not found")
        return updated

    def delete(self, task_id: int) -> None:
        if not self.repo.delete_task(task_id):
            raise NotFoundError(f"Task {task_id} not found")

    def search(
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
        if status is not None and status != "":
            _validate_status(status)
        if priority_min is not None:
            _validate_priority(priority_min)
        if priority_max is not None:
            _validate_priority(priority_max)
        if priority_min is not None and priority_max is not None and priority_min > priority_max:
            raise ValidationError("priority_min cannot be greater than priority_max")
        if due_before is not None:
            _validate_due_date(due_before)
        if due_after is not None:
            _validate_due_date(due_after)
        if due_before is not None and due_after is not None and due_after > due_before:
            raise ValidationError("due_after cannot be greater than due_before")
        if q is not None and not isinstance(q, str):
            raise ValidationError("q must be a string")
        if q is not None:
            q = q.strip() or None
        limit = _validate_non_negative_int(limit, "limit")
        offset = _validate_non_negative_int(offset, "offset")

        return self.repo.list_tasks(
            q=q,
            status=status or None,
            priority_min=priority_min,
            priority_max=priority_max,
            due_before=due_before,
            due_after=due_after,
            sort_by=sort_by,
            sort_dir=sort_dir,
            limit=limit,
            offset=offset,
        )
