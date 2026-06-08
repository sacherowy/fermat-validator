# Research: FerMat Task Download

**Phase**: 0 — Research  
**Feature**: `002-fermat-task-download`

---

## 1. Live Website Structure

**Decision**: The listing page is `https://sp221.edu.pl/zadania-z-poprzednich-edycji,171,pl` and all PDFs reside under `https://sp221.edu.pl/files/171/`.

**Rationale**: The original script targeted `https://sp221.edu.pl/fermat/` which returns 404. The actual download base is `/files/171/`. Discovered by fetching the listing page and inspecting all `href=*.pdf` links.

**Alternatives considered**: Guessing subdirectory structure under `/fermat/` — ruled out, those paths 404.

---

## 2. URL Patterns by Year

**Decision**: Two distinct patterns exist. The split year is 2024.

| Years | Pattern | Example |
|-------|---------|---------|
| 2017–2023 | `fermatYYYY.pdf` (single combined PDF, no etap separation) | `fermat2023.pdf` |
| 2024–2025 | `fermatYYYY-eN.pdf` per etap | `fermat2024-e1.pdf`, `fermat2024-e2.pdf` |
| 2026 | `fermat2026.pdf` (combined; separate etap files not yet published) | `fermat2026.pdf` |

**Rationale**: The website changed format starting with the 2024 edition to publish separate per-etap files. Earlier editions have a single combined PDF.

**How to store combined PDFs**: Since the FastAPI backend expects `tasks/{year}/{etap}/tasks.pdf`, a combined PDF for 2017–2023 should be saved to both `tasks/{year}/etap1/tasks.pdf` and `tasks/{year}/etap2/tasks.pdf` (symlink or copy), or only to `etap1/` with a note. The cleaner approach is to save the combined PDF once as `tasks/{year}/etap1/tasks.pdf` and skip etap2 for those years — the backend's `storage.py` will simply not find etap2 tasks for those years, which is acceptable since no task JSON files exist for them either.

---

## 3. Solutions Availability

**Decision**: Solutions exist only for 2024 etap1 and 2025 etap1, as `fermatYYYY-e1r.pdf`.

| Year | Etap | Solutions URL | Available |
|------|------|--------------|-----------|
| 2024 | etap1 | `fermat2024-e1r.pdf` | ✅ HTTP 200 |
| 2025 | etap1 | `fermat2025-e1r.pdf` | ✅ HTTP 200 |
| All others | any | — | ❌ 404 |

**Rationale**: Confirmed by HTTP HEAD probing. Aligns with constitution Principle V.

---

## 4. OMJ Artifacts to Remove

**Decision**: Three locations contain OMJ data, all must be cleared:

| Location | What | Why remove |
|---|---|---|
| `tasks/*/` | ~80 OMJ PDFs (years 2005–2025) | Wrong competition's source PDFs |
| `data/tasks/*/` | 352 task JSON files (OMJ task content, hints, skills, prerequisites) | Even 2024 JSONs reference OMJ PDF paths (e.g. `20omj-1etap.pdf`); served directly to students by FastAPI |
| `data/task_prerequisites_analysis.md` | OMJ prerequisites analysis doc | Explicitly titled "OMJ Task Prerequisites Analysis"; no FerMat relevance |

**Decision**: `data/skills.json` is **NOT** OMJ-specific — it contains a generic math skills taxonomy (43 skills, 6 categories) with Polish descriptions written for primary-school students. Keep as-is.

**Commands**:
```bash
rm -rf tasks/*/
rm -rf data/tasks/*/
rm -f data/task_prerequisites_analysis.md
```

**Rationale**: `rm -rf dir/*/` removes all year subdirectories while leaving the parent directory intact (satisfies FR-001/FR-001b). Selective filename-pattern matching is fragile and unnecessary since we want a complete clean slate.

**Alternatives considered**: Selective deletion matching `*omj*`/`*omg*` patterns — rejected; the `data/tasks/` JSON files don't follow OMJ naming conventions so pattern-matching would miss them entirely.

---

## 5. Script Architecture Approach

**Decision**: Update `download_fermat.py` in-place rather than creating a new script.

**Rationale**: The spec assumes the script already exists (`Assumptions` section). The existing structure (argparse, `run()` / `main()` split, URL probing, stats reporting) is sound. Only the URL logic needs replacement.

**Key changes needed**:
1. Replace `BASE_URL` and URL generation with known patterns.
2. Add `LISTING_URL` = the sp221.edu.pl listing page.
3. For 2024–2025: emit two task candidates (`-e1.pdf`, `-e2.pdf`) plus solution candidate (`-e1r.pdf`).
4. For 2017–2023: emit one task candidate (`fermatYYYY.pdf`), save to `etap1/tasks.pdf`.
5. For 2026+: try both combined (`fermat2026.pdf`) and split (`fermat2026-e1.pdf`) patterns.
6. Remove `discover_pdf_links` HTML scraping fallback — use known URL list as primary source; optionally scrape as supplementary discovery for future years.
7. Remove `probe_url` slow fallback; use `generate_expected_urls` that returns only known-good patterns.

---

## 6. Handling Combined PDFs for 2017–2023

**Decision**: Save combined PDFs only to `tasks/{year}/etap1/tasks.pdf`. Do not create duplicate etap2 entries.

**Rationale**: The backend scans `data/tasks/{year}/{etap}/` for JSON task files. PDFs without corresponding JSON are not served. Adding empty etap2 PDF entries for combined-PDF years would create phantom etaps with no tasks. Etap1-only storage is the least-surprise default.

**Alternative considered**: Copy to both etap1 and etap2 — rejected (would show etap2 with no tasks in the UI once task JSON is added).

---

## 7. Year Range

**Decision**: Script covers 2017–2026. Years before 2017 are excluded.

**Rationale**: The FerMat competition started in 2017 (edition I). The website does not list earlier editions. The existing OMJ data in `tasks/2005`–`tasks/2016` is OMJ-origin and unrelated to FerMat.

---

## 8. Clearing OMJ Data

**Decision**: Implement clearing as a standalone shell operation, not as a flag in `download_fermat.py`.

**Rationale**: FR-001 says the clearing operation must remove all files and subdirectories from `tasks/`. Embedding `--clear` in the download script conflates two distinct operations. The administrator can run `rm -rf tasks/*/` directly. The spec's User Story 1 is a one-time migration, not a recurring script feature. Document the command in the plan rather than encoding it in the script.

**Alternative considered**: `--clear` flag in script — rejected for simplicity.
