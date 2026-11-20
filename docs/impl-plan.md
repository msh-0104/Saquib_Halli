```md
# Brownfield Todo App Enhancements — Implementation Plan (docs/impl-plan.md)

Repo: **msh-0104/Saquib_Halli**  
Jira Epic: **MM-1 — Brownfield Todo App Enhancements**  
Process Stories: **MM-5..MM-14** (Subtasks: **MM-15..MM-20**)  
Top 5 Enhancements: SQLite persistence, CRUD edit/delete, Search/Filter, Priority/Sorting, Due Dates/Urgency Views

> IMPORTANT: `docs/impl-plan.md` previously contained an unrelated “Automated Documentation Sync Agent” plan.
> This file is now repurposed to document the Todo App enhancement plan.

---

## 0) Purpose
Provide a dependency-ordered, execution-ready plan to deliver and validate the **Top 5 shortlisted enhancements** for the Brownfield Todo App.  
This document is the **source of truth** and should be linked from Jira **MM-8** and Epic **MM-1**.

---

## 1) Scope

### 1.1 In scope (Top 5 enhancements)
1. **Persistent Local SQLite Database Storage** (Jira: **MM-2**)
2. **Task Edit & Delete CRUD Operations** (Jira: **MM-3**)
3. **Multi-Condition Search & Status Filtering** (Jira: **MM-4**)
4. **Task Priority Levels & Sorting** (Jira: **TBD** – create story under MM-1)
5. **Due Dates & Urgency Views** (Jira: **TBD** – create story under MM-1)

### 1.2 Out of scope (for this release)
- Cloud sync / remote DB / multi-device sync
- Multi-user auth/roles
- Major UI redesign beyond what is required for these features
- Analytics/telemetry (unless later requested)

### 1.3 Success criteria (release-level)
- Tasks persist via SQLite with **stable IDs**; app reloads correctly after restart.
- Users can **edit** and **delete** tasks; changes persist correctly.
- Users can **search** and **filter** using multiple conditions (minimum: text + status).
- Users can set **priority** and sort; ordering is predictable and stable.
- Users can set **due dates** and view by urgency (Overdue / Due Today / Upcoming / None).
- For each enhancement: **AC → Gherkin → Playwright** traceability exists and evidence is linked.
- Local runbook exists and smoke validation passes.

---

## 2) Jira mapping (Top 5 ↔ stories) + dependency order

| # | Enhancement | Jira Key | Depends on | Notes |
|---:|---|---|---|---|
| 1 | SQLite persistence | MM-2 | — | Foundation: persistence + stable IDs |
| 2 | Edit/Delete CRUD | MM-3 | MM-2 | Must use stable IDs for correctness |
| 3 | Priority + Sorting | TBD | MM-2 | Adds data attributes for filtering/sorting |
| 4 | Due Dates + Urgency | TBD | MM-2 | Adds due_date + new views |
| 5 | Search + Status Filtering | MM-4 | MM-2, (TBD Priority), (TBD Due Dates) | Prefer DB query; AND semantics |

---

## 3) Governance (MM-5..MM-14)

### 3.1 Milestones / gates
| Milestone | Jira | Exit criteria |
|---|---|---|
| M1 Candidate list complete | MM-5 | Candidate list + themes/value + HITL notes captured |
| M2 Prioritization locked (Top 5) | MM-6 | Impact/Effort + dependency order + risks |
| M3 Requirements standardized | MM-7 | Template created + Top 5 stories updated (or ≥3 minimum) |
| M4 Plan baseline | MM-8 | This file updated and linked in Jira |
| M5 Design governance ready | MM-9 | Design checklist used; decisions/risks recorded |
| M6 PR governance ready | MM-10 | PR template + review checklist used on ≥1 PR |
| M7 Test design ready | MM-11 | Gherkin scenarios for Top 5, traceable to AC |
| M8 Automation evidence ready | MM-12 | Playwright executed; report/log linked; failures tracked |
| M9 Docs + runbook complete | MM-13/MM-14 | Confluence links verified + local runbook smoke validated |

### 3.2 Cadence
- **2×/week execution sync (15–20 min):** blockers/dependencies/next actions
- **Weekly milestone review (30 min):** gate completion + scope decisions

### 3.3 Weekly status template
- RAG:
- Done (Jira keys + PR/test/doc links):
- In progress:
- Next:
- Risks/Blockers:
- Decisions needed:

---

## 4) RAID log (starter)

| ID | Type | Description | Impact | Likelihood | Mitigation | Owner |
|---|---|---:|---:|---:|---|---|
| R1 | Risk | Priority & Due Date stories not created in Jira | Med | Med | Create both stories; link to MM-1; update keys here | PO/Lead |
| R2 | Risk | Local build/run instability blocks Playwright | High | Med | Complete MM-14 early; define smoke steps; pin versions | Dev/DevOps |
| R3 | Risk | Flaky E2E tests | Med | Med | Stable selectors; deterministic test data; retries policy | QA |
| R4 | Risk | SQLite migration/data regression | High | Med | Migration strategy + reset plan; repo/unit tests | Dev |
| R5 | Risk | Missing evidence links in Jira | Low | High | Add “Evidence links” per enhancement; final link audit | Tech Lead |

---

## 5) Cross-cutting standards (must apply)

### 5.1 PR / review gate (MM-10)
- Use PR template
- Reviewer checklist must cover: correctness, error handling, test evidence, maintainability, security (as applicable)

### 5.2 Design gate (MM-9)
- Use design review checklist
- Record decisions and risks (link to Confluence from Jira MM-9/MM-13)

### 5.3 Testing gate (MM-11/MM-12)
- Maintain traceability: **Story AC → Gherkin → Playwright**
- Minimum per enhancement: **1 happy path + 2 edge cases** (or mark TBD with reason)

---

## 6) Per-enhancement execution plans (Dev / QA / Docs)

> For each enhancement below, fill “Evidence links” as you complete PRs/tests/docs.

---

### 6.1 Enhancement 1 — Persistent Local SQLite Database Storage (MM-2)

**Goal:** Persist todos locally using SQLite with stable IDs and consistent read/write behavior.

**Dev tasks**
- [ ] Review current storage mechanism and data model
- [ ] Define schema (tables/columns/constraints)
- [ ] Implement repository/data-access layer
- [ ] Implement initialization + schema versioning/migration
- [ ] Ensure stable ID generation and mapping to UI model
- [ ] Wire read-on-start and write-on-mutation flows
- [ ] Error handling (open/write failure) + logging strategy

**QA tasks**
- [ ] Gherkin committed
- [ ] Playwright: add task persists after restart; list reload correctness
- [ ] Edge testing approach for DB failures documented (simulate or unit-test repository)

**Gherkin placeholders**
| ID | Scenario | Type |
|---|---|---|
| DB-HP-01 | Add a task and verify it persists after app restart | Happy |
| DB-EC-01 | Add multiple tasks; verify stable IDs and no duplicates after reload | Edge |
| DB-EC-02 | Failed write shows safe error state | Edge |

**Rollout / rollback**
- Rollout: enable SQLite repo; smoke validate persistence
- Rollback: revert PR; document any data loss implications

**Evidence links**
- PR(s):
- Playwright report/log:
- Design/decision notes:
- Confluence:

---

### 6.2 Enhancement 2 — Task Edit & Delete CRUD Operations (MM-3)

**Goal:** Allow users to edit and delete tasks with correct UX and persistence.

**Dev tasks**
- [ ] Decide edit UX and validations
- [ ] Implement edit operation by stable ID
- [ ] Implement delete (confirm UX if needed) by stable ID
- [ ] Ensure UI refresh + empty state behavior
- [ ] Ensure persistence correctness (depends on MM-2)

**QA tasks**
- [ ] Playwright: edit persists after restart
- [ ] Playwright: delete persists after restart
- [ ] Edge: invalid edit; delete last item; delete under filters (if enabled)

**Gherkin placeholders**
| ID | Scenario | Type |
|---|---|---|
| CRUD-HP-01 | Edit an existing task and verify changes persist | Happy |
| CRUD-HP-02 | Delete a task and verify it is removed | Happy |
| CRUD-EC-01 | Invalid edits are rejected and not persisted | Edge |
| CRUD-EC-02 | Delete then restart; task stays deleted | Edge |

**Rollout / rollback**
- Rollout: ship UI + persistence; run smoke + e2e
- Rollback: revert PR(s)

**Evidence links**
- PR(s):
- Playwright report/log:
- Design/decision notes:
- Confluence:

---

### 6.3 Enhancement 3 — Task Priority Levels & Sorting (Jira: TBD)

**Goal:** Add priority levels (e.g., Low/Medium/High) and sorting by priority.

**Dev tasks**
- [ ] Define priority values + default
- [ ] Add `priority` to schema + migration
- [ ] Update create/edit UX to set priority
- [ ] Implement sorting + stable tie-breaker (e.g., created_at or id)
- [ ] Confirm interaction with status/urgency views

**QA tasks**
- [ ] Playwright: priority persists after restart
- [ ] Playwright: sorting correct and stable
- [ ] Edge: same priority retains stable order

**Gherkin placeholders**
| ID | Scenario | Type |
|---|---|---|
| PRI-HP-01 | Set priority and verify it persists | Happy |
| PRI-HP-02 | Sort tasks by priority and verify order | Happy |
| PRI-EC-01 | Same priority retains stable order | Edge |

**Evidence links**
- PR(s):
- Playwright report/log:
- Design/decision notes:
- Confluence:

---

### 6.4 Enhancement 4 — Due Dates & Urgency Views (Jira: TBD)

**Goal:** Add due dates and urgency-based views (Overdue / Due Today / Upcoming / None).

**Dev tasks**
- [ ] Decide date-only vs datetime + timezone handling
- [ ] Add `due_date` to schema + migration
- [ ] Update create/edit UX to set/clear due date
- [ ] Implement urgency categorization rules
- [ ] Implement urgency view(s)

**QA tasks**
- [ ] Playwright: due date persists after restart
- [ ] Validate urgency categorization using controlled dates (mock clock if possible)
- [ ] Edge: timezone boundary; clearing due date; completion interactions

**Gherkin placeholders**
| ID | Scenario | Type |
|---|---|---|
| DUE-HP-01 | Assign due date and verify it persists | Happy |
| DUE-HP-02 | Overdue tasks appear in overdue view | Happy |
| DUE-EC-01 | Clear due date and verify view updates | Edge |
| DUE-EC-02 | Timezone boundary does not misclassify “Due Today” | Edge |

**Evidence links**
- PR(s):
- Playwright report/log:
- Design/decision notes:
- Confluence:

---

### 6.5 Enhancement 5 — Multi-Condition Search & Status Filtering (MM-4)

**Goal:** Multi-condition search/filter (min: text + status; optionally include priority/due-date).

**Dev tasks**
- [ ] Define filter dimensions + UX controls
- [ ] Implement combined filters with AND semantics
- [ ] Implement query logic (prefer DB query)
- [ ] Define empty-state and clear/reset behavior
- [ ] Confirm interaction with sorting/urgency views

**QA tasks**
- [ ] Playwright: search works
- [ ] Playwright: status filter works
- [ ] Playwright: combined search + status works
- [ ] Edge: empty results; special chars; case sensitivity

**Gherkin placeholders**
| ID | Scenario | Type |
|---|---|---|
| FIL-HP-01 | Search by text returns matching tasks | Happy |
| FIL-HP-02 | Filter by status returns matching tasks | Happy |
| FIL-EC-01 | Combine search + status filter uses AND behavior | Edge |
| FIL-EC-02 | Clearing filters restores default list | Edge |

**Evidence links**
- PR(s):
- Playwright report/log:
- Design/decision notes:
- Confluence:

---

## 7) Definition of Done (cross-cutting)
- [ ] MM-9 design checklist used; decisions recorded
- [ ] MM-10 PR template + review checklist used
- [ ] MM-11 Gherkin committed and linked
- [ ] MM-12 Playwright executed; evidence linked; failures tracked
- [ ] MM-13 Confluence pages created and linked from Jira
- [ ] MM-14 build scripts + local runbook + smoke run complete
```
