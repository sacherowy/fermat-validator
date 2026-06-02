---
description: "Task list for FerMat Validator domain migration from OMJ"
---

# Tasks: FerMat Validator — Domain Migration from OMJ

**Input**: Design documents from `specs/001-fermat-validator-app/`

**Prerequisites**: plan.md ✅ spec.md ✅ research.md ✅ data-model.md ✅ contracts/ ✅

**Tests**: Not requested — no test tasks generated.

**Organization**: Tasks grouped by user story to enable independent implementation
and testing. Foundation phase (scoring infrastructure) is the sole blocking prerequisite.

---

## Phase 1: Setup

**Purpose**: Create the new scoring configuration file that the rest of the migration depends on.

- [X] T001 Create `config/` directory and initial `config/scoring.yml` with FerMat default scale (tasks 1–5: 2 pts, tasks 6–10: 4 pts for both etap1 and etap2) — see `specs/001-fermat-validator-app/contracts/scoring-config.md`

**Checkpoint**: `config/scoring.yml` present and valid YAML — Phase 2 can begin.

---

## Phase 2: Foundational — Scoring Infrastructure

**Purpose**: Replace OMJ hardcoded scoring logic with YAML-driven FerMat scoring.
MUST be complete before User Story 2 (submission flow) can work correctly.

**⚠️ CRITICAL**: User Story 2 submission flow cannot function until this phase is complete.

- [X] T002 Create `app/ai/scoring_config.py` — YAML loader with `get_max_points(etap: str, task_number: int) -> int` and startup validation (both etap1/etap2 must exist; missing task raises clear error); load `config/scoring.yml` with `functools.lru_cache`
- [X] T003 [P] Update `app/ai/parsing.py` — rename `normalize_omj_score()` to `clamp_score(score: int, max_points: int) -> int`; remove `VALID_SCORES_ETAP1/2/3` constants; update `parse_ai_response` signature to accept `max_points: int` instead of `etap: str`; update module docstring (OMJ → FerMat)
- [X] T004 [P] Update `app/ai/prompt_builder.py` — change `build_prompt(etap)` to `build_prompt(etap: str, task_number: int, max_points: int)`; remove `"etap3"` from `SCORING_PROMPT_FILES` dict; append dynamic line `"Oceń rozwiązanie w skali 0–{max_points} punktów (liczba całkowita)."` to assembled prompt
- [X] T005 Update `app/ai/providers/gemini.py` — call `get_max_points(etap, task_number)` from `scoring_config.py` at start of `analyze_solution()` and `analyze_solution_stream()`; pass `max_points` to `build_prompt()` and `parse_ai_response()`; update `RESPONSE_JSON_SCHEMA["properties"]["score"]["description"]` to `"Score from 0 to max_points for this task (integer)"`; remove `etap3` reference in docstring (depends on T002, T003, T004)
- [X] T006 [P] Replace `prompts/gemini_prompt_scoring_etap1.txt` — FerMat etap1 criteria matching configurable scale; educational tone (kl. 4–6); omit OMJ-specific language
- [X] T007 [P] Replace `prompts/gemini_prompt_scoring_etap2.txt` — FerMat etap2 criteria matching configurable scale; keep assessment rubric logic, remove OMJ branding
- [X] T008 [P] Delete `prompts/gemini_prompt_scoring_etap3.txt` — FerMat has no etap3

**Checkpoint**: AI scoring pipeline uses YAML-sourced `max_points`; no hardcoded OMJ score sets remain; `grep "VALID_SCORES_ETAP\|normalize_omj_score\|etap3" app/ai/` returns 0 results.

---

## Phase 3: User Story 1 — Przeglądanie zadań (Priority: P1) 🎯 MVP

**Goal**: All user-facing text, titles, SEO metadata, and branding show FerMat identity;
no OMJ text visible to students browsing tasks.

**Independent Test**: Open http://localhost:3000, navigate to any task via 3 clicks —
verify "FerMat" everywhere, zero "OMJ" or "Olimpiada Matematyczna Juniorów" visible.

### Implementation for User Story 1

