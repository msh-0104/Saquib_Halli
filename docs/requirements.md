# Todo App Requirements

## 1) Enhancement candidates identified using AI Assistant (grouped by theme)

### Theme A — Requirements & backlog quality (AI-assisted)
**Enhancements**
- Standardize story format + acceptance criteria templates (BA assistant).
- Auto-suggest story splits + dependencies (to avoid oversized stories).
- Maintain a “Definition of Ready/Done” checklist for HITL reviews.
**Impact**: fewer ambiguous stories; faster execution; easier QA alignment.

### Theme B — Design governance (AI-assisted)
**Enhancements**
- Architecture + design review checklist with a repeatable template.
- ADR (Architecture Decision Record) capture for key decisions/risks.
**Impact**: repeatable reviews, traceability, reduced rework.

### Theme C — Implementation workflow (AI-assisted)
**Enhancements**
- Implementation plan generator (ordered tasks + blocked items).
- PR template + automated reviewer checklist (per Copilot doc).
**Impact**: predictable execution and consistent PR quality.

### Theme D — Testing automation (AI-assisted)
**Enhancements**
- Gherkin test case generation per story + edge cases.
- Playwright automation + test execution evidence linked back to Jira.
**Impact**: measurable verification, better regression safety.

### Theme E — Documentation sync (AI-assisted)
**Enhancements**
- Automatic generation/update of README + Confluence links.
- “Docs drift” checks (ensure docs reflect implemented behavior).
**Impact**: reduces stale docs; improves handover and demo readiness.

### Theme F — Deployment readiness (AI-assisted)
**Enhancements**
- Local deployment runbook + scripted build/package steps.
- Standard “smoke checklist” for local deployment validation.
**Impact**: repeatable demos; fewer last-minute deployment failures.

---

## 2) Prioritization (lightweight: Impact vs Effort) + sequencing
**Recommended sequence**
1. **Theme A (Backlog quality)**: highest leverage; enables everything else.
2. **Theme C (Implementation workflow)** + **Theme B (Design governance)**: ensures build is controlled and reviewable.
3. **Theme D (Testing automation)**: validates value delivered.
4. **Theme E (Documentation sync)** + **Theme F (Deployment readiness)**: polish + demo stability.

---

## 3) Jira backlog translation (Epics → Stories → Tasks)
Below are **Jira-ready artifacts** you can create under project `mm-learning-group-1`.  
(Fields like Assignee remain **TBD** to avoid assumptions.)

### EPIC A — AI-assisted Requirements & Backlog Quality
**Summary**: Establish AI-assisted standards to produce clear, testable requirements and Jira work items.  
**Labels**: `capstone`, `ai-sdlc`, `requirements`

**Story A1 — Standardize user story and acceptance criteria templates**
- **As a** BA/PO  
- **I want** a standard Jira story template (description + AC)  
- **So that** all work items are consistent and testable.
**Acceptance Criteria**
- A template exists for Story fields: Problem, Scope, Out of scope, AC, Dependencies, Risks.
- At least 3 existing stories are updated to the template format (or “TBD” placeholders where unknown).

**Tasks**
- Define story template (Description + AC structure)
- Apply template to initial backlog items
- Review with HITL checklist (DoR)

**Story A2 — AI assistant suggests story split and dependency ordering**
**Acceptance Criteria**
- Given a large story, assistant proposes at least 2 smaller stories with clear boundaries.
- Dependencies are explicitly listed in each derived story.

**Tasks**
- Define splitting rules (by workflow step / component / risk)
- Pilot on 1–2 sample items and refine guidance

---

### EPIC B — AI-assisted Architecture & Design Governance
**Summary**: Create repeatable architecture/design review artifacts with HITL checkpoints.  
**Labels**: `capstone`, `architecture`, `design-review`

**Story B1 — Architecture document + review checklist**
**Acceptance Criteria**
- Architecture doc includes components, data flow, and NFR considerations (TBD where unknown).
- A design review checklist is created and used in at least one review cycle.

**Tasks**
- Create architecture outline (Confluence link: TBD)
- Create design review checklist
- Capture review findings + decisions

**Story B2 — Capture ADRs for key decisions**
**Acceptance Criteria**
- At least 2 ADRs created (format: Context, Decision, Alternatives, Consequences).
- ADRs linked from relevant Jira items.

**Tasks**
- Create ADR template
- Create initial ADRs from current decisions (TBD)

---

### EPIC C — AI-assisted Implementation Planning & PR Quality Gate
**Summary**: Generate an implementation plan and enforce PR quality via a standard checklist.  
**Labels**: `capstone`, `implementation`, `pr-review`

**Story C1 — Implementation plan generated and dependency-ordered**
**Acceptance Criteria**
- Plan lists tasks in dependency order.
- Blocked tasks are explicitly marked with prerequisites.

**Tasks**
- Generate `impl-plan.md` (repo link: TBD)
- Review plan with HITL and adjust

**Story C2 — PR template with reviewer checklist (correctness/security/testing)**
**Acceptance Criteria**
- PR template contains: Summary, Changes Made, Test Evidence, Known Limitations, Reviewer Checklist.
- Checklist covers: Correctness, Security, Error Handling, Test Coverage, Clarity, DRY, Dependency Safety.

