# Implementation Plan: Clear OMJ Data and Download FerMat Task PDFs

**Branch**: `002-fermat-task-download` | **Date**: 2026-06-04 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/002-fermat-task-download/spec.md`

## Summary

Remove OMJ competition PDFs from `tasks/` (one-time migration) and update `download_fermat.py` to correctly target the live FerMat website at `https://sp221.edu.pl/files/171/`. The existing script has the right architecture but wrong URLs; Phase 0 research confirmed the actual URL patterns and established that combined PDFs (2017–2023) and per-etap PDFs (2024–2025) require different handling.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: stdlib only (`urllib`, `argparse`, `re`, `pathlib`) — no new dependencies

**Storage**: Local filesystem — `tasks/{year}/{etap}/tasks.pdf` and `tasks/{year}/{etap}/solutions.pdf`

**Testing**: Manual — `--dry-run` flag + file existence checks; no automated test framework needed for this standalone script

**Target Platform**: macOS/Linux (developer workstation, run outside Docker)

**Project Type**: CLI utility script

**Performance Goals**: Full run completes in under 5 minutes (SC-003); approximately 20–30 HTTP requests total

**Constraints**: No third-party libraries; must not write files in `--dry-run` mode; must be idempotent by default

**Scale/Scope**: ~20–30 PDF files across 10 editions (2017–2026), 2 etaps each (some combined)

## Constitution Check

*GATE: Must pass before implementation. Re-checked after Phase 1 design.*

| Principle | Gate | Status |
|-----------|------|--------|
| I. Domain Fidelity | Clearing OMJ data removes all OMJ-named files; new download populates only FerMat PDFs | ✅ PASS |
| II. Architecture Continuity | Script is a standalone utility; no changes to FastAPI, frontend, or DB layers | ✅ PASS |
| III. Configurable Scoring | Not applicable to this feature (no scoring logic involved) | ✅ N/A |
| IV. Educational Intent | Not applicable (no user-facing UI or feedback) | ✅ N/A |
| V. Data Availability Awareness | Solutions saved only for 2024–2025 etap1 (`-e1r.pdf`); all other combos are task-only | ✅ PASS |

**Post-design re-check**: No violations introduced. Combined PDFs for 2017–2023 stored as `etap1/tasks.pdf` only (no phantom etap2 entries). Solutions gating matches Principle V exactly.

## Project Structure

### Documentation (this feature)

```text
specs/002-fermat-task-download/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── contracts/
│   └── cli-contract.md  # CLI interface contract
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code (repository root)

```text
download_fermat.py       # Updated in-place (URL logic, year range, combined vs split PDFs)
create_tasks.py          # TASK_COUNTS updated: etap1→10, etap2→10, etap3 removed
populate_metadata.py     # Prompt updated: OMJ→FerMat, age 9-12, no etap3 guidance

tasks/                   # Cleared of OMJ data, then populated by script
├── 2017/etap1/tasks.pdf
├── 2018/etap1/tasks.pdf
...
├── 2023/etap1/tasks.pdf
├── 2024/etap1/tasks.pdf
├── 2024/etap1/solutions.pdf
├── 2024/etap2/tasks.pdf
├── 2025/etap1/tasks.pdf
├── 2025/etap1/solutions.pdf
├── 2025/etap2/tasks.pdf
└── 2026/etap1/tasks.pdf  (combined PDF, if already published)
```

## Implementation Tasks

### Task 1 — Clear OMJ Data

**What**: Remove all OMJ artifacts from three locations:

| Location | Count | Command |
|---|---|---|
| `tasks/` | ~80 PDFs | `rm -rf tasks/*/` |
| `data/tasks/` | 352 task JSONs | `rm -rf data/tasks/*/` |
| `data/task_prerequisites_analysis.md` | 1 file | `rm -f data/task_prerequisites_analysis.md` |

**Full command sequence**:
```bash
rm -rf tasks/*/
rm -rf data/tasks/*/
rm -f data/task_prerequisites_analysis.md
```

**Verification**:
```bash
find tasks/ -type f | wc -l          # → 0
find data/tasks/ -type f | wc -l     # → 0
ls data/task_prerequisites_analysis.md 2>&1  # → No such file
```

**Do NOT delete**:
- `data/skills.json` — generic math skills taxonomy, already adapted for FerMat; kept as-is
- `data/uploads/` and `data/submissions/` — empty placeholders

**Notes**:
- One-time migration; not encoded in `download_fermat.py`
- SC-001 is satisfied when all three checks pass

---

### Task 2 — Update `download_fermat.py`

**What**: Replace the URL generation logic with known FerMat patterns from research.

**Changes**:

1. **Replace `BASE_URL`** (was pointing at wrong path):
   ```python
   BASE_URL = "https://sp221.edu.pl/files/171/"
   LISTING_URL = "https://sp221.edu.pl/zadania-z-poprzednich-edycji,171,pl"
   ```

2. **Replace `generate_expected_urls()`** with a function that builds a deterministic candidate list:
   - Years 2017–2023: one candidate → `fermatYYYY.pdf` → saved as `{year}/etap1/tasks.pdf`
   - Years 2024–2025: three candidates per year:
     - `fermatYYYY-e1.pdf` → `{year}/etap1/tasks.pdf`
     - `fermatYYYY-e2.pdf` → `{year}/etap2/tasks.pdf`
     - `fermatYYYY-e1r.pdf` → `{year}/etap1/solutions.pdf`
   - Year 2026: try combined first (`fermat2026.pdf` → `etap1/tasks.pdf`), then split if it 404s
   - Future years (2027+): same split pattern as 2024–2025

3. **Remove `discover_pdf_links()` HTML scraping** — no longer needed as primary path; retain as dead code removal.

4. **Remove `probe_url()` slow probing loop** — the known candidate list replaces it. HTTP 404 during actual download is already handled gracefully by `download_file()`.

5. **Update `run()`**: remove the two-step "try scraping, fall back to probing" logic. Single path: generate candidates → apply year filter → deduplicate → download.

6. **Keep unchanged**: argparse, `download_file()`, `dest_path()`, stats reporting, `--dry-run`, `--force`, `--year`.

**Verification**:
- `python download_fermat.py --dry-run` lists ~20 candidate PDFs and writes zero files
- `python download_fermat.py --year 2024 --dry-run` lists exactly 3 entries (e1 tasks, e2 tasks, e1 solutions)
- `python download_fermat.py --year 2024` downloads files to correct paths

---

### Task 3 — Test and Download All FerMat PDFs

**What**: Run the updated script without `--dry-run` to populate `tasks/`.

**Steps**:
1. `python download_fermat.py --dry-run` — confirm candidate list looks correct
2. `python download_fermat.py` — download all editions
3. `find tasks/ -name "tasks.pdf" | sort` — verify expected files exist
4. `find tasks/ -name "solutions.pdf" | sort` — verify only 2024/etap1 and 2025/etap1
5. Re-run `python download_fermat.py` — verify zero downloads (idempotency, SC-004)

**Expected output** (approximate):
```
tasks/2017/etap1/tasks.pdf
tasks/2018/etap1/tasks.pdf
...
tasks/2023/etap1/tasks.pdf
tasks/2024/etap1/tasks.pdf
tasks/2024/etap1/solutions.pdf
tasks/2024/etap2/tasks.pdf
tasks/2025/etap1/tasks.pdf
tasks/2025/etap1/solutions.pdf
tasks/2025/etap2/tasks.pdf
tasks/2026/etap1/tasks.pdf  (if published)

