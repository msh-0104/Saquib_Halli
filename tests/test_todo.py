import pytest

from src.database import Database, DatabaseConfig
from src.repository import RepositoryError, TaskRepository
from src.service import NotFoundError, TaskCreate, TaskService, TaskUpdate, ValidationError


@pytest.fixture()
def db(tmp_path):
    db_path = tmp_path / "test_todo.db"
    db = Database(DatabaseConfig(path=str(db_path)))
    db.init_schema()
    return db


@pytest.fixture()
def service(db):
    repo = TaskRepository(db)
    return TaskService(repo)


def test_create_task_success(service: TaskService):
    task = service.create(TaskCreate(title="Buy milk", description="2 liters", priority=2))
    assert task.id > 0
    assert task.title == "Buy milk"
    assert task.description == "2 liters"
    assert task.status == "pending"
    assert task.priority == 2
    assert task.due_date is None


def test_create_task_title_trim_and_non_empty(service: TaskService):
    task = service.create(TaskCreate(title="   Do thing   "))
    assert task.title == "Do thing"

    with pytest.raises(ValidationError):
        service.create(TaskCreate(title="   "))


def test_update_task_success(service: TaskService):
    task = service.create(TaskCreate(title="A", description="d", priority=1))
    updated = service.update(task.id, TaskUpdate(title="B", status="done", priority=5))
    assert updated.id == task.id
    assert updated.title == "B"
    assert updated.status == "done"
    assert updated.priority == 5


def test_update_due_date_set_and_clear(service: TaskService):
    task = service.create(TaskCreate(title="With due", due_date="2030-01-01"))
    assert task.due_date == "2030-01-01"

    updated = service.update(task.id, TaskUpdate(clear_due_date=True))
    assert updated.due_date is None


def test_get_not_found(service: TaskService):
    with pytest.raises(NotFoundError):
        service.get(99999)


def test_update_not_found(service: TaskService):
    with pytest.raises(NotFoundError):
        service.update(99999, TaskUpdate(title="Nope"))


def test_delete_not_found(service: TaskService):
    with pytest.raises(NotFoundError):
        service.delete(99999)


def test_delete_success(service: TaskService):
    task = service.create(TaskCreate(title="To delete"))
    service.delete(task.id)
    with pytest.raises(NotFoundError):
        service.get(task.id)


def test_search_filters_and_sort(service: TaskService):
    t1 = service.create(TaskCreate(title="Write report", description="alpha", priority=3, due_date="2030-01-10"))
    t2 = service.create(TaskCreate(title="Write tests", description="beta", priority=1, due_date="2030-01-05"))
    t3 = service.create(TaskCreate(title="Pay bills", description="gamma", priority=5))

    results = service.search(q="Write", sort_by="due_date", sort_dir="asc")
    assert [t.title for t in results][:2] == ["Write tests", "Write report"]

    service.update(t1.id, TaskUpdate(status="done"))
    done = service.search(status="done")
    assert [t.id for t in done] == [t1.id]


def test_search_invalid_sort(service: TaskService):
    with pytest.raises(RepositoryError):
        service.search(sort_by=";drop table tasks;")

    with pytest.raises(RepositoryError):
        service.search(sort_dir="sideways")


def test_search_invalid_ranges(service: TaskService):
    with pytest.raises(ValidationError):
        service.search(priority_min=4, priority_max=2)

    with pytest.raises(ValidationError):
        service.search(due_after="2030-01-10", due_before="2030-01-01")


def test_db_enforces_title_non_empty(db):
    repo = TaskRepository(db)
    with pytest.raises(RepositoryError):
        repo.create_task(title="   ")
