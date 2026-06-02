#!/usr/bin/env python3
"""
download_fermat.py — Download FerMat task PDFs from sp221.edu.pl

Fetches the FerMat task listing page, discovers PDF links per edition/etap,
and downloads to tasks/{year}/{etap}/ (mirroring the existing directory layout).
Already-downloaded files are skipped (idempotent).

Usage:
    python download_fermat.py                      # Download all editions
    python download_fermat.py --year 2024          # Download specific year
    python download_fermat.py --dry-run            # List PDFs without downloading
    python download_fermat.py --force              # Re-download existing files
    python download_fermat.py --year 2024 --force  # Force re-download for year
"""

import argparse
import re
import sys
import urllib.request
import urllib.error
from pathlib import Path
from urllib.parse import urljoin, urlparse

# ── Configuration ──────────────────────────────────────────────────────────────

# Base URL for FerMat task listing.
# The listing page is expected to have links to PDF files organised by year/etap.
BASE_URL = "https://sp221.edu.pl/fermat/"

# Output directory (relative to this script)
TASKS_DIR = Path(__file__).parent / "tasks"

# HTTP request timeout in seconds
REQUEST_TIMEOUT = 30

# Known file names per etap (in order of preference)
ETAP_FILE_NAMES = {
    "etap1": ["zadania.pdf", "tasks.pdf", "etap1.pdf"],
    "etap2": ["zadania.pdf", "tasks.pdf", "etap2.pdf"],
}
SOLUTION_FILE_NAMES = ["rozwiazania.pdf", "solutions.pdf"]

# User-agent to identify ourselves politely
USER_AGENT = "FerMat-Validator-Downloader/1.0 (educational tool; contact fermat@sp221.edu.pl)"


# ── Helpers ────────────────────────────────────────────────────────────────────

