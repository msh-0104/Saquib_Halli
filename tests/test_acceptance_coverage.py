from __future__ import annotations

from pathlib import Path

import pytest

from src.database import Database, DatabaseConfig
from src.repository import RepositoryError, TaskRepository
from src.service import (
    NotFoundError,
    TaskCreate,
    TaskService,
    TaskUpdate,
    ValidationError,
)


@pytest.fixture()
def database(tmp_path: Path) -> Database:
    db = Database(DatabaseConfig(path=str(tmp_path / "coverage.db")))
    db.init_schema()
    return db


@pytest.fixture()
def repository(database: Database) -> TaskRepository:
    return TaskRepository(database)


@pytest.fixture()
def service(repository: TaskRepository) -> TaskService:
    return TaskService(repository)


# Service validation: missing fields, normalization, boundaries, and optional fields.

def test_create_missing_required_title_field_is_rejected() -> None:
    with pytest.raises(TypeError):
        TaskCreate()  # type: ignore[call-arg]


def test_create_missing_or_wrong_type_title_is_rejected(service: TaskService) -> None:
    for value in (None, 17):
        with pytest.raises(ValidationError):
            service.create(TaskCreate(title=value))  # type: ignore[arg-type]


@pytest.mark.parametrize("title", ["", " ", "\t\n", "\u00a0", "\u2003"])
def test_create_rejects_whitespace_only_title(service: TaskService, title: str) -> None:
    with pytest.raises(ValidationError, match="non-empty"):
        service.create(TaskCreate(title=title))


def test_title_length_boundaries_are_checked_after_trimming(service: TaskService) -> None:
    assert service.create(TaskCreate(title=" x ")).title == "x"
    assert len(service.create(TaskCreate(title="x" * 255)).title) == 255
    assert len(service.create(TaskCreate(title=" " + "x" * 255 + " ")).title) == 255
    with pytest.raises(ValidationError, match="255"):
        service.create(TaskCreate(title="x" * 256))


@pytest.mark.parametrize(
    "data",
    [
        TaskCreate(title="Valid", description=42),  # type: ignore[arg-type]
        TaskCreate(title="Valid", status="archived"),
        TaskCreate(title="Valid", priority=True),
        TaskCreate(title="Valid", priority=-1),
        TaskCreate(title="Valid", priority=6),
        TaskCreate(title="Valid", due_date="not-a-date"),
        TaskCreate(title="Valid", due_date=20300101),  # type: ignore[arg-type]
    ],
)
def test_invalid_optional_create_fields_are_rejected(
    service: TaskService, data: TaskCreate
) -> None:
    with pytest.raises(ValidationError):
        service.create(data)


def test_optional_create_fields_use_documented_defaults(service: TaskService) -> None:
    task = service.create(TaskCreate(title="Default fields"))
    assert task.description == ""
    assert task.status == "pending"
    assert task.priority == 0
    assert task.due_date is None


def test_invalid_edit_does_not_change_persisted_title(service: TaskService) -> None:
    task = service.create(TaskCreate(title="Saved title"))
    with pytest.raises(ValidationError):
        service.update(task.id, TaskUpdate(title=" " * 256))
    assert service.get(task.id).title == "Saved title"


# Repository operations: stable identity and missing-record behavior.

def test_repository_create_get_update_delete_by_stable_id(
    repository: TaskRepository,
) -> None:
    first = repository.create_task(title="First")
    second = repository.create_task(title="Second")
    assert first.id != second.id

    updated = repository.update_task(first.id, title="First edited", status="done")
    assert updated is not None
    assert updated.id == first.id
    assert updated.title == "First edited"
    assert updated.status == "done"
    assert repository.get_task(second.id) == second

    assert repository.delete_task(first.id) is True
    assert repository.get_task(first.id) is None
    assert repository.get_task(second.id) == second
    assert repository.delete_task(first.id) is False


def test_repository_update_can_clear_one_optional_field_without_losing_others(
    repository: TaskRepository,
) -> None:
    task = repository.create_task(title="Due task", description="Keep this", due_date="2030-01-01")
    updated = repository.update_task(
        task.id,
        title="Renamed",
        clear_due_date=True,
    )
    assert updated is not None
    assert updated.title == "Renamed"
    assert updated.due_date is None
    assert updated.description == "Keep this"


