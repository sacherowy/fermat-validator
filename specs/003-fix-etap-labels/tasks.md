# Tasks: Korekta opisów etapów (etap1/etap2)

**Input**: Design documents from `/specs/003-fix-etap-labels/`

**Prerequisites**: [plan.md](plan.md) (required), [spec.md](spec.md) (required for user stories)

**Tests**: Not requested — spec.md confirms no E2E assertions on corrected labels and no unit test changes needed.

**Organization**: Tasks are grouped by user story. All changes are purely presentational text edits — no new files, no schema changes, no API changes.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: No project initialization required — this feature modifies existing text in existing files only.

- [X] T001 Verify target files exist and contain expected strings (grep for "okręgowy", "wojewódzki", "etap3", "2004" in identified files)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: No blocking foundational infrastructure — all user stories can proceed immediately after T001.

*(No tasks — changes are independent text edits with no shared prerequisites beyond file existence.)*

---

## Phase 3: User Story 1 - Poprawne etykiety etapów w nawigacji (Priority: P1) 🎯 MVP

**Goal**: The etap2 card on `/years/{year}` no longer implies a regional/provincial stage level.

**Independent Test**: Visit `/years/2024`, confirm the Etap II card description does NOT contain "wojewódzki", "okręgowy", or any other regional qualifier.

### Implementation for User Story 1

- [X] T002 [US1] Change etap2 description from `"Etap wojewódzki"` to `"Drugi etap szkolny"` in `frontend/src/app/years/[year]/page.tsx` (line 54)

**Checkpoint**: User Story 1 is fully functional — the most visible label change is live in Next.js frontend.

---

## Phase 4: User Story 2 - Spójna terminologia w całej aplikacji (Priority: P2)

**Goal**: All surfaces (Next.js + legacy Jinja2 HTML templates) use consistent, correct FerMat stage labels.

**Independent Test**: `grep -r "okręgowy\|wojewódzki" templates/ frontend/src/` returns no results.

### Implementation for User Story 2

- [X] T003 [P] [US2] Change `Etap II (okręgowy)` to `Etap II (szkolny)` in `templates/year.html` (line 24)
- [X] T004 [P] [US2] Change `Etap II (okręgowy)` to `Etap II (szkolny)` in `templates/etap.html` (line 17, inside the Jinja2 `{% elif etap == "etap2" %}` branch)

**Checkpoint**: User Stories 1 and 2 are both complete — no "okręgowy" or "wojewódzki" strings remain in any user-facing surface.

---

## Phase 5: User Story 3 - Poprawne filtry na stronie "Moje rozwiązania" (Priority: P2)

**Goal**: The `/my-solutions` filter shows only Etap I and Etap II, and the year range starts at 2017 (first FerMat edition).

**Independent Test**: Visit `/my-solutions`, open the "Etap" filter — options are only "Wszystkie", "Etap I", "Etap II". Open the "Rok" filter — earliest year is 2017.

### Implementation for User Story 3

- [X] T005 [US3] Fix year range: change `currentYear - 2004` to `currentYear - 2016` in `frontend/src/components/my-solutions/FiltersBar.tsx` (lines 25–27, also update the comment to reference 2017)
- [X] T006 [US3] Remove `<MenuItem value="etap3">Etap III</MenuItem>` from `frontend/src/components/my-solutions/FiltersBar.tsx` (line 98)

**Checkpoint**: All three user stories are complete — filters show correct etap/year options.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final verification that no regressions were introduced.

- [X] T007 [P] Run backend unit tests to confirm no regressions: `pytest tests/` from repo root
- [X] T008 [P] Run frontend unit tests to confirm no regressions: `cd frontend && npm test`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Empty — no blocking prereqs
- **User Stories (Phases 3–5)**: All depend only on T001 (file verification); can proceed in parallel
- **Polish (Phase 6)**: Depends on Phases 3–5 completion

### User Story Dependencies

- **US1 (P1)**: Independent — single file, single line change
- **US2 (P2)**: Independent — two different template files (T003, T004 are parallel)
- **US3 (P2)**: Independent — same file but different lines (T005 before T006 for safety)

### Within Each User Story

- US2: T003 and T004 are in different files → can run in parallel
- US3: T005 and T006 are in the same file → run sequentially

### Parallel Opportunities

- T003 and T004 can run simultaneously (different files, different template engines)
- T007 and T008 can run simultaneously (different test suites)

---

## Parallel Example: User Story 2

```bash
# Launch both template fixes simultaneously:
Task: "Change Etap II (okręgowy) → Etap II (szkolny) in templates/year.html"
Task: "Change Etap II (okręgowy) → Etap II (szkolny) in templates/etap.html"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete T001: Verify target files
2. Complete T002: Fix Next.js year page — most user-visible change
3. **STOP and VALIDATE**: Visit `/years/2024`, confirm etap2 card shows "Drugi etap szkolny"
4. Ship if urgency requires — US2 and US3 are follow-up polish

### Incremental Delivery

1. T001 → T002 → Validate US1 (MVP)
2. T003 + T004 (parallel) → Validate US2
3. T005 → T006 → Validate US3
4. T007 + T008 (parallel) → Confirm no regressions

### Single Developer

All 6 implementation tasks are independent text edits — complete in order T001→T002→T003→T004→T005→T006→T007/T008.

---

## Notes

- [P] tasks = different files, no dependencies → safe to parallelize
- URL keys (`etap1`, `etap2`) and DB identifiers are NOT changed — only display text
- No new files created, no schema changes, no API changes
- E2E tests confirmed clean: no assertions on "okręgowy", "wojewódzki", or "Etap III"
- `constants.test.ts` tests `getMaxScore("etap3")` — internal identifier, not a UI label → unchanged
