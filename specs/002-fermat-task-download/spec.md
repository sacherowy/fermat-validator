# Feature Specification: Clear OMJ Data and Download FerMat Task PDFs

**Feature Branch**: `002-fermat-task-download`

**Created**: 2026-06-04

**Status**: Draft

**Input**: User description: "I need you to clear tasks folder that currently contains OMJ data, and create script to download data from Fermat list of past mathematics competition tasks. After script is created test it and download Fermat tasks."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Clear OMJ Task Data (Priority: P1)

An administrator clears all OMJ competition data so that only FerMat-relevant content remains. The OMJ data spans three locations:

- `tasks/` — OMJ PDF files (years 2005–2025, filenames like `20omj-1etap.pdf`, `omg01_1.pdf`)
- `data/tasks/` — 352 OMJ task metadata JSON files (task content, AI-generated hints, skill mappings, prerequisites); even 2024 JSONs still reference OMJ PDF paths like `tasks/2024/etap1/20omj-1etap.pdf`
- `data/task_prerequisites_analysis.md` — an OMJ-specific analysis document explicitly titled "OMJ Task Prerequisites Analysis"

**Why this priority**: All other work depends on starting from a clean slate. OMJ task JSONs surfaced in the application's task list would show wrong content to students and corrupt skill/prerequisite graphs.

**Independent Test**: Verifiable with:
- `find tasks/ -type f | wc -l` → 0
- `find data/tasks/ -type f | wc -l` → 0
- `ls data/task_prerequisites_analysis.md` → no such file

**Acceptance Scenarios**:

1. **Given** `tasks/` contains OMJ PDFs across years 2005–2025, **When** the clearing operation runs, **Then** all files and subdirectories inside `tasks/` are removed.
2. **Given** `data/tasks/` contains 352 OMJ task JSON files, **When** the clearing operation runs, **Then** all files and subdirectories inside `data/tasks/` are removed.
3. **Given** `data/task_prerequisites_analysis.md` exists, **When** the clearing operation runs, **Then** the file is deleted.
4. **Given** all three clearing steps have run, **When** a user lists their contents, **Then** no OMJ-named files or OMJ task content appears anywhere in the repository's data directories.

---

### User Story 2 - Download FerMat Task PDFs (Priority: P2)

An administrator runs the download script to populate `tasks/` with official FerMat competition PDFs sourced from `https://sp221.edu.pl/fermat/`. After downloading, the `tasks/` folder contains only FerMat task PDFs organized by year and etap.

**Why this priority**: The application cannot evaluate student submissions without the official task PDFs. This is the primary data setup step.

**Independent Test**: Can be fully tested by running `python download_fermat.py --dry-run`, confirming it lists FerMat PDFs, then running without `--dry-run` and verifying files appear in `tasks/{year}/{etap}/`.

**Acceptance Scenarios**:

1. **Given** an empty `tasks/` directory and internet access, **When** `python download_fermat.py` runs, **Then** FerMat task PDFs are saved to `tasks/{year}/{etap}/tasks.pdf` for all available editions.
2. **Given** some PDFs already downloaded, **When** the script runs again, **Then** existing files are skipped and no files are re-downloaded (idempotent behaviour).
3. **Given** `--dry-run` flag is passed, **When** the script runs, **Then** it prints a list of PDFs it would download without writing any files.
4. **Given** `--year 2024` is passed, **When** the script runs, **Then** only 2024 PDFs are downloaded.
5. **Given** a URL returns HTTP 404 (no PDF exists for that edition/etap), **When** the script encounters it, **Then** the error is logged and the script continues processing remaining URLs.

---

### User Story 3 - Verify Downloaded Content (Priority: P3)

An administrator confirms that the downloaded PDFs match the expected FerMat editions and are valid PDF files that can be served by the application.

**Why this priority**: Corrupt or misidentified files would cause silent failures during AI evaluation.

**Independent Test**: After running the download, verify `tasks/2024/etap1/tasks.pdf` exists and is a readable PDF.

**Acceptance Scenarios**:

1. **Given** the download has completed, **When** the user checks `tasks/`, **Then** each year's etap subdirectory contains at least `tasks.pdf`.
2. **Given** a downloaded file, **When** it is opened as a PDF, **Then** it is a valid, non-empty PDF document.

---

### User Story 4 - Populate FerMat Task JSON Files (Priority: P2)

An administrator runs the task-creation pipeline to produce `data/tasks/{year}/{etap}/task_N.json` files for all downloaded FerMat editions. Each JSON contains the task's LaTeX-formatted title and content (extracted from the PDF by Claude), plus AI-generated metadata: difficulty rating, mathematical categories, four progressive hints, and skill mappings.

**Why this priority**: Without task JSON files the FastAPI backend serves no tasks and the application is non-functional. PDFs alone are not enough — the frontend renders task content from JSON, not from the PDF.

**Independent Test**: After running the pipeline for 2024/etap1, verify `data/tasks/2024/etap1/task_1.json` exists, has a non-placeholder `content` field, and has `hints` with exactly 4 entries.

**Acceptance Scenarios**:

1. **Given** `tasks/2024/etap1/tasks.pdf` exists, **When** `python create_tasks.py 2024 etap1` runs, **Then** `data/tasks/2024/etap1/task_1.json` through `task_10.json` are created as stubs (10 tasks, matching `config/scoring.yml`).
2. **Given** stub JSON files exist for 2024/etap1, **When** `python fix_latex_content.py 2024 etap1` runs, **Then** each task JSON has its `title` and `content` populated with LaTeX-formatted text extracted from the PDF.
3. **Given** task JSONs with content populated, **When** `python populate_metadata.py --year 2024` runs, **Then** each task JSON gains `difficulty`, `categories`, `hints` (4 entries), `skills_required`, and `skills_gained`.
4. **Given** metadata-populated JSONs, **When** `python generate_task_index.py` then `python populate_prerequisites.py` run, **Then** each task JSON has a `prerequisites` list referencing valid task IDs.
5. **Given** a task JSON fully populated, **When** the FastAPI backend loads it, **Then** the task appears in the task list and its detail page renders correctly with LaTeX content.

**Known limitation — combined PDFs (2017–2023)**: Editions 2017–2023 have a single combined PDF (saved to `etap1/` only). The pipeline will create and populate etap1 task JSONs for those years. Etap2 task JSONs for 2017–2023 cannot be created until separate etap2 PDFs are sourced; this is acceptable for the initial migration.

---

### Edge Cases

- What happens when the sp221.edu.pl listing page is temporarily unavailable?
- What happens when no PDFs exist for a given year/etap combination (e.g., etap3 for FerMat, which does not exist)?
- What happens if the `tasks/` directory contains a mix of OMJ and FerMat files (partial migration state)?
- What is the actual task count in combined 2017–2023 PDFs — does FerMat always have 10 tasks per etap, or did older editions use a different count?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The clearing operation MUST remove all files and subdirectories from `tasks/` without deleting the `tasks/` directory itself.
- **FR-001b**: The clearing operation MUST remove all files and subdirectories from `data/tasks/` without deleting the `data/tasks/` directory itself.
- **FR-001c**: The clearing operation MUST delete `data/task_prerequisites_analysis.md` if it exists.
- **FR-002**: The download script MUST fetch FerMat task PDFs from `https://sp221.edu.pl/fermat/` and save them to `tasks/{year}/{etap}/tasks.pdf`.
- **FR-003**: The download script MUST skip files that already exist locally unless `--force` is passed.
- **FR-004**: The download script MUST support `--dry-run` mode that lists candidate PDFs without writing any files.
- **FR-005**: The download script MUST support `--year YEAR` to limit downloads to a single edition.
- **FR-006**: The download script MUST handle HTTP errors (4xx, 5xx, network timeouts) gracefully, logging the failure and continuing with remaining downloads.
- **FR-007**: The download script MUST organise downloaded files into `tasks/{year}/{etap}/` matching the layout expected by the FastAPI backend's task loading system.
- **FR-008**: The download script MUST print a summary at the end showing how many files were downloaded, skipped, and failed.
- **FR-009**: Solution PDFs, when available (editions 2024+ etap1), MUST be saved as `tasks/{year}/{etap}/solutions.pdf`.
- **FR-010**: `create_tasks.py` MUST use task counts of 10 for both etap1 and etap2 (matching `config/scoring.yml`); etap3 MUST NOT be created.
- **FR-011**: `populate_metadata.py` prompt MUST reference FerMat (not OMJ), target age range grades 4–6 (ages 9–12), and contain no etap3 difficulty guidance.
- **FR-012**: The pipeline MUST be runnable per-year so that editions can be processed incrementally (e.g. start with 2024–2025 before tackling combined-PDF editions).

### Key Entities

- **Task PDF**: An official FerMat competition PDF file. Attributes: year (e.g., 2024), etap (etap1 or etap2), type (tasks or solutions), source URL, local path.
- **Edition/Etap**: A combination of competition year and stage. FerMat has etap1 and etap2; there is no etap3.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After the clearing operation, `tasks/` contains zero files (`find tasks/ -type f | wc -l` → 0), `data/tasks/` contains zero files (`find data/tasks/ -type f | wc -l` → 0), and `data/task_prerequisites_analysis.md` does not exist.
- **SC-002**: After running the download script, at least one `tasks.pdf` file per available edition is present in `tasks/`.
- **SC-003**: The download script completes a full run in under 5 minutes for all available editions on a standard broadband connection.
- **SC-004**: Re-running the download script on an already-populated `tasks/` directory produces zero new downloads and zero errors (idempotency).
- **SC-005**: The `--dry-run` flag causes zero files to be written (verifiable by checking `tasks/` remains empty after a dry run).
- **SC-006**: After running the full pipeline for 2024/etap1 and 2024/etap2, each of the 20 task JSONs has non-empty `content`, exactly 4 `hints`, and at least one entry in `skills_required`.
- **SC-007**: The application serves 2024/etap1 tasks at `/api/years/2024/etap1` with correct task content after the pipeline completes.

## Assumptions

- `download_fermat.py` already exists in the repository root and targets `https://sp221.edu.pl/fermat/`. The script needs to be validated against the live site, not created from scratch.
- FerMat has two stages (etap1, etap2) per edition; there is no etap3.
- Solution PDFs are available only for editions 2024 and later, etap1 only (per constitution Principle V).
- The FerMat website at `https://sp221.edu.pl/fermat/` is publicly accessible without authentication.
- Years available from the FerMat website are approximately 2015–2025; earlier years (pre-2015) may not have online PDFs.
- The clearing of `tasks/`, `data/tasks/`, and `data/task_prerequisites_analysis.md` is a one-time migration action; once OMJ data is removed and FerMat data downloaded, the tasks folder is managed solely by the download script.
- `data/skills.json` contains a generic math skills taxonomy already adapted for the FerMat audience (Polish descriptions, primary-school-appropriate categories); it is NOT OMJ-specific and MUST be preserved.
- Internet access is available on the machine running the download script (outside Docker).
