# CLI Contract: download_fermat.py

**Feature**: `002-fermat-task-download`

---

## Invocation

```
python download_fermat.py [OPTIONS]
```

Run from the repository root (outside Docker). Requires internet access and Python 3.11+. No third-party packages.

---

## Options

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--year YEAR` | `str` | (all years) | Download only this edition, e.g. `2024` |
| `--dry-run` | flag | off | Print candidates without writing files |
| `--force` | flag | off | Re-download files that already exist locally |

---

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | All attempted downloads succeeded (or were skipped/dry-run) |
| `1` | One or more HTTP errors occurred during download |

---

## Stdout Contract

### Header block (always printed)

```
FerMat PDF Downloader
Base URL : https://sp221.edu.pl/files/171/
Output   : /path/to/tasks
[Mode     : DRY RUN (no files written)]   ← only when --dry-run
[Year     : YYYY]                          ← only when --year passed
```

### Per-file line

```
  [+] 2024/etap1/tasks.pdf  (downloaded)
  [=] 2024/etap1/tasks.pdf  (skipped)
  [?] 2024/etap1/tasks.pdf  (dry-run)
  [!] 2024/etap1/tasks.pdf  (error: HTTP 404 ...)
       URL: https://sp221.edu.pl/files/171/fermat2024-e1.pdf   ← only on error
```

Icon key: `+` = downloaded, `=` = skipped, `?` = dry-run, `!` = error.

### Summary block (always printed)

```
──────────────────────────────────────────────────
Summary: N files processed
  Downloaded : N
  Skipped    : N (already exist; use --force to overwrite)
  Errors     : N
```

In `--dry-run` mode:
```
  Would download : N
  Would skip     : N
```

---

## Filesystem Side Effects

- Files are written only when `--dry-run` is **not** set.
- Destination layout: `tasks/{year}/{etap}/{file_type}.pdf`
  - `file_type` is `tasks` or `solutions`
- Parent directories are created automatically (`mkdir -p` behaviour).
- Existing files are **not** overwritten unless `--force` is passed.
- `tasks/` directory itself is never deleted or recreated.

---

## Guarantees

- **Idempotent**: re-running on an already-populated directory produces zero downloads and exit code 0.
- **Graceful on 404**: a missing PDF logs an error line and continues; other files still download.
- **No writes on dry-run**: `tasks/` is not modified in any way when `--dry-run` is active.
- **Year-scoped**: `--year YYYY` limits both download and dry-run output to that edition only.

---

## Examples

```bash
# Full download (all editions, 2017–2026)
python download_fermat.py

# Preview what would be downloaded
python download_fermat.py --dry-run

# Download only 2024 edition
python download_fermat.py --year 2024

# Re-download 2024 even if files exist
python download_fermat.py --year 2024 --force

# Clear OMJ data before first download (one-time migration)
rm -rf tasks/*/
python download_fermat.py
```
