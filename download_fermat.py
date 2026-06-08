#!/usr/bin/env python3
"""
download_fermat.py — Download FerMat task PDFs from sp221.edu.pl

Downloads FerMat competition PDFs using known URL patterns and saves them to
tasks/{year}/{etap}/ matching the layout expected by the FastAPI backend.
Already-downloaded files are skipped (idempotent).

URL patterns (confirmed via research):
  2017-2023: fermatYYYY.pdf          → tasks/{year}/etap1/tasks.pdf  (combined PDF)
  2024-2025: fermatYYYY-e1.pdf       → tasks/{year}/etap1/tasks.pdf
             fermatYYYY-e2.pdf       → tasks/{year}/etap2/tasks.pdf
             fermatYYYY-e1r.pdf      → tasks/{year}/etap1/solutions.pdf
  2026+:     fermatYYYY-e1.pdf / fermatYYYY-e2.pdf (split, best-effort)

Usage:
    python download_fermat.py                      # Download all editions
    python download_fermat.py --year 2024          # Download specific year
    python download_fermat.py --dry-run            # List PDFs without downloading
    python download_fermat.py --force              # Re-download existing files
    python download_fermat.py --year 2024 --force  # Force re-download for year
"""

import argparse
import sys
import urllib.request
import urllib.error
from pathlib import Path

# ── Configuration ──────────────────────────────────────────────────────────────

# Base URL where all FerMat PDFs are hosted
BASE_URL = "https://sp221.edu.pl/files/171/"

# Listing page (informational — used for reference, not scraping)
LISTING_URL = "https://sp221.edu.pl/zadania-z-poprzednich-edycji,171,pl"

# Output directory (relative to this script)
TASKS_DIR = Path(__file__).parent / "tasks"

# HTTP request timeout in seconds
REQUEST_TIMEOUT = 30

# User-agent to identify ourselves politely
USER_AGENT = "FerMat-Validator-Downloader/1.0 (educational tool; contact fermat@sp221.edu.pl)"


# ── Helpers ────────────────────────────────────────────────────────────────────

def download_file(url: str, dest: Path, force: bool = False, dry_run: bool = False) -> str:
    """Download a single file. Returns status: 'downloaded', 'skipped', or 'dry-run'."""
    if dest.exists() and not force:
        return "skipped"

    if dry_run:
        return "dry-run"

    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            content = resp.read()
        dest.write_bytes(content)
        return "downloaded"
    except (urllib.error.HTTPError, urllib.error.URLError) as e:
        return f"error: {e}"


def generate_candidates() -> list[dict]:
    """
    Build a deterministic list of PDF candidates using confirmed FerMat URL patterns.

    Pattern rules (from research.md):
      2017-2023: fermatYYYY.pdf → etap1/tasks.pdf  (combined PDF, no separate etap2)
      2024-2025: fermatYYYY-e1.pdf → etap1/tasks.pdf
                 fermatYYYY-e2.pdf → etap2/tasks.pdf
                 fermatYYYY-e1r.pdf → etap1/solutions.pdf
      2026+:     split pattern (best-effort; 404s are handled gracefully)
    """
    candidates = []
    base = BASE_URL.rstrip("/")

    # Combined-PDF years: single PDF stored as etap1/tasks.pdf
    for year in range(2017, 2024):
        candidates.append({
            "year": str(year),
            "etap": "etap1",
            "file_type": "tasks",
            "url": f"{base}/fermat{year}.pdf",
            "filename": f"fermat{year}.pdf",
        })

    # Split-PDF years: separate per-etap files + etap1 solutions
    for year in range(2024, 2026):
        candidates.append({
            "year": str(year),
            "etap": "etap1",
            "file_type": "tasks",
            "url": f"{base}/fermat{year}-e1.pdf",
            "filename": f"fermat{year}-e1.pdf",
        })
        candidates.append({
            "year": str(year),
            "etap": "etap2",
            "file_type": "tasks",
            "url": f"{base}/fermat{year}-e2.pdf",
            "filename": f"fermat{year}-e2.pdf",
        })
        candidates.append({
            "year": str(year),
            "etap": "etap1",
            "file_type": "solutions",
            "url": f"{base}/fermat{year}-e1r.pdf",
            "filename": f"fermat{year}-e1r.pdf",
        })

    # Future years (2026+): attempt split pattern; 404s are logged and skipped
    current_year = 2026
    for year in range(current_year, current_year + 1):
        candidates.append({
            "year": str(year),
            "etap": "etap1",
            "file_type": "tasks",
            "url": f"{base}/fermat{year}-e1.pdf",
            "filename": f"fermat{year}-e1.pdf",
        })
        candidates.append({
            "year": str(year),
            "etap": "etap2",
            "file_type": "tasks",
            "url": f"{base}/fermat{year}-e2.pdf",
            "filename": f"fermat{year}-e2.pdf",
        })

    return candidates


