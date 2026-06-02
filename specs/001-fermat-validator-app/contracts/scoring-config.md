# Contract: Scoring Configuration YAML

**Audience**: Application administrator (SP 221)
**File**: `config/scoring.yml` (in repository root, mounted into Docker containers)
**Date**: 2026-06-02

---

## Purpose

The scoring configuration defines the maximum points a student can receive per
task, grouped by etap and task number. This file is read at application startup
and re-read on each scoring YAML cache miss. Changes take effect without
restarting or rebuilding the application (subject to cache TTL).

---

## Schema

```yaml
# Top-level keys: etap1 and etap2 (REQUIRED, both must be present)

etap1:                         # Stage I configuration (REQUIRED)
  task_groups:                 # List of task groups (REQUIRED, min 1 entry)
    - tasks: [1, 2, 3, 4, 5]  # List of task numbers in this group (REQUIRED)
      max_points: 2            # Max points per task in this group (REQUIRED, int > 0)
    - tasks: [6, 7, 8, 9, 10]
      max_points: 4

etap2:                         # Stage II configuration (REQUIRED)
  task_groups:
    - tasks: [1, 2, 3, 4, 5]
      max_points: 2
    - tasks: [6, 7, 8, 9, 10]
      max_points: 4
```

---

## Validation Rules

| Rule | Error if violated |
|------|-------------------|
| Both `etap1` and `etap2` keys must exist | Config load failure at startup |
| `task_groups` must be a non-empty list | Config load failure |
| Each group must have `tasks` (list of ints) | Config load failure |
| Each group must have `max_points` (int > 0) | Config load failure |
| Task numbers within an etap must be unique | Config load failure |
| Task number for submitted task must exist in config | Submission rejected (HTTP 422) |

---

## Computed Values

The application derives the following from this config at runtime:

- `total_max(etap)`: Sum of `max_points × len(tasks)` across all groups for an etap.
  Example: etap1 total_max = (5 × 2) + (5 × 4) = 30 points. *(Note: 5 tasks × 2 pts + 5 tasks × 4 pts)*
- `max_points(etap, task_number)`: Looked up from the group containing `task_number`.

---

## Behavior Contract for the Application

1. **Startup**: Config is loaded and validated once. Invalid YAML causes application
   startup failure with a clear error message.
2. **Submission**: Before invoking AI, the system looks up `max_points` for the
   submitted `(etap, task_number)`. If not found, submission is rejected with a
   user-friendly error: *"Brak konfiguracji punktacji dla tego zadania."*
3. **AI Prompt**: The prompt includes: *"Oceń rozwiązanie w skali 0–{max_points} punktów."*
4. **Score Clamp**: AI response score is clamped to `[0, max_points]` server-side
   regardless of AI output.
5. **Hot Reload**: Config changes are picked up within the cache TTL (default: at
   next application restart or cache expiry). For immediate effect, restart the
   `api` container.

---

## Example: Adding a Future Edition Override

If a future edition uses a different scale, extend the YAML with per-year overrides
(requires application code support — currently uses `default` only):

```yaml
# Future extension example (NOT yet implemented):
# overrides:
#   2026:
#     etap1:
#       task_groups:
#         - tasks: [1, 2, 3, 4, 5]
#           max_points: 3
#         - tasks: [6, 7, 8, 9, 10]
#           max_points: 5
```
