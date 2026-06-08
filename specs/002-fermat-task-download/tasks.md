# Tasks: Clear OMJ Data and Download FerMat Task PDFs

**Input**: Design documents from `/specs/002-fermat-task-download/`

**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/cli-contract.md ✓

**Tests**: Not requested — no automated test tasks generated. Verification is manual (shell checks + dry-run).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- All scripts are at repository root; no new files or packages needed

---

## Phase 1: Setup

**Purpose**: Confirm current state of scripts before making changes.

- [X] T001 Read download_fermat.py to identify current BASE_URL, generate_expected_urls(), discover_pdf_links(), and run() structure
- [X] T002 [P] Read create_tasks.py to locate TASK_COUNTS dict and etap3 references
- [X] T003 [P] Read populate_metadata.py to locate PROMPT_TEMPLATE and OMJ/etap3 references

**Checkpoint**: Current script state understood — implementation can begin.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: No shared infrastructure is needed for this feature. All user stories operate on independent files and shell operations.

**⚠️ SKIP TO PHASE 3**: US1 must complete before US2 (empty `tasks/` required), but there is no shared code foundation to establish first.

---

## Phase 3: User Story 1 — Clear OMJ Task Data (Priority: P1) 🎯 MVP

**Goal**: Remove all OMJ competition artifacts from three locations so no OMJ data is served by the application.

**Independent Test**:
```bash
find tasks/ -type f | wc -l          # → 0
find data/tasks/ -type f | wc -l     # → 0
ls data/task_prerequisites_analysis.md 2>&1  # → No such file or directory
```

### Implementation for User Story 1

- [X] T004 [US1] Delete all year subdirectories inside tasks/ with `rm -rf tasks/*/` (keeps the tasks/ directory itself, satisfies FR-001)
- [X] T005 [US1] Delete all year subdirectories inside data/tasks/ with `rm -rf data/tasks/*/` (keeps the data/tasks/ directory itself, satisfies FR-001b)
- [X] T006 [US1] Delete data/task_prerequisites_analysis.md with `rm -f data/task_prerequisites_analysis.md` (satisfies FR-001c)
- [X] T007 [US1] Verify SC-001: run the three find/ls checks above and confirm all return zero files / no such file

**Checkpoint**: SC-001 satisfied — tasks/ and data/tasks/ are empty, analysis doc is gone. US2 can now begin.

---

## Phase 4: User Story 2 — Download FerMat Task PDFs (Priority: P2)

**Goal**: Update download_fermat.py so it targets the live FerMat website with correct URL patterns, then run it to populate tasks/.

**Independent Test**:
```bash
python download_fermat.py --dry-run            # Lists ~20 candidates, writes zero files
python download_fermat.py --year 2024 --dry-run  # Lists exactly 3 entries
python download_fermat.py --year 2024          # Creates tasks/2024/etap1/tasks.pdf, solutions.pdf, etap2/tasks.pdf
```

### Implementation for User Story 2

- [X] T008 [US2] Replace BASE_URL with `"https://sp221.edu.pl/files/171/"` and add `LISTING_URL = "https://sp221.edu.pl/zadania-z-poprzednich-edycji,171,pl"` in download_fermat.py
- [X] T009 [US2] Replace generate_expected_urls() in download_fermat.py with a deterministic builder: years 2017–2023 → single `fermatYYYY.pdf` → `{year}/etap1/tasks.pdf`; years 2024–2025 → `fermatYYYY-e1.pdf` + `fermatYYYY-e2.pdf` + `fermatYYYY-e1r.pdf`; year 2026 → `fermat2026-e1.pdf` (split) and `fermat2026-e2.pdf` (split, best effort)
- [X] T010 [US2] Remove discover_pdf_links() HTML scraping function and probe_url() slow-probing loop from download_fermat.py (no longer needed — known URL list replaces them)
- [X] T011 [US2] Update run() in download_fermat.py to use the single path: generate candidates → apply --year filter → deduplicate by (year, etap, file_type) → download each (remove the old two-step scrape-then-probe logic)
- [X] T012 [US2] Verify CLI stdout matches cli-contract.md: header block with Base URL / Output / optional Mode and Year lines; per-file lines with [+]/[=]/[?]/[!] icons; summary block with Downloaded/Skipped/Errors counts
- [X] T013 [US2] Run `python download_fermat.py --dry-run` and confirm it lists ~20 candidate PDFs and writes zero files to tasks/ (SC-005)
- [X] T014 [US2] Run `python download_fermat.py --year 2024 --dry-run` and confirm exactly 3 entries: etap1/tasks.pdf, etap1/solutions.pdf, etap2/tasks.pdf
- [X] T015 [US2] Run `python download_fermat.py` (full download) and verify expected files appear in tasks/ with `find tasks/ -name "*.pdf" | sort`
- [X] T016 [US2] Re-run `python download_fermat.py` immediately after T015 and verify zero downloaded, zero errors (idempotency — SC-004)