def fetch_html(url: str) -> str:
    """Fetch HTML content from URL."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            charset = resp.headers.get_content_charset("utf-8")
            return resp.read().decode(charset)
    except urllib.error.HTTPError as e:
        print(f"  HTTP {e.code} fetching {url}: {e.reason}")
        raise
    except urllib.error.URLError as e:
        print(f"  Network error fetching {url}: {e.reason}")
        raise


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


def discover_pdf_links(html: str, base_url: str) -> list[dict]:
    """
    Parse HTML and extract PDF links grouped by year and etap.

    Expected HTML structure (heuristic — adjust if sp221.edu.pl changes format):
    Links containing year patterns like 2024, 2023, ... and
    file names matching etap1/etap2 patterns.

    Returns list of dicts: [{year, etap, url, filename}, ...]
    """
    # Find all href links to PDF files
    pdf_links = re.findall(r'href=["\']([^"\']*\.pdf)["\']', html, re.IGNORECASE)
    results = []

    for link in pdf_links:
        full_url = urljoin(base_url, link)
        parsed = urlparse(full_url)
        path_parts = parsed.path.lower().split("/")
        filename = path_parts[-1] if path_parts else ""

        # Try to extract year from path or filename
        year_match = re.search(r"(20\d{2})", full_url)
        if not year_match:
            continue
        year = year_match.group(1)

        # Determine etap from path or filename
        etap = None
        path_str = full_url.lower()
        if "etap2" in path_str or "etap_2" in path_str or "ii" in path_str:
            etap = "etap2"
        elif "etap1" in path_str or "etap_1" in path_str or "etap-1" in path_str:
            etap = "etap1"
        else:
            # Default to etap1 if we cannot determine
            etap = "etap1"

        # Determine file type
        is_solution = any(s in filename for s in ["rozwiaz", "solution", "answer"])
        file_type = "solutions" if is_solution else "tasks"

        results.append({
            "year": year,
            "etap": etap,
            "file_type": file_type,
            "url": full_url,
            "filename": filename,
        })

    return results


def generate_expected_urls(base_url: str) -> list[dict]:
    """
    Generate expected PDF URLs using the known FerMat URL structure.

    Since sp221.edu.pl's exact structure is not yet known, this function
    generates candidate URLs based on common patterns. Unknown URLs will
    produce HTTP 404 and be skipped gracefully.

    Known pattern (example): https://sp221.edu.pl/fermat/2024/etap1/zadania.pdf
    """
    # Editions known to exist (conservative estimate — expand as more are confirmed)
    # FerMat started approximately 2015; extend as needed
    known_years = list(range(2015, 2026))
    etaps = ["etap1", "etap2"]
    pdf_variants = {
        "tasks": ["zadania.pdf", "tasks.pdf"],
        "solutions": ["rozwiazania.pdf", "solutions.pdf"],
    }

    candidates = []
    for year in known_years:
        for etap in etaps:
            for file_type, filenames in pdf_variants.items():
                for filename in filenames:
                    candidates.append({
                        "year": str(year),
                        "etap": etap,
                        "file_type": file_type,
                        "url": f"{base_url.rstrip('/')}/{year}/{etap}/{filename}",
                        "filename": filename,
                    })
    return candidates


def probe_url(url: str) -> bool:
    """Return True if URL responds with HTTP 200."""
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            return resp.status == 200
    except Exception:
        return False


def dest_path(year: str, etap: str, file_type: str, filename: str) -> Path:
    """Return local destination path for a PDF file."""
    return TASKS_DIR / year / etap / f"{file_type}.pdf"


# ── Main logic ─────────────────────────────────────────────────────────────────

def run(
    year_filter: str | None,
    dry_run: bool,
    force: bool,
) -> int:
    """Run the downloader. Returns exit code (0 = success)."""
    print(f"FerMat PDF Downloader")
    print(f"Base URL : {BASE_URL}")
    print(f"Output   : {TASKS_DIR}")
    if dry_run:
        print("Mode     : DRY RUN (no files written)")
    if year_filter:
        print(f"Year     : {year_filter}")
    print()

    # Step 1: Try to fetch and parse the listing page
    discovered: list[dict] = []
    try:
        print(f"Fetching listing page: {BASE_URL}")
        html = fetch_html(BASE_URL)
        discovered = discover_pdf_links(html, BASE_URL)
        print(f"  Discovered {len(discovered)} PDF links from listing page.")
    except Exception:
        print("  Could not fetch listing page. Falling back to URL pattern probing.")
        discovered = []

    # Step 2: If discovery failed or found nothing, fall back to URL probing
    if not discovered:
        print("Probing candidate URLs (this may take a moment)...")
        candidates = generate_expected_urls(BASE_URL)
        if year_filter:
            candidates = [c for c in candidates if c["year"] == year_filter]

        # Probe in order; stop on first hit per (year, etap, file_type) combination
        seen: set[tuple] = set()
        for c in candidates:
            key = (c["year"], c["etap"], c["file_type"])
            if key in seen:
                continue
            if probe_url(c["url"]):
                discovered.append(c)
                seen.add(key)
                print(f"  Found: {c['url']}")

    # Step 3: Apply year filter
    if year_filter:
        discovered = [d for d in discovered if d["year"] == year_filter]

    if not discovered:
        if year_filter:
            print(f"No PDFs found for year {year_filter}.")
        else:
            print("No PDFs found. Check that sp221.edu.pl is reachable and the URL structure matches.")
        return 1

    # Step 4: Deduplicate (prefer first occurrence per key)
    seen_keys: set[tuple] = set()
    unique: list[dict] = []
    for d in discovered:
        key = (d["year"], d["etap"], d["file_type"])
        if key not in seen_keys:
            unique.append(d)
            seen_keys.add(key)
    discovered = unique

    # Step 5: Download
    stats = {"downloaded": 0, "skipped": 0, "dry-run": 0, "error": 0}
    print(f"\nProcessing {len(discovered)} PDF(s):\n")

    for item in sorted(discovered, key=lambda x: (x["year"], x["etap"], x["file_type"])):
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

    # Step 6: Summary
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