# Search/filter: title-only, Unicode case-insensitive, literal query, AND behavior.

def test_search_is_title_only_casefolded_and_treats_query_as_literal(
    repository: TaskRepository,
) -> None:
    repository.create_task(title="Straße 100%_ready", description="description-only phrase")
    repository.create_task(title="Strasse 1000_ready", description="unrelated")

    assert len(repository.list_tasks(q="STRASSE")) == 2
    assert [task.title for task in repository.list_tasks(q="100%_")] == [
        "Straße 100%_ready"
    ]
    assert repository.list_tasks(q="description-only phrase") == []


def test_search_and_status_filter_use_and_semantics(repository: TaskRepository) -> None:
    repository.create_task(title="Alpha active", status="pending")
    expected = repository.create_task(title="Alpha completed", status="done")
    repository.create_task(title="Beta completed", status="done")

    result = repository.list_tasks(q="alpha", status="done")
    assert [task.id for task in result] == [expected.id]


# Persistence and error cases.

def test_saved_data_is_available_after_database_reopen(tmp_path: Path) -> None:
    path = tmp_path / "reopen.db"
    first_db = Database(DatabaseConfig(path=str(path)))
    first_db.init_schema()
    first_repo = TaskRepository(first_db)
    created = first_repo.create_task(title="Persisted", status="done")

    reopened_repo = TaskRepository(Database(DatabaseConfig(path=str(path))))
    loaded = reopened_repo.get_task(created.id)
    assert loaded == created


def test_missing_schema_is_an_error_not_an_empty_list(tmp_path: Path) -> None:
    repo = TaskRepository(Database(DatabaseConfig(path=str(tmp_path / "missing-schema.db"))))
    with pytest.raises(RepositoryError):
        repo.list_tasks()


def test_invalid_repository_operation_is_rejected(repository: TaskRepository) -> None:
    with pytest.raises(RepositoryError, match="sort"):
        repository.list_tasks(sort_by="id; DROP TABLE tasks")
    # Rejection must not have damaged the table.
    assert repository.create_task(title="Still usable").title == "Still usable"


def test_failed_write_rolls_back_and_preserves_existing_row(
    database: Database, repository: TaskRepository
) -> None:
    original = repository.create_task(title="Keep this value")
    with database.session() as connection:
        connection.execute(
            """
            CREATE TRIGGER reject_task_update
            BEFORE UPDATE ON tasks
            BEGIN
                SELECT RAISE(ABORT, 'simulated write failure');
            END;
            """
        )

    with pytest.raises(RepositoryError):
        repository.update_task(original.id, title="Must not persist")

    assert repository.get_task(original.id) == original


def test_failed_create_does_not_leave_partial_record(
    database: Database, repository: TaskRepository
) -> None:
    with database.session() as connection:
        connection.execute(
            """
            CREATE TRIGGER reject_task_insert
            BEFORE INSERT ON tasks
            BEGIN
                SELECT RAISE(ABORT, 'simulated write failure');
            END;
            """
        )

    with pytest.raises(RepositoryError):
        repository.create_task(title="Must not persist")
    assert repository.list_tasks() == []


# End-to-end workflow: create -> edit -> complete -> reopen -> delete.

def test_full_task_lifecycle_survives_reload_and_deletes_by_id(tmp_path: Path) -> None:
    path = tmp_path / "lifecycle.db"
    first_db = Database(DatabaseConfig(path=str(path)))
    first_db.init_schema()
    first_service = TaskService(TaskRepository(first_db))

    created = first_service.create(TaskCreate(title="Initial title"))
    edited = first_service.update(created.id, TaskUpdate(title="Edited title"))
    completed = first_service.update(edited.id, TaskUpdate(status="done"))

    assert completed.id == created.id
    assert completed.title == "Edited title"
    assert completed.status == "done"
    assert completed.created_at == created.created_at
    assert completed.updated_at > created.updated_at

    reloaded_service = TaskService(TaskRepository(Database(DatabaseConfig(path=str(path)))))
    assert reloaded_service.get(created.id) == completed

    reloaded_service.delete(created.id)
    with pytest.raises(NotFoundError):
        reloaded_service.get(created.id)
    assert reloaded_service.search() == []