**Checkpoint**: SC-002, SC-003, SC-004, SC-005 satisfied — tasks/ populated with FerMat PDFs.

---

## Phase 5: User Story 4 — Populate FerMat Task JSON Files (Priority: P2)

**Goal**: Fix create_tasks.py and populate_metadata.py for FerMat, then run the full pipeline to generate data/tasks/ JSON files for all downloaded editions.

**Independent Test**: After running pipeline for 2024/etap1:
```bash
ls data/tasks/2024/etap1/task_{1..10}.json  # All 10 exist
python3 -c "
import json, pathlib
for f in sorted(pathlib.Path('data/tasks/2024/etap1').glob('task_*.json')):
    t = json.loads(f.read_text())
    ok = t.get('content','') not in ('','Treść zadania do uzupełnienia.') \
         and len(t.get('hints',[])) == 4 and t.get('difficulty')
    print(f.name, '✓' if ok else '✗ INCOMPLETE')
"
```

### Implementation for User Story 4

- [X] T017 [P] [US4] Update TASK_COUNTS in create_tasks.py: set `"etap1": 10, "etap2": 5`, remove `"etap3"` key and any etap3 references (actual etap2 PDF count is 5, confirmed from live PDFs)
- [X] T018 [P] [US4] Update PROMPT_TEMPLATE in populate_metadata.py: replace "z Olimpiady Matematycznej Juniorów" → "z Konkursu Matematycznego FerMat", replace age range to "klasy 4-6, wiek 9-12 lat", remove etap3 difficulty guidance line (satisfies FR-011)
- [X] T019 [US4] Verify script fixes: `grep -n "OMJ\|etap3" populate_metadata.py` returns no matches inside PROMPT_TEMPLATE
- [X] T020 [P] [US4] Run `python create_tasks.py 2024 etap1` and `python create_tasks.py 2024 etap2` to create stub JSON files in data/tasks/2024/
- [X] T021 [P] [US4] Run `python create_tasks.py 2025 etap1` and `python create_tasks.py 2025 etap2` to create stub JSON files in data/tasks/2025/
- [X] T022 [US4] Run fix_latex_content.py for all editions (2017–2025); all 94 tasks have content populated
- [X] T023 [US4] Run populate_metadata.py year by year (2017–2025); all 94 tasks have difficulty, hints, skills
- [X] T024 [US4] Run generate_task_index.py then populate_prerequisites.py year by year (2017–2025)
- [X] T025 [US4] Run create/fix/metadata/prerequisites pipeline for combined-PDF editions 2017–2023 (etap1 only, 9 tasks each — confirmed from live PDFs)
- [X] T026 [US4] Verify SC-006: all 2024/etap1 task JSONs have non-placeholder content, exactly 4 hints, non-zero difficulty (10/10 ✓)
- [ ] T027 [US4] Verify SC-007: start Docker stack (`./start.sh`) and run `curl -s http://localhost:8000/api/years/2024/etap1 | python3 -m json.tool | head -20` to confirm tasks are served

**Checkpoint**: SC-006 satisfied — FerMat task JSONs populated. SC-007 requires Docker stack.

---

## Phase 6: User Story 3 — Verify Downloaded Content (Priority: P3)

**Goal**: Confirm that the downloaded PDFs match expected editions and are valid, non-empty files.

**Independent Test**: `ls -lh tasks/2024/etap1/tasks.pdf` shows a non-zero file size.

### Implementation for User Story 3

- [X] T028 [P] [US3] Verify tasks/ layout: 11 tasks.pdf files present — 7 for 2017–2023 etap1, 2 for 2024 (etap1+2), 2 for 2025 (etap1+2) ✓
- [X] T029 [P] [US3] Verify solutions.pdf scope: exactly tasks/2024/etap1/solutions.pdf and tasks/2025/etap1/solutions.pdf ✓
- [X] T030 [US3] Verify all downloaded PDFs are non-empty: zero-byte check passed; sample `file` command returns "PDF document" ✓

**Checkpoint**: SC-002 fully confirmed — PDFs are valid, non-empty, correctly placed.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final checks across all stories.