- [X] T009 [P] [US1] Update `frontend/src/lib/utils/constants.ts` — `APP_NAME = "FerMat Validator"`, `APP_TITLE = "FerMat Validator – Konkurs Matematyczny FerMat"`, `APP_DESCRIPTION` (FerMat-specific), `SITE_URL = "https://fermat-validator.pl"` (or TBD domain), `CONTACT_EMAIL` (update from omj.validator@gmail.com)
- [X] T010 [P] [US1] Update `frontend/src/app/layout.tsx` — keywords array (remove "OMJ", "olimpiada matematyczna juniorów"; add FerMat equivalents); `description` meta; JSON-LD organization name/description
- [X] T011 [P] [US1] Update `frontend/src/app/years/page.tsx` — `title` ("Archiwum zadań FerMat"), `description`; remove "OMJ started in 2005" comment; update edition count label
- [X] T012 [P] [US1] Update `frontend/src/app/years/[year]/page.tsx` — `title` template (`FerMat ${year}`), `description` (remove "Olimpiady Matematycznej Juniorów" phrase); page heading
- [X] T013 [P] [US1] Update `frontend/src/app/years/[year]/[etap]/page.tsx` — `title` template, `description`; ensure etap display label is "Etap I"/"Etap II" (not "etap1"/"etap2")
- [X] T014 [P] [US1] Update `frontend/src/app/task/[year]/[etap]/[num]/page.tsx` — `title` template (remove `| OMJ` suffix)
- [X] T015 [US1] Update `frontend/src/app/page.tsx` — homepage headline, sub-descriptions, feature bullet texts, demo image alt text (`/images/omj-demo.gif` → rename or update ref if image is replaced); remove "Ponad 340 zadań z 20 lat Olimpiady Matematycznej Juniorów" copy
- [X] T016 [P] [US1] Update `frontend/src/components/layout/Footer.tsx` — tagline, links (`omj.edu.pl` → `sp221.edu.pl`); remove "Oficjalna strona OMJ" link; add FerMat competition link; update GitHub repo link if changed
- [X] T017 [US1] Rewrite `frontend/src/app/regulamin/page.tsx` — replace all OMJ references with FerMat/SP 221; update site URL from `omj-validator.pl`; update GitHub repo href; update task content attribution (SP 221, not OMJ)
- [X] T018 [P] [US1] Update `frontend/src/app/opengraph-image.tsx` — "Trener OMJ" → "FerMat Validator"; "Olimpiada Matematyczna Juniorów" → "Konkurs Matematyczny FerMat"; update domain text
- [X] T019 [P] [US1] Update `frontend/src/app/sitemap.ts` and `frontend/src/app/robots.ts` — `SITE_URL` constant (import from `constants.ts` if not already)

**Checkpoint**: `grep -ri "omj\|olimpiada matematyczna juniorow" frontend/src/` (case-insensitive) returns 0 results outside of `regulamin/page.tsx` historical attribution comments (if any).

---

## Phase 4: User Story 2 — Przesyłanie rozwiązania i ocena AI (Priority: P2)

**Goal**: Backend uses FerMat branding and YAML-driven scoring; submission flow returns
correct score range per task; missing-solution path works with clear user message.

**Independent Test**: Submit any image to 2024 etap1 task 3 (score 0–2); then to 2019 etap2
task 1 (no solution PDF — verify disclaimer message).

**Prerequisites**: Phase 2 (Foundational) must be complete.

### Implementation for User Story 2

- [X] T020 [P] [US2] Update `app/main.py` — `FastAPI(title="FerMat Validator", description="Walidator rozwiązań FerMat")`
- [X] T021 [P] [US2] Update `app/config.py` — default `google_group_email` (remove `omj-validator-alpha@googlegroups.com`; replace with placeholder or FerMat group); update DB URL comment (line 140: `omj:omj@localhost/omj` → `fermat:fermat@localhost/fermat` in comment)
- [X] T022 [P] [US2] Update `app/models.py` docstring (line 8: "OMJ tasks" → "FerMat tasks"); `app/progress.py` module docstring; `app/skills.py` module docstring — all OMJ → FerMat
- [X] T023 [P] [US2] Update `app/db/__init__.py`, `app/db/models.py`, `app/db/repositories.py`, `app/db/session.py` — module-level docstrings "OMJ Validator" → "FerMat Validator"
- [X] T024 [P] [US2] Update `docker-compose.yml` (dev) and `docker-compose.prod.yml` (prod) — DB name `omj` → `fermat`, DB user `omj` → `fermat`, DB password `omj` → `fermat`; update `DATABASE_URL` environment variable accordingly
- [X] T025 [US2] Update `docker-compose.e2e.yml` — project name `omj-e2e` → `fermat-e2e`; container names `omj-e2e-*` → `fermat-e2e-*`; `POSTGRES_DB: omj_e2e` → `fermat_e2e`; `DATABASE_URL` postgres connection string (depends on T024 for consistency)

