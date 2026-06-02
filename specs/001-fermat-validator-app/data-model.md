# Data Model: FerMat Validator

**Feature**: `001-fermat-validator-app`
**Date**: 2026-06-02

---

## Entities

### Edition (Edycja)

Represents one year of the FerMat competition.

| Field | Type | Notes |
|-------|------|-------|
| `year` | int | 2017–2025 (editions I–IX) |
| `stages` | list[Stage] | Always [etap1, etap2] |

Derived from the filesystem: `tasks/{year}/` directory.

---

### Stage (Etap)

One stage within an edition. FerMat has exactly two: `etap1` and `etap2`.

| Field | Type | Notes |
|-------|------|-------|
| `etap_id` | str | `"etap1"` or `"etap2"` (tech ID; display as "Etap I" / "Etap II") |
| `year` | int | FK → Edition |
| `tasks` | list[Task] | Tasks belonging to this stage |
| `scoring_config` | ScoringConfig | Loaded from `config/scoring.yml` at runtime |

---

### Task (Zadanie)

A single competition problem.

| Field | Type | Notes |
|-------|------|-------|
| `number` | int | 1–10 |
| `title` | str | Optional; may contain LaTeX |
| `content` | str | Full problem text; may contain LaTeX |
| `year` | int | FK → Edition |
| `etap` | str | FK → Stage (`etap1`\|`etap2`) |
| `pdf_task` | Path | Absolute path: `tasks/{year}/{etap}/tasks.pdf` (or per-task) |
| `pdf_solution` | Path\|None | Only for year≥2024 AND etap==etap1 |
| `hints` | list[str] | Up to 4 strings; empty list if none |
| `difficulty` | int\|None | Optional; 1–5 |
| `categories` | list[str] | Optional; from taxonomy in `config/scoring.yml` |
| `prerequisites` | list[str] | Optional; e.g. `["2023_etap1_2"]` |

Persisted as: `data/tasks/{year}/{etap}/task_{number}.json`

**Solution PDF availability rule**:
```
has_solution = (year >= 2024) AND (etap == "etap1")
```

---

### Submission (Zgłoszenie)

A student's solution attempt, stored in PostgreSQL. Schema unchanged from OMJ.

| Field | Type | Notes |
|-------|------|-------|
| `id` | int | Auto PK |
| `user_id` | str | FK → User (Google sub) |
| `year` | int | |
| `etap` | str | `"etap1"` or `"etap2"` |
| `task_number` | int | |
| `score` | int | 0 … max_points (from ScoringConfig) |
| `feedback` | str | Polish text from AI; includes non-official disclaimer |
| `created_at` | datetime | UTC |
| `image_paths` | str | JSON-serialized list of relative paths |

No Alembic migration required — column structure is identical to OMJ.

---

### User (Użytkownik)

Google OAuth account. Schema unchanged from OMJ.

| Field | Type | Notes |
|-------|------|-------|
| `google_sub` | str | PK |
| `email` | str | |
| `name` | str | |
| `created_at` | datetime | |

---

### ScoringConfig

Runtime configuration loaded from `config/scoring.yml`. Not persisted in DB.

| Field | Type | Notes |
|-------|------|-------|
| `etap` | str | `"etap1"` or `"etap2"` |
| `task_groups` | list[TaskGroup] | Ordered; used to look up `max_points` |
| `total_max` | int | Sum of all group max_points |

#### TaskGroup

| Field | Type | Notes |
|-------|------|-------|
| `tasks` | list[int] | Task numbers in this group, e.g. `[1,2,3,4,5]` |
| `max_points` | int | Per-task maximum for this group |

---

## YAML Schema: `config/scoring.yml`

```yaml
# FerMat Validator — Scoring Configuration
# Edit this file to adjust point scales; no rebuild required.

etap1:
  task_groups:
    - tasks: [1, 2, 3, 4, 5]
      max_points: 2
    - tasks: [6, 7, 8, 9, 10]
      max_points: 4

etap2:
  task_groups:
    - tasks: [1, 2, 3, 4, 5]
      max_points: 2
    - tasks: [6, 7, 8, 9, 10]
      max_points: 4
```

### Validation rules (enforced by `scoring_config.py` at startup):

1. Both `etap1` and `etap2` keys MUST be present.
2. Every `task_groups` entry MUST have `tasks` (non-empty list of ints) and
   `max_points` (positive int).
3. Task numbers within an etap MUST be unique across all groups.
4. Missing config for a submitted task MUST raise a validation error blocking
   the submission (per FR-007).

---

## Filesystem Layout (data)

```text
tasks/
└── {year}/                    # e.g., 2024/
    ├── etap1/
    │   ├── tasks.pdf          # All tasks for etap1 (single PDF per stage)
    │   └── solutions.pdf      # Solutions (only year >= 2024)
    └── etap2/
        └── tasks.pdf

data/
├── tasks/
│   └── {year}/
│       ├── etap1/
│       │   ├── task_1.json
│       │   └── task_2.json … task_10.json
│       └── etap2/
│           └── task_1.json … task_10.json
└── uploads/
    └── {user_id}/
        └── {year}/
            └── {etap}/
                └── {task_num}/
                    └── {filename}

config/
└── scoring.yml                # Admin-editable scoring configuration
```