data/tasks/              # Populated by pipeline after PDFs downloaded
├── 2024/etap1/task_1.json … task_10.json
├── 2024/etap2/task_1.json … task_10.json
├── 2025/etap1/task_1.json … task_10.json
├── 2025/etap2/task_1.json … task_10.json
└── 2017…2023/etap1/task_1.json … task_10.json  (etap2 deferred — combined PDFs)
```

---

### Task 4 — Fix `create_tasks.py` and `populate_metadata.py` for FerMat

**What**: Two targeted script fixes to remove OMJ assumptions.

#### 4a — `create_tasks.py`: update task counts

```python
# Before (OMJ)
TASK_COUNTS = {
    "etap1": 7,
    "etap2": 5,
    "etap3": 5,
}

# After (FerMat)
TASK_COUNTS = {
    "etap1": 10,
    "etap2": 10,
}
```

Remove any `etap3` references from the script.

**Verification**: `python create_tasks.py 2024 etap1 --dry-run` prints "Creating 10 tasks".

#### 4b — `populate_metadata.py`: update prompt text

Three changes in `PROMPT_TEMPLATE`:

1. Replace "z Olimpiady Matematycznej Juniorów" → "z Konkursu Matematycznego FerMat"
2. Replace "OMJ to olimpiada dla klas 4-8, wiek 10-14 lat" → "FerMat to konkurs dla klas 4-6, wiek 9-12 lat"
3. Remove the etap3 difficulty guidance line: "Etap 3 zwykle ma zadania o trudności 4-5"

**Verification**: `grep -n "OMJ\|etap3" populate_metadata.py` returns no matches inside the prompt template.

---

### Task 5 — Run the Task JSON Population Pipeline

**What**: Run all pipeline scripts to generate FerMat task JSONs from the downloaded PDFs.

**Recommended order** — start with 2024/2025 (split PDFs, clean 10-task format):

```bash
# Step 1: Create stubs
python create_tasks.py 2024 etap1
python create_tasks.py 2024 etap2
python create_tasks.py 2025 etap1
python create_tasks.py 2025 etap2

# Step 2: Extract LaTeX content from PDFs (calls Claude CLI)
python fix_latex_content.py 2024 etap1
python fix_latex_content.py 2024 etap2
python fix_latex_content.py 2025 etap1
python fix_latex_content.py 2025 etap2

# Step 3: Generate metadata — difficulty, hints, skills (calls Claude CLI)
python populate_metadata.py --year 2024
python populate_metadata.py --year 2025

# Step 4: Prerequisites
python generate_task_index.py
python populate_prerequisites.py --year 2024
python populate_prerequisites.py --year 2025

# Step 5: Repeat for combined-PDF editions (etap1 only, 2017–2023)
python create_tasks.py --all --etap etap1
python fix_latex_content.py --all
python populate_metadata.py
python generate_task_index.py
python populate_prerequisites.py
```

**Verification** (SC-006, SC-007):
```bash
# Check all 2024/etap1 JSONs are fully populated
python3 -c "
import json, pathlib
for f in sorted(pathlib.Path('data/tasks/2024/etap1').glob('task_*.json')):
    t = json.loads(f.read_text())
    ok = t.get('content','') not in ('','Treść zadania do uzupełnienia.') \
         and len(t.get('hints',[])) == 4 and t.get('difficulty')
    print(f.name, '✓' if ok else '✗ INCOMPLETE')
"

# App serves 2024/etap1 tasks (requires Docker stack running)
curl -s http://localhost:8000/api/years/2024/etap1 | python3 -m json.tool | head -20
```

**Notes**:
- `fix_latex_content.py` and `populate_metadata.py` require the Claude CLI (`claude`) available in PATH with a valid session
- Combined-PDF editions (2017–2023): only etap1 JSONs are created; etap2 for those years is deferred until separate PDFs are sourced
- If a combined PDF's actual task count differs from 10, adjust stubs manually before running `fix_latex_content.py`