**Checkpoint**: `grep -ri "omj" app/ docker-compose*.yml` returns 0 results; AI submission for 2024/etap1 returns score in `[0, 2]` for task 1–5.

---

## Phase 5: User Story 3 — Progresywne wskazówki (Priority: P3)

**Goal**: Remaining UI pages carry FerMat branding; localStorage key uses FerMat namespace.

**Independent Test**: Click "Pokaż wskazówkę" on any task with hints — verify 4-level
progression works; check localStorage — key should be `fermat-practice-timer` (not `omj-*`).

### Implementation for User Story 3

- [X] T026 [P] [US3] Update `frontend/src/app/progress/page.tsx` — `description` meta (remove "OMJ" references)
- [X] T027 [P] [US3] Update `frontend/src/app/practice/etap2/page.tsx` — `description` meta; update "Olimpiady Matematycznej Juniorów" → "Konkursu Matematycznego FerMat"
- [X] T028 [P] [US3] Update `frontend/src/lib/contexts/TimerContext.tsx` — `STORAGE_KEY = "omj-practice-timer"` → `"fermat-practice-timer"`

**Checkpoint**: `grep -ri "omj" frontend/src/` returns 0 results; hint progression works end-to-end on any task with `hints` array populated.

---

## Phase 6: Task Ingestion — download_fermat.py

**Goal**: Administrator can download all FerMat PDFs from sp221.edu.pl with a single command.

**Independent Test**: Run `python download_fermat.py --dry-run` — verify it lists expected
editions without downloading; run `python download_fermat.py --year 2024` — verify
`tasks/2024/etap1/tasks.pdf` and `tasks/2024/etap1/solutions.pdf` are created.

- [X] T029 Create `download_fermat.py` — standalone CLI script (no web framework deps): fetches sp221.edu.pl task listing page, discovers PDF links per edition/etap, downloads to `tasks/{year}/{etap}/` (mirroring existing directory layout), skips already-downloaded files (idempotent), prints download summary; supports `--year YEAR`, `--dry-run`, `--force` flags

**Checkpoint**: `python download_fermat.py --dry-run` exits 0 and lists at least 9 editions.

---

## Final Phase: Polish & Cross-Cutting Concerns

**Purpose**: Verify migration completeness, smoke-test end-to-end, catch stragglers.

- [X] T030 [P] Audit remaining OMJ references: run `grep -ri "omj\|olimpiada matematyczna juniorow" --include="*.py" --include="*.ts" --include="*.tsx" --include="*.yml" --include="*.yaml" --include="*.txt" . | grep -v "node_modules\|\.git\|__pycache__\|specs/"` — fix any remaining hits not covered by T009–T028
- [X] T031 [P] Validate `config/scoring.yml` error handling: temporarily corrupt YAML and verify application fails with clear error message; restore file; verify `get_max_points("etap1", 99)` raises a clear error caught before submission
- [X] T032 Run quickstart.md smoke-test checklist (`specs/001-fermat-validator-app/quickstart.md`) — verify all 5 checkpoint sections pass end-to-end
- [X] T033 [P] Update `README.md` (if it exists) and `docs/production-deployment.md` — replace "OMJ Validator" with "FerMat Validator"; update domain references

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on T001 (scoring.yml must exist for scoring_config.py) — BLOCKS User Story 2
- **User Story 1 (Phase 3)**: Depends on Phase 1 only — can start once T001 is done; does NOT depend on Phase 2
- **User Story 2 (Phase 4)**: Depends on Phase 2 completion — scoring pipeline must work before testing submission
- **User Story 3 (Phase 5)**: Independent of Phase 2 — can run in parallel with Phase 3 or 4
- **Task Ingestion (Phase 6)**: Independent of all above — can start anytime
- **Polish (Final)**: Depends on all user story phases complete

