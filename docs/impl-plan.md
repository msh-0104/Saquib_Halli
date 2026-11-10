# Implementation Plan: Brownfield Todo App Enhancements

This document outlines the phased implementation plan for adding our 3 core user stories to the brownfield Todo application under project `mm-learning-group-1`.

## 1. Scope & Features to Build
1. **Persistent Storage:** Replace in-memory list storage with a local SQLite database so tasks survive application restarts.
2. **Edit and Delete Tasks:** Add unique task IDs and repository methods to update task text/status or remove tasks entirely.
3. **Filter and Search Tasks:** Add multi-condition querying (status filtering like 'pending'/'done' plus keyword search matching titles/descriptions).

---

## 2. Phased Task Breakdown & Dependencies

### **Phase 1: Database & Persistence Layer (Prerequisite)**
- **Task 1.1:** Create `src/database.py` to manage SQLite connection, WAL mode, foreign keys, and schema initialization (`tasks` table).
- **Task 1.2:** Implement unit tests for database connection and schema setup.

### **Phase 2: Repository & Service Layers (Core Logic)**
- **Task 2.1:** Create `src/repository.py` (`SqliteTaskRepository`) implementing secure parameterized CRUD operations (`create_task`, `get_task`, `update_task`, `delete_task`, `list_tasks`).
- **Task 2.2:** Create `src/service.py` (`TaskService`) to handle input validation (non-empty titles, valid priorities, valid dates) and custom domain exceptions (`ValidationError`, `NotFoundError`).

### **Phase 3: Testing & Verification (Quality Gate)**
- **Task 3.1:** Create `tests/test_todo.py` covering happy paths, edge cases (empty titles, invalid sort parameters), and search filtering.
- **Task 3.2:** Execute pytest suite (`python -m pytest tests/test_todo.py -v`) and verify 100% test pass rate.
