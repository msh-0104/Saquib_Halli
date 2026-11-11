"# Todo Backend Implementation" 
# AI-Assistant–Driven SDLC Capstone Project (Brownfield Todo App)
**Project Scope:** `mm-learning-group-1`

## Overview
This repository contains the end-to-end implementation of an AI-assistant–driven Software Development Life Cycle (SDLC) pipeline. We analyzed a brownfield in-memory Todo application, identified key feature gaps, designed an incremental architecture, and executed improvements using CodeMie, Jira, Confluence, Claude Code, Pytest, and local SQLite persistence.

## Features Added
1. **Persistent Storage:** Local SQLite database integration (`todo.db`) replacing temporary in-memory storage.
2. **Edit & Delete Tasks:** Full CRUD support allowing updates to task titles/status and immediate deletion.
3. **Filter & Search:** Multi-condition search filtering combining status tabs (`pending`/`done`) and keyword substring matching.

## Project Structure
- `src/database.py` — SQLite connection manager and DDL schema setup.
- `src/repository.py` — SqliteTaskRepository handling parameterized CRUD and search queries.
- `src/service.py` — TaskService handling validation and custom domain exceptions.
- `tests/test_todo.py` — Comprehensive unit test suite (`pytest`).
- `docs/` — Requirements, architecture, implementation plans, and review checklists.

## Setup & Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/msh-0104/Saquib_Halli.git
   cd Saquib_Halli