### Within Phase 2 (Scoring Infrastructure)

```
T001 (scoring.yml)
  └── T002 (scoring_config.py loader)
      └── T005 (gemini.py — integrates T002+T003+T004)
T003 (parsing.py) ──[P with T002]──┘
T004 (prompt_builder.py) ──[P]────┘
T006 (prompt etap1 file) ──[P]── independent
T007 (prompt etap2 file) ──[P]── independent
T008 (delete etap3 file) ──[P]── independent
```

### Within Phase 3 (US1 — Frontend)

T009–T014, T016, T018–T019 can all run in parallel (different files).
T015 and T017 are larger rewrites — run sequentially after parallelizable tasks.

### Within Phase 4 (US2 — Backend)

T020–T024 are all parallel (different files). T025 depends on T024 for DB naming consistency.

### Within Phase 5 (US3)

T026, T027, T028 are all parallel (different files).

---

## Parallel Execution Examples

### Phase 2: Scoring Foundation

```
Parallel batch 1 (all independent):
  Task: "Create app/ai/scoring_config.py with get_max_points()" [T002]
  Task: "Replace normalize_omj_score() in app/ai/parsing.py" [T003]
  Task: "Update build_prompt() in app/ai/prompt_builder.py" [T004]
  Task: "Replace prompts/gemini_prompt_scoring_etap1.txt" [T006]
  Task: "Replace prompts/gemini_prompt_scoring_etap2.txt" [T007]
  Task: "Delete prompts/gemini_prompt_scoring_etap3.txt" [T008]

Sequential after batch 1:
  Task: "Update app/ai/providers/gemini.py to use max_points" [T005]
```

### Phase 3: User Story 1 Frontend

```
Parallel batch (all different files):
  Task: "Update frontend/src/lib/utils/constants.ts" [T009]
  Task: "Update frontend/src/app/layout.tsx" [T010]
  Task: "Update frontend/src/app/years/page.tsx" [T011]
  Task: "Update frontend/src/app/years/[year]/page.tsx" [T012]
  Task: "Update frontend/src/app/years/[year]/[etap]/page.tsx" [T013]
  Task: "Update frontend/src/app/task/[year]/[etap]/[num]/page.tsx" [T014]
  Task: "Update frontend/src/components/layout/Footer.tsx" [T016]
  Task: "Update frontend/src/app/opengraph-image.tsx" [T018]
  Task: "Update frontend/src/app/sitemap.ts and robots.ts" [T019]

Sequential (larger files):
  Task: "Update frontend/src/app/page.tsx homepage" [T015]
  Task: "Rewrite frontend/src/app/regulamin/page.tsx" [T017]
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001)
2. Complete Phase 2: Foundational (T002–T008) — unblocks scoring
3. Complete Phase 3: User Story 1 (T009–T019) — FerMat branding live
4. **STOP and VALIDATE**: Browse app at http://localhost:3000; verify zero OMJ text
5. Deploy / demo if ready

### Incremental Delivery

1. Phase 1 + Phase 2 → Scoring infrastructure ready
2. Phase 3 → FerMat branding, task browsing works (US1 MVP)
3. Phase 4 → Submission with new scoring (US2 complete)
4. Phase 5 → Hints branding cleanup (US3 complete)
5. Phase 6 → Task ingestion script ready
6. Final Phase → Full audit and smoke test

### Parallel Team Strategy

- **Person A**: Phase 2 (scoring infrastructure — backend focus)
- **Person B**: Phase 3 (frontend domain cleanup — frontend focus)
- Both can work simultaneously after T001 is done.
- Phase 4 and 5 can follow in any order after their prerequisites.

---

## Notes

- `[P]` tasks operate on different files — safe to parallelize
- `[Story]` label maps each task to its user story for traceability
- T005 is the integration point for all Phase 2 changes — do it last in that phase
- T025 (docker-compose.e2e.yml) should be done after T024 to keep DB naming consistent
- The `regulamin/page.tsx` rewrite (T017) is the largest single task — allocate extra time
- After T030 audit, fix any stragglers before marking Polish phase complete
- `config/scoring.yml` is NOT inside Docker — it must be present at the repo root
  (it's bind-mounted into the container per Docker Compose setup)