- [X] T031 [P] Run `python download_fermat.py --dry-run` one final time — clean output, no legacy code ✓
- [X] T032 Run `grep -n "discover_pdf_links\|probe_url\|OMJ\|omj" download_fermat.py` — no legacy references ✓
- [X] T033 [P] Run `grep -n "OMJ\|etap3" create_tasks.py populate_metadata.py` — clean ✓

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately; run T001/T002/T003 in parallel
- **Phase 3 (US1)**: Depends on Setup — US1 clearing MUST complete before US2 downloads
- **Phase 4 (US2)**: Depends on US1 — tasks/ must be empty before downloading FerMat PDFs
- **Phase 5 (US4)**: Depends on US2 — PDFs must exist before JSON pipeline runs; T017/T018 (script fixes) can run in parallel with US2 work
- **Phase 6 (US3)**: Depends on US2 — PDFs must exist; can run concurrently with US4
- **Polish (Phase 7)**: Depends on all user stories complete

### User Story Dependencies

- **US1 (P1)**: Can start immediately after Setup — no story dependencies
- **US2 (P2)**: Depends on US1 (tasks/ must be empty)
- **US4 (P2)**: Depends on US2 (PDFs must exist); script fixes T017/T018 can start during US2
- **US3 (P3)**: Depends on US2; can run in parallel with US4

### Within Each User Story

- Script reads (T001–T003) must precede edits (T008–T011, T017–T018)
- Clearing (T004–T006) must complete and be verified (T007) before downloading
- Script edits (T008–T011) before dry-run validation (T013–T014) before live download (T015)
- create_tasks.py stubs (T020–T021) before fix_latex (T022) before populate_metadata (T023) before prerequisites (T024)

### Parallel Opportunities

- T001, T002, T003 (Phase 1 reads) — parallel
- T004, T005, T006 (clearing) — parallel (different locations)
- T017, T018 (script fixes in different files) — parallel
- T020, T021 (create_tasks for 2024 and 2025) — parallel
- T028, T029 (verification checks) — parallel

---

## Parallel Example: User Story 4

```bash
# Run script fixes in parallel (different files):
Task T017: Update TASK_COUNTS in create_tasks.py
Task T018: Update PROMPT_TEMPLATE in populate_metadata.py

# Run stub creation in parallel (different year directories):
Task T020: create_tasks.py for 2024/etap1 and 2024/etap2
Task T021: create_tasks.py for 2025/etap1 and 2025/etap2
```

---

## Implementation Strategy

### MVP First (User Story 1 only — clearing)

1. Complete Phase 1: Setup (read scripts)
2. Complete Phase 3: US1 — clear OMJ data, verify with SC-001 checks
3. **STOP and VALIDATE**: confirm tasks/ and data/tasks/ are empty
4. Ready for US2 download

### Incremental Delivery

1. Setup → US1 clearing → verify clean state (Phase 1+3)
2. US2 script update → dry-run → live download → idempotency check (Phase 4)
3. US4 script fixes → pipeline for 2024/2025 → verify JSONs → pipeline for 2017–2023 (Phase 5)
4. US3 file validity checks (Phase 6)
5. Polish (Phase 7)

### Single-Developer Order (recommended)

T001→T002→T003 → T004→T005→T006→T007 → T008→T009→T010→T011→T012→T013→T014→T015→T016 → T017+T018(parallel)→T019→T020+T021(parallel)→T022→T023→T024→T025→T026→T027 → T028+T029+T030 → T031+T032+T033

---

## Notes

- All scripts run outside Docker (from repository root), Python 3.11+ required
- `fix_latex_content.py` and `populate_metadata.py` require `claude` CLI in PATH with a valid session
- Combined-PDF editions 2017–2023: only etap1 JSONs are created (no separate etap2 PDF exists — deferred)
- Combined-PDF years have 9 tasks (not 10) — confirmed from live PDFs; task_10 stubs removed
- FerMat etap2 has 5 tasks (not 10) — confirmed from live PDFs; scoring.yml updated accordingly
- `data/skills.json` is preserved — it is NOT OMJ-specific (generic math skills taxonomy for primary school)
- Exit code 1 from download_fermat.py means at least one HTTP error occurred; review `[!]` lines in output
- Year 2026: script generates split-etap candidates; if they 404 (not yet published), errors are expected and benign
- `triangle_inequality` skill added to data/skills.json (suggested by populate_metadata.py for 2025/etap1/task_7)
- `populate_prerequisites.py` OMJ reference fixed to FerMat
