# Implementation Plan: Automated Documentation Sync Agent

This document outlines the phased, dependency-ordered task list for building and deploying the Automated Documentation Sync Agent based on `docs/requirements.md` and `docs/architecture.md`.

---

## **Phase 1: Project Setup & Configuration**
* **Task 1.1:** Initialize repository directory structure (`/src`, `/docs`, `/.github/workflows`, `/tests`). *(Prerequisite: None)*
* **Task 1.2:** Create configuration file `docs-map.json` mapping source code directories to target documentation markdown files. *(Prerequisite: Task 1.1)*
* **Task 1.3:** Setup dependencies (`requirements.txt` or `package.json`) including GitPython, PyGithub/Octokit, and linting tools. *(Prerequisite: Task 1.1)*

## **Phase 2: Core Agent Logic (Parser & Mapper)**
* **Task 2.1:** Implement **Diff Parser Module** (`src/parser.py`) to extract modified files and public API signatures from `git diff HEAD~1`. *(Prerequisite: Task 1.3)*
* **Task 2.2:** Implement **Documentation Mapper** (`src/mapper.py`) using `docs-map.json` to associate code changes with corresponding `.md` files. *(Prerequisite: Task 2.1)*
* **Task 2.3:** Implement **Secret Scanner Filter** to sanitize diff inputs and block sensitive token transmission. *(Prerequisite: Task 2.1)*

## **Phase 3: Content Generation & PR Automation**
* **Task 3.1:** Implement **Content Generator Module** (`src/generator.py`) to interact with the LLM API (GitHub Copilot / OpenAI) and draft concise markdown updates. *(Prerequisite: Task 2.2)*
* **Task 3.2:** Implement **PR Automation Script** (`src/pr_manager.py`) to check for existing open sync PRs (idempotency) and create/update draft PRs. *(Prerequisite: Task 3.1)*

## **Phase 4: CI/CD Pipeline & Quality Gates**
* **Task 4.1:** Write GitHub Actions workflow (`.github/workflows/docs-sync.yml`) triggered on merge to `main`. *(Prerequisite: Tasks 1.2, 3.2)*
* **Task 4.2:** Integrate quality gates (`markdownlint`, link checker `lychee`) into the workflow steps. *(Prerequisite: Task 4.1)*

## **Phase 5: Testing & Verification**
* **Task 5.1:** Write unit tests for parser, mapper, and generator modules (`tests/`). *(Prerequisite: Task 3.1)*
* **Task 5.2:** Perform integration test run on a test branch to verify end-to-end event triggering, diff processing, and draft PR creation. *(Prerequisite: Tasks 4.2, 5.1)*

---

## **Blocked / Prerequisite Dependencies Summary**
- **Phase 3** depends entirely on successful completion of **Phase 2** (Parser & Mapper).
- **Phase 4 (CI/CD)** cannot be finalized until core python scripts are in place (**Phase 3**).
- **Phase 5 (Testing)** requires core logic and CI workflow to be fully written.

How to proceed:
You can commit this implementation plan as docs/impl-plan.md to your repository.