def dest_path(year: str, etap: str, file_type: str, filename: str) -> Path:
    """Return local destination path for a PDF file."""
    return TASKS_DIR / year / etap / f"{file_type}.pdf"


# ── Main logic ─────────────────────────────────────────────────────────────────

def run(
    year_filter: str | None,
    dry_run: bool,
    force: bool,
) -> int:
    """Run the downloader. Returns exit code (0 = success, 1 = one or more errors)."""
    print("FerMat PDF Downloader")
    print(f"Base URL : {BASE_URL}")
    print(f"Output   : {TASKS_DIR}")
    if dry_run:
        print("Mode     : DRY RUN (no files written)")
    if year_filter:
        print(f"Year     : {year_filter}")
    print()

    # Step 1: Build deterministic candidate list
    candidates = generate_candidates()

    # Step 2: Apply year filter
    if year_filter:
        candidates = [c for c in candidates if c["year"] == year_filter]

    # Step 3: Deduplicate by (year, etap, file_type) — first wins
    seen_keys: set[tuple] = set()
    unique: list[dict] = []
    for c in candidates:
        key = (c["year"], c["etap"], c["file_type"])
        if key not in seen_keys:
            unique.append(c)
            seen_keys.add(key)
    candidates = unique

    # Step 4: Download each candidate
    stats = {"downloaded": 0, "skipped": 0, "dry-run": 0, "error": 0}
    print(f"Processing {len(candidates)} PDF candidate(s):\n")

    for item in sorted(candidates, key=lambda x: (x["year"], x["etap"], x["file_type"])):
        dest = dest_path(item["year"], item["etap"], item["file_type"], item["filename"])
        status = download_file(item["url"], dest, force=force, dry_run=dry_run)

        icon = {
            "downloaded": "+",
            "skipped": "=",
            "dry-run": "?",
        }.get(status, "!")

        print(f"  [{icon}] {item['year']}/{item['etap']}/{item['file_type']}.pdf  ({status})")
        if status.startswith("error"):
            print(f"       URL: {item['url']}")
            stats["error"] += 1
        elif status == "downloaded":
            stats["downloaded"] += 1
        elif status == "skipped":
            stats["skipped"] += 1
        else:
            stats["dry-run"] += 1

    # Step 5: Summary
    total = sum(stats.values())
    print(f"\n{'─' * 50}")
    print(f"Summary: {total} files processed")
    if not dry_run:
        print(f"  Downloaded : {stats['downloaded']}")
        print(f"  Skipped    : {stats['skipped']} (already exist; use --force to overwrite)")
        print(f"  Errors     : {stats['error']}")
    else:
        print(f"  Would download : {stats['dry-run']}")
        print(f"  Would skip     : {stats['skipped']}")
    print()

    return 0 if stats["error"] == 0 else 1


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download FerMat competition task PDFs from sp221.edu.pl",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--year",
        metavar="YEAR",
        help="Download only this year (e.g. 2024)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List what would be downloaded without writing any files",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download files that already exist locally",
    )
    args = parser.parse_args()

    sys.exit(run(
        year_filter=args.year,
        dry_run=args.dry_run,
        force=args.force,
    ))


if __name__ == "__main__":
    main()
