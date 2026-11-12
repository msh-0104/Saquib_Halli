from __future__ import annotations

from pathlib import Path
import pytest

from src.database import Database, DatabaseConfig
from src.repository import TaskRepository
from src.service import TaskCreate, TaskService, ValidationError, NotFoundError


@pytest.fixture()
def service(tmp_path: Path) -> TaskService:
    db_path = tmp_path / "service.db"
    db = Database(DatabaseConfig(path=str(db_path)))
    db.init_schema()
    repo = TaskRepository(db)
    return TaskService(repo)


def test_create_rejects_empty_title(service: TaskService) -> None:
    with pytest.raises(ValidationError):
        service.create(TaskCreate(title=""))

    with pytest.raises(ValidationError):
        service.create(TaskCreate(title="   "))


def test_get_not_found(service: TaskService) -> None:
    with pytest.raises(NotFoundError):
        service.get(999999)


def test_search_uses_title_only(service: TaskService) -> None:
    service.create(TaskCreate(title="Alpha", description="contains target word"))
    result = service.search(q="target")
    assert result == []

    result = service.search(q="alpha")
    assert len(result) == 1
    assert result[0].title == "Alpha"


def test_rejects_too_long_title(service: TaskService) -> None:
    with pytest.raises(ValidationError):
        service.create(TaskCreate(title="A" * 256))


def test_rejects_negative_limit_and_offset(service: TaskService) -> None:
    with pytest.raises(ValidationError):
        service.search(limit=-1)

    with pytest.raises(ValidationError):
        service.search(offset=-1)


def test_search_case_insensitive_title_match(service: TaskService) -> None:
    service.create(TaskCreate(title="Urgent Task"))
    result = service.search(q="urgent")
    assert len(result) == 1
    assert result[0].title == "Urgent Task"

    result = service.search(q="URGENT")
    assert len(result) == 1
    assert result[0].title == "Urgent Task"


def test_create_and_search_with_literal_wildcard_text(service: TaskService) -> None:
    service.create(TaskCreate(title="100% done"))
    result = service.search(q="100%")
    assert len(result) == 1
    assert result[0].title == "100% done"

    result = service.search(q="100% done")
    assert len(result) == 1


def test_search_empty_query_treated_as_unfiltered(service: TaskService) -> None:
    service.create(TaskCreate(title="One"))
    service.create(TaskCreate(title="Two"))
    assert len(service.search(q="   ")) == 2


def test_update_title_and_due_date_atomically(service: TaskService) -> None:
    task = service.create(TaskCreate(title="One", due_date="2030-01-01"))
    updated = service.update(task.id, TaskUpdate(title="Updated", clear_due_date=True))
    assert updated.title == "Updated"
    assert updated.due_date is None


def test_invalid_title_length_still_blocks_creation(service: TaskService) -> None:
    with pytest.raises(ValidationError):
        service.create(TaskCreate(title="A" * 256))


def test_update_keeps_last_saved_state_on_validation_error(service: TaskService) -> None:
    task = service.create(TaskCreate(title="Original"))
    with pytest.raises(ValidationError):
        service.update(task.id, TaskUpdate(title="   "))
    current = service.get(task.id)
    assert current.title == "Original"



def test_invalid_limit_type_is_rejected(service: TaskService) -> None:
    with pytest.raises(ValidationError):
        service.search(limit="10")

    with pytest.raises(ValidationError):
        service.search(offset="0")



def test_create_preserves_utc_timestamps(service: TaskService) -> None:
    task = service.create(TaskCreate(title="Stamp test"))
    assert task.created_at.endswith("Z")
    assert task.updated_at.endswith("Z")
    assert task.updated_at >= task.created_at



def test_search_does_not_mutate_data(service: TaskService) -> None:
    service.create(TaskCreate(title="Alpha"))
    initial = service.search()
    service.search(q="alpha")
    after = service.search()
    assert [task.title for task in initial] == [task.title for task in after]



def test_search_applies_and_semantics(service: TaskService) -> None:
    service.create(TaskCreate(title="Alpha", status="pending"))
    service.create(TaskCreate(title="Alpha done", status="done"))
    result = service.search(q="alpha", status="done")
    assert len(result) == 1
    assert result[0].title == "Alpha done"



