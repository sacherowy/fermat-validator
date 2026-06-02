# Research: FerMat Validator Domain Migration

**Feature**: `001-fermat-validator-app`
**Date**: 2026-06-02

---

## Decision 1: YAML Scoring Config Structure

**Decision**: Flat YAML with `etap1`/`etap2` top-level keys, each containing
`task_groups` (list of task ranges with `max_points`) and `total_max`.

**Rationale**: The spec requires per-etap configurability. Task groups are the
natural grouping unit for FerMat (tasks 1–5 vs 6–10 have different weights).
A flat structure is easier for a non-developer admin to edit than a nested
per-edition override structure. Per-edition overrides can be added later if needed.

**Alternatives considered**:
- Per-task flat list (`task_1: 2, task_2: 2, ...`): More verbose, error-prone for admin.
- Per-edition nested structure: Premature complexity — all known editions share the
  same scale. Deferred to future amendment if editions diverge.

---

## Decision 2: Score Normalization Strategy

**Decision**: Replace `normalize_omj_score(score, etap)` with
`clamp_score(score, max_points)` that simply clamps AI output to `[0, max_points]`.
The AI prompt is updated to explicitly state the allowed score range for the
specific task being evaluated.

**Rationale**: OMJ used a sparse discrete set {0,1,3} or {0,2,5,6} that required
mapping logic. FerMat uses a continuous integer range [0, N] where N comes from
the YAML config. Clamping is both simpler and more correct — it preserves the AI's
nuanced score within the allowed range rather than snapping to discrete values.

**Key change in call chain**:

```
Before:  build_prompt(etap)  →  parse_ai_response(text, etap)  →  normalize_omj_score(score, etap)
After:   build_prompt(etap, task_number, max_points)  →  parse_ai_response(text, max_points)  →  clamp_score(score, max_points)
```

`task_number` is already available in `analyze_solution()` — no signature change
to the public AI interface needed.

**Alternatives considered**:
- Keep discrete normalization with FerMat-specific sets: Unnecessarily complex
  for a continuous scale; would hardcode values that belong in YAML.
- Offload clamping entirely to the AI (no server-side normalization): Risky —
  AI can hallucinate out-of-range values; server-side clamp is a safety net.

---

## Decision 3: Prompt File Strategy for FerMat Scoring Criteria

**Decision**: Replace `gemini_prompt_scoring_etap1.txt` and
`gemini_prompt_scoring_etap2.txt` with FerMat-appropriate rubrics. Delete
`gemini_prompt_scoring_etap3.txt`. Inject dynamic `max_points` into the prompt
via `build_prompt()` at call time (not baked into static files).

**Rationale**: Static files contain OMJ-specific point values and language.
FerMat rubrics need to describe the competition's educational context (primary
school, non-official assessment). The `max_points` value is task-specific and
YAML-driven — it cannot be static.

**Prompt injection approach**: `build_prompt()` appends a dynamic scoring line:
```
Oceń rozwiązanie w skali 0-{max_points} punktów (liczba całkowita).
```
This overrides the static file's generic scale instruction.

---

## Decision 4: etap3 Removal Strategy

**Decision**: Remove `etap3` from all code surfaces:
- Delete `prompts/gemini_prompt_scoring_etap3.txt`
- Remove `"etap3": "..."` entry from `SCORING_PROMPT_FILES` dict in `prompt_builder.py`
- Remove `VALID_SCORES_ETAP3` constant from `parsing.py`
- Remove `etap3` from the `etap` parameter default comment in `gemini.py`

**Rationale**: FerMat competition has exactly two stages (etap1, etap2). Leaving
etap3 as dead code creates confusion and risks accidental use.

**Alternatives considered**:
- Keep etap3 for backward compatibility: No FerMat data uses etap3;
  backward compat with OMJ data is explicitly out of scope (DB wiped).

---

## Decision 5: download_fermat.py Design

**Decision**: New standalone CLI script (no web framework dependency) that:
1. Fetches the task listing page from sp221.edu.pl
2. Discovers PDF links per edition/etap
3. Downloads to `tasks/{year}/{etap}/` mirroring the existing directory structure
4. Skips already-downloaded files (idempotent)
5. Prints a summary of what was downloaded/skipped

**Rationale**: The existing `download_tasks.py` pattern (OMJ) is the established
convention in this codebase. A new script specific to the FerMat URL structure
follows the same pattern and is runnable outside Docker by the admin.

**Alternatives considered**:
- Extend `download_tasks.py`: Would conflate two different source sites;
  cleaner to have a purpose-specific script.
- Admin manual copy via SSH: Valid fallback per clarification Q1, but a script
  makes onboarding future admins easier.

---

## Decision 6: Docker / Infrastructure Rename Scope

**Decision**: In `docker-compose.e2e.yml`, rename:
- Project name: `omj-e2e` → `fermat-e2e`
- Container names: `omj-e2e-*` → `fermat-e2e-*`
- DB name: `omj_e2e` → `fermat_e2e`
- DB user/pass credentials: keep `e2e`/`e2e` (not OMJ-specific)

In production (`docker-compose.prod.yml`) and dev (`docker-compose.yml`):
- Change DB name `omj` → `fermat` in DATABASE_URL
- Change DB user `omj` → `fermat` (or keep as `app` — non-OMJ neutral)
- Update `.env.example` if present

**Rationale**: Container and DB names with "omj" are visible in `docker ps` and
`psql` — violates Constitution I (Domain Fidelity) in the operational context.

---

## Resolved NEEDS CLARIFICATION

All items resolved during `/speckit-clarify` session on 2026-06-02. No open items.