**Tasks**
- Add PR template file in repo (location TBD)
- Add reviewer checklist section
- Trial on a sample PR (or draft PR text)

---

### EPIC D — AI-assisted Testing (Gherkin + Playwright evidence)
**Summary**: Ensure stories are validated with Gherkin test cases and Playwright automation evidence.  
**Labels**: `capstone`, `testing`, `playwright`

**Story D1 — Generate Gherkin test cases per story**
**Acceptance Criteria**
- Each in-scope story has at least: 1 happy path + 2 edge cases in Gherkin.
- Tests reference acceptance criteria.

**Tasks**
- Produce Gherkin scenarios for initial stories
- Review scenarios with HITL

**Story D2 — Playwright automated tests + execution report**
**Acceptance Criteria**
- Automated tests exist for selected scenarios (scope: TBD).
- Execution evidence is stored (log/report) and linked in Jira.

**Tasks**
- Create Playwright test scaffolding (if not present)
- Implement tests for chosen scenarios
- Run tests and attach/link results

---

### EPIC E — AI-assisted Documentation Sync (README + Confluence alignment)
**Summary**: Keep README/Confluence artifacts aligned with implemented behavior and workflow outputs.  
**Labels**: `capstone`, `documentation`

**Story E1 — README updated with build/test/deploy steps**
**Acceptance Criteria**
- README contains: build steps, run steps, test steps, and troubleshooting.
- README references Jira epic/story keys and Confluence pages (TBD links allowed).

**Tasks**
- Draft README sections
- Validate steps on local environment (HITL)

**Story E2 — Docs drift checklist**
**Acceptance Criteria**
- A checklist exists to verify docs match current behavior after changes.
- Checklist is executed at least once and results recorded.

**Tasks**
- Create docs drift checklist
- Apply after one iteration

---

### EPIC F — Local Deployment Readiness (scripted)
**Summary**: Provide a repeatable local build and deployment workflow with smoke validation.  
**Labels**: `capstone`, `deployment`, `local-env`

**Story F1 — Build/package script created and committed**
**Acceptance Criteria**
- Script exists and can be run end-to-end locally (steps TBD).
- Output artifact is generated and location documented.

**Tasks**
- Create build script(s)
- Commit scripts to git
- Document usage in README

**Story F2 — Local deployment smoke checklist**
**Acceptance Criteria**
- Smoke checklist exists (startup, basic navigation/API health, key flows).
- Checklist executed once with recorded results.

**Tasks**
- Draft smoke checklist
- Execute smoke checks and store results

---

## Jira creation/update note
I can’t confirm creation/updating in Jira yet because the Jira API call did not return project metadata (the `/project` endpoint response came back as HTML, suggesting an auth/base-url issue in this environment).

If you want, paste **either**:
- your Jira base URL + confirmation that my API tool is authorized, **or**
- existing Jira issue keys already created in `mm-learning-group-1`

…and I will **rewrite/update** those tickets (clear scope, add AC, add subtasks, link dependencies) or produce a **copy/paste-ready** Jira import format.reflect the latest successful action.
- Multiple tabs/windows and conflict resolution are outside MVP scope. Database locking or transient errors must still be handled gracefully without data corruption.

## Nice-to-have / future scope

- Undo for deletes or edits; soft deletion and later purge.
- Retry controls and offline write queues.
- Persisting search/filter state across app restarts.
- Sorting by creation date, modification date, or completion state.
- Drag-and-drop ordering and keyboard shortcuts.
- Multi-window conflict detection, multi-user access, and cross-device synchronization.
- Schema migration tooling and expanded diagnostic logging.

## Manual QA cases

1. Create a valid todo; verify it appears, has an ID and timestamps, and remains after restart.
2. Create titles with leading/trailing whitespace; verify saved whitespace is trimmed.
3. Submit an empty or whitespace-only title; verify save is blocked with an explanation.
4. Submit a title longer than 255 characters; verify save is blocked with an explanation.
5. Edit a todo; verify its ID remains the same, its title changes, and `updated_at` changes.
6. Cancel an edit; verify unsaved changes are discarded.
7. Attempt an invalid edit; verify the saved title remains intact.
8. Toggle completion; verify the state and `updated_at` persist after reload.
9. Start a deletion and cancel; verify the todo remains. Confirm deletion; verify only that todo is removed.
10. Simulate database read/write failures; verify a clear error, no crash, and no false success or data corruption.
11. Search with different capitalization; verify matching is case-insensitive and results update as the query changes.
12. Test All, Active, and Completed filters, then combine each with a search query; verify AND behavior.
13. Search for a non-matching title; verify the “No results” state. Clear search/filter independently and verify the expected results return.
14. Delete the only visible result under a filter/search; verify the list transitions to the correct empty state.
15. Toggle and immediately edit a todo; verify the latest successful state appears in both the UI and persisted data.
16. Delete one todo and then edit or toggle another; verify the operation targets the correct stable ID.
17. Load a few thousand todos; verify loading completes in approximately 1–2 seconds on a typical developer machine.