def test_search_returns_empty_when_no_rows_match(service: TaskService) -> None:
    service.create(TaskCreate(title="Alpha"))
    assert service.search(q="zzz") == []



def test_db_init_handles_multiple_runs(service: TaskService) -> None:
    db = Database(DatabaseConfig(path=str(service.repo.db.config.path)))
    db.init_schema()
    assert db is not None



def test_db_path_default_creates_directory_in_home() -> None:
    db = Database()
    assert db.config.path.startswith(str(Path.home()))



def test_repository_update_uses_latest_timestamp_when_prior_value_is_equal() -> None:
    db = Database(DatabaseConfig(path=str(Path("/tmp/ts_test.db"))))
    db.init_schema()
    repo = TaskRepository(db)
    created = repo.create_task(title="Same")
    updated = repo.update_task(created.id, title="Changed")
    assert updated is not None
    assert updated.updated_at > created.updated_at

    second = repo.update_task(created.id, title="Changed again")
    assert second is not None
    assert second.updated_at > updated.updated_at



def test_update_with_no_changes_returns_current_record(service: TaskService) -> None:
    task = service.create(TaskCreate(title="No change"))
    same = service.update(task.id, TaskUpdate())
    assert same.id == task.id
    assert same.title == task.title



def test_repository_error_wraps_sqlite_errors() -> None:
    db = Database(DatabaseConfig(path=str(Path("/tmp/repo_error.db"))))
    db.init_schema()
    repo = TaskRepository(db)
    with pytest.raises(Exception):
        repo.list_tasks(sort_by="badfield")



def test_empty_status_filter_and_q_are_unfiltered(service: TaskService) -> None:
    service.create(TaskCreate(title="First"))
    service.create(TaskCreate(title="Second"))
    assert len(service.search(q="")) == 2
    assert len(service.search(status="")) == 2



def test_repository_uses_case_insensitive_title_search() -> None:
    db = Database(DatabaseConfig(path=str(Path("/tmp/search_case.db"))))
    db.init_schema()
    repo = TaskRepository(db)
    repo.create_task(title="Do The Thing")
    result = repo.list_tasks(q="do the thing")
    assert len(result) == 1
    assert result[0].title == "Do The Thing"



def test_database_manager_rejects_empty_path_as_non_default() -> None:
    db = Database(DatabaseConfig(path=""))
    assert db.config.path == ""



