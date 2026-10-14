# System Architecture: Automated Documentation Sync Agent

## 1. High-Level Architecture Overview
The Automated Documentation Sync Agent is designed as an event-driven, non-blocking pipeline integrated into GitHub Actions. It listens to merge events on the `main` branch, analyzes code diffs, maps changes to documentation files, generates updated markdown content, and opens a pull request for human review.

```
[ Git Push / Merge to main ]
│
▼
[ GitHub Actions Workflow (Trigger) ]
│
▼
[ 1. Diff Parser & Analyzer ] ──(Extract public APIs/modules)
│
▼
[ 2. Doc Mapper & Heuristics ] ──(Match code paths to /docs/*.md)
│
▼
[ 3. AI / Content Generator ] ──(Draft updated Markdown)
│
▼
[ 4. PR Automation & Linting ] ──(Markdownlint / Linkcheck)
│
▼
[ GitHub Pull Request Created (Draft) ]
```

---

## 2. Key Components & Responsibilities

| Component | Responsibility | Technology / Tooling |
| :--- | :--- | :--- |
| **Workflow Trigger** | Listens for `push` events on `main` branch and initiates the agent pipeline. | GitHub Actions (`on: push: branches: [main]`) |
| **Diff Parser** | Extracts modified source files, public function signatures, and exported classes from git diffs. | Python / GitPython / Tree-sitter |
| **Documentation Mapper** | Applies heuristics to map modified source files to corresponding documentation markdown files in `/docs`. | Custom Mapping Rules & Config (`docs-map.json`) |
| **Content Generator** | Synthesizes diff updates into clear, natural language documentation additions or revisions. | LLM Integration / OpenAI API via GitHub Copilot / Actions secret |
| **Linter & Validator** | Runs automated checks to ensure markdown validity, correct link references, and zero exposed secrets. | `markdownlint`, `lychee` (link checker), Trufflehog |
| **PR Automation** | Automatically creates or updates an existing draft Pull Request with the generated documentation changes. | `peter-evans/create-pull-request` GitHub Action |

---

## 3. Data Flow
1. **Event Capture:** A PR is merged into `main`, triggering the GitHub Actions workflow.
2. **Extraction:** The workflow checks out the repository, gets the commit diff (`git diff HEAD~1`), and feeds it into the Diff Parser.
3. **Mapping:** The Mapper checks modified files against configured documentation targets (e.g., `src/api/` → `docs/api-reference.md`).
4. **Generation:** The Content Generator drafts the updated markdown section.
5. **Validation:** Automated linters check the generated markdown for syntax errors and broken links.
6. **PR Creation:** The PR Automation component opens or updates a draft Pull Request on the repository using a dedicated GitHub App token.

---

Next Phase: Step 2 — Architecture Design
Now that our functional and non-functional requirements are locked in, let's design the high-level architecture for the Automated Documentation Sync Agent.

Here is a proposed architecture draft based on your requirements. You can review this, save it as docs/architecture.md, and commit it to your branch!
