#!/usr/bin/env python3
"""
rename_whatsapp.py

Rename images downloaded from WhatsApp so they have a clean
ISO-like timestamp name instead of the verbose default, e.g.

    "WhatsApp Image 2024-05-10 at 14.53.22.jpeg"
→   "2024-05-10_14-53-22.jpeg"

Files that do not match the WhatsApp naming pattern are left untouched.

CLI
---
    python rename_whatsapp.py [-n] [-f] [folder]

Options
-------
    folder            Directory to scan recursively (default: ./img)
    -n, --dry-run     Show the operations that would be performed
                      without actually renaming anything.
    -f, --force       Overwrite destination files if they already exist.

Exit status
-----------
    0  All went fine
    1  Provided folder does not exist
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# Capture any date in the form YYYY-MM-DD appearing in the filename
# (works for both original WhatsApp names and those already normalised).
_DATE_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")


def extract_date(stem: str) -> str | None:
    """
    Return a date string 'YYYY-MM-DD' extracted from *stem* or None
    if no valid date is found.
    """
    m = _DATE_RE.search(stem)
    if not m:
        return None
    try:
        dt = datetime(int(m[1]), int(m[2]), int(m[3]))
    except ValueError:
        return None
    return dt.strftime("%Y-%m-%d")


def _deduplicated_path(path: Path) -> Path:
    """
    Return a variant of *path* that does not clash with an existing file
    by appending '_1', '_2', … before the extension.
    """
    stem, suffix = path.stem, path.suffix.lower()
    counter = 1
    candidate = path
    while candidate.exists():
        candidate = path.with_name(f"{stem}_{counter}{suffix}")
        counter += 1
    return candidate


def rename_file(
    path: Path,
    new_path: Path,
    *,
    dry_run: bool,
    force: bool,
) -> bool:
    """
    Rename *path* to *new_path*.

    Returns True if a rename (or dry-run rename) was performed, False when the
    destination already exists and --force was not supplied.
    """
    exists = new_path.exists()

    # Skip when destination already exists unless --force is supplied
    if exists and not force:
        print(f"SKIP   (exists) {path.name} → {new_path.name}")
        return False

    if dry_run:
        print(f"DRYRUN        {path.name} → {new_path.name}")
        return True

    if exists and force:
        new_path.unlink()  # replace existing file
    path.rename(new_path)
    print(f"RENAME        {path.name} → {new_path.name}")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Rename WhatsApp image files.")
    parser.add_argument(
        "folder",
        nargs="?",
        default="img",
        help="Folder to process (default: ./img)",
    )
    parser.add_argument("-n", "--dry-run", action="store_true", help="Dry-run mode")
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Overwrite if the target filename already exists",
    )
    args = parser.parse_args()

    root = Path(args.folder).resolve()
    if not root.is_dir():
        sys.exit("Folder not found: {root}")

    renamed = 0
    skipped = 0

    # Progressive counter for each date
    next_index: dict[str, int] = defaultdict(lambda: 1)

    for path in root.rglob("*"):
        if not path.is_file():
            continue

        date_str = extract_date(path.stem)
        if date_str is None:
            skipped += 1
            continue

        idx = next_index[date_str]
        next_index[date_str] += 1

        new_name = f"{date_str}_{idx:04d}{path.suffix.lower()}"

        if rename_file(
            path,
            path.with_name(new_name),
            dry_run=args.dry_run,
            force=True,  # always overwrite if the name already exists
        ):
            renamed += 1

    print(
        f"\nDone. Renamed: {renamed}, left unchanged (non-WhatsApp): {skipped}"
    )


if __name__ == "__main__":
    main()
