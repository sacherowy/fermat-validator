# Data Model: FerMat Task Download

**Feature**: `002-fermat-task-download`

---

## Entities

### PdfCandidate

Represents a single downloadable PDF file before it is fetched.

| Field | Type | Description |
|-------|------|-------------|
| `year` | `str` | 4-digit year, e.g. `"2024"` |
| `etap` | `str` | `"etap1"` or `"etap2"` |
| `file_type` | `str` | `"tasks"` or `"solutions"` |
| `url` | `str` | Full URL to the PDF on sp221.edu.pl |
| `filename` | `str` | Bare filename, e.g. `"fermat2024-e1.pdf"` |

**Key**: `(year, etap, file_type)` — unique per candidate set; duplicates are deduplicated (first wins).

**Validation rules**:
- `file_type == "solutions"` is only valid when `year in ("2024", "2025") AND etap == "etap1"` (constitution Principle V).
- `etap` is always `"etap1"` for years 2017–2023 (combined PDF years have no etap2 variant).

---

### DownloadResult

Represents the outcome of attempting to download one `PdfCandidate`.

| Field | Type | Values |
|-------|------|--------|
| `candidate` | `PdfCandidate` | The attempted candidate |
| `status` | `str` | `"downloaded"`, `"skipped"`, `"dry-run"`, `"error: <msg>"` |
| `local_path` | `Path \| None` | Resolved destination path; `None` if dry-run or error |

---

### DownloadStats

Aggregated run summary.

| Field | Type | Description |
|-------|------|-------------|
| `downloaded` | `int` | Files newly written |
| `skipped` | `int` | Files already present (no `--force`) |
| `dry_run` | `int` | Files that would have been downloaded |
| `error` | `int` | Failed downloads |

**Exit code**: `0` if `error == 0`, else `1`.

---

## URL Pattern Rules (deterministic, no probing)

```
Base: https://sp221.edu.pl/files/171/

Years 2017–2023 (combined PDF, etap1 only):
  tasks.pdf  ← fermatYYYY.pdf           → tasks/YYYY/etap1/tasks.pdf

Years 2024–2025 (split per etap + solutions for etap1):
  tasks.pdf  ← fermatYYYY-e1.pdf        → tasks/YYYY/etap1/tasks.pdf
  tasks.pdf  ← fermatYYYY-e2.pdf        → tasks/YYYY/etap2/tasks.pdf
  solutions  ← fermatYYYY-e1r.pdf       → tasks/YYYY/etap1/solutions.pdf

Year 2026 (try split first, fall back to combined):
  tasks.pdf  ← fermat2026-e1.pdf or fermat2026.pdf → tasks/2026/etap1/tasks.pdf
  tasks.pdf  ← fermat2026-e2.pdf (if exists)       → tasks/2026/etap2/tasks.pdf
```

---

## Filesystem Layout (post-download)

```text
tasks/
├── 2017/etap1/tasks.pdf
├── 2018/etap1/tasks.pdf
├── 2019/etap1/tasks.pdf
├── 2020/etap1/tasks.pdf
├── 2021/etap1/tasks.pdf
├── 2022/etap1/tasks.pdf
├── 2023/etap1/tasks.pdf
├── 2024/
│   ├── etap1/
│   │   ├── tasks.pdf
│   │   └── solutions.pdf
│   └── etap2/
│       └── tasks.pdf
├── 2025/
│   ├── etap1/
│   │   ├── tasks.pdf
│   │   └── solutions.pdf
│   └── etap2/
│       └── tasks.pdf
└── 2026/
    └── etap1/
        └── tasks.pdf   (if published by run time)
```

No database changes. No new Python packages.