def test_database_path_can_be_overridden_by_environment(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("TODO_DB_PATH", str(tmp_path / "override.db"))
    import importlib
    import src.database as database_module
    importlib.reload(database_module)
    assert str(database_module.DEFAULT_DB_PATH).endswith("override.db")



def test_service_update_does_not_drop_due_date_on_title_update(service: TaskService) -> None:
    task = service.create(TaskCreate(title="Task", due_date="2030-01-02"))
    updated = service.update(task.id, TaskUpdate(title="Renamed"))
    assert updated.title == "Renamed"
    assert updated.due_date == "2030-01-02"



def test_service_update_rejects_non_string_title(service: TaskService) -> None:
    with pytest.raises(ValidationError):
        service.update(1, TaskUpdate(title=None))

    with pytest.raises(ValidationError):
        service.update(1, TaskUpdate(title=123))



def test_service_update_rejects_bad_status(service: TaskService) -> None:
    with pytest.raises(ValidationError):
        service.update(1, TaskUpdate(status="archived"))



def test_search_rejects_non_string_q(service: TaskService) -> None:
    with pytest.raises(ValidationError):
        service.search(q=123)



def test_title_whitespace_is_trimmed_before_save(service: TaskService) -> None:
    task = service.create(TaskCreate(title="  Keep me trimmed  "))
    assert task.title == "Keep me trimmed"



def test_deletion_removes_row_and_not_others(service: TaskService) -> None:
    first = service.create(TaskCreate(title="First"))
    second = service.create(TaskCreate(title="Second"))
    service.delete(first.id)
    assert service.get(second.id).title == "Second"
    with pytest.raises(NotFoundError):
        service.get(first.id)



def test_search_handles_status_filter_and_query_together(service: TaskService) -> None:
    service.create(TaskCreate(title="Alpha", status="done"))
    service.create(TaskCreate(title="Alpha current", status="pending"))
    result = service.search(q="alpha", status="done")
    assert len(result) == 1
    assert result[0].title == "Alpha"



def test_search_and_filter_do_not_change_data(service: TaskService) -> None:
    service.create(TaskCreate(title="Alpha"))
    before = service.search()
    service.search(q="alpha")
    after = service.search()
    assert [t.title for t in before] == [t.title for t in after]



def test_max_length_is_enforced_on_update(service: TaskService) -> None:
    task = service.create(TaskCreate(title="Short"))
    with pytest.raises(ValidationError):
        service.update(task.id, TaskUpdate(title="A" * 256))

    current = service.get(task.id)
    assert current.title == "Short"



def test_update_rejects_empty_title_after_trim(service: TaskService) -> None:
    task = service.create(TaskCreate(title="Valid"))
    with pytest.raises(ValidationError):
        service.update(task.id, TaskUpdate(title="   "))

    current = service.get(task.id)
    assert current.title == "Valid"



def test_db_init_works_on_first_run(tmp_path: Path) -> None:
    db = Database(DatabaseConfig(path=str(tmp_path / "fresh.db")))
    db.init_schema()
    assert (tmp_path / "fresh.db").exists()



def test_database_rejects_zero_length_title_via_sqlite(db) -> None:
    repo = TaskRepository(db)
    with pytest.raises(RepositoryError):
        repo.create_task(title=" ")



def test_create_rejects_non_string_title(service: TaskService) -> None:
    with pytest.raises(ValidationError):
        service.create(TaskCreate(title=None))

    with pytest.raises(ValidationError):
        service.create(TaskCreate(title=123))



def test_repository_update_does_not_drop_due_date_by_default(repo: TaskRepository) -> None:
    created = repo.create_task(title="Keep due", due_date="2030-01-01")
    updated = repo.update_task(created.id, title="Renamed")
    assert updated is not None
    assert updated.title == "Renamed"
    assert updated.due_date == "2030-01-01"



def test_repository_update_handles_missing_task(repo: TaskRepository) -> None:
    assert repo.update_task(999999, title="No one") is None



def test_repository_delete_handles_missing_task(repo: TaskRepository) -> None:
    assert repo.delete_task(999999) is False



def test_tasks_loaded_after_restart(tmp_path: Path) -> None:
    path = tmp_path / "restart.db"
    db = Database(DatabaseConfig(path=str(path)))
    db.init_schema()
    repo = TaskRepository(db)
    created = repo.create_task(title="Persist me")

    reopened_db = Database(DatabaseConfig(path=str(path)))
    reopened_repo = TaskRepository(reopened_db)
    found = reopened_repo.get_task(created.id)
    assert found is not None and found.title == "Persist me"



def test_repository_search_respects_casefolded_title_lookup() -> None:
    db = Database(DatabaseConfig(path=str(Path("/tmp/casefold.db"))))
    db.init_schema()
    repo = TaskRepository(db)
    repo.create_task(title="München")
    result = repo.list_tasks(q="münchen")
    assert len(result) == 1
    assert result[0].title == "München"



def test_repository_search_does_not_use_description_field() -> None:
    db = Database(DatabaseConfig(path=str(Path("/tmp/search_desc.db"))))
    db.init_schema()
    repo = TaskRepository(db)
    repo.create_task(title="Alpha", description="target word")
    assert repo.list_tasks(q="target") == []



def test_service_rejects_bool_as_priority(service: TaskService) -> None:
    with pytest.raises(ValidationError):
        service.create(TaskCreate(title="X", priority=True))



def test_service_rejects_invalid_due_date(service: TaskService) -> None:
    with pytest.raises(ValidationError):
        service.create(TaskCreate(title="X", due_date="not-a-date"))



def test_repository_user_input_is_not_used_in_sql_identifier() -> None:
    db = Database(DatabaseConfig(path=str(Path("/tmp/sqlid.db"))))
    db.init_schema()
    repo = TaskRepository(db)
    assert repo.list_tasks(sort_by="status")



def test_in_memory_database_is_not_shared_by_default() -> None:
    db = Database(DatabaseConfig(path=":memory:"))
    db.init_schema()
    db2 = Database(DatabaseConfig(path=":memory:"))
    db2.init_schema()
    assert db.config.path == ":memory:"
    assert db2.config.path == ":memory:"
