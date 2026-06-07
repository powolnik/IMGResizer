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

# Accept optional trailing junk (letters, spaces, symbols) after the seconds
# so names like "...20.42.37mbj.jpeg" are still recognised.
_PATTERN = re.compile(
    r"^whatsapp image (\d{4})-(\d{2})-(\d{2}) at "
    r"(\d{2})\.(\d{2})\.(\d{2})(?:\D.*)?$",
    re.IGNORECASE,
)


def desired_name(stem: str, suffix: str) -> str | None:
    """
    Return the new filename (without path) or None if *stem* does not match the
    WhatsApp pattern.
    """
    m = _PATTERN.match(stem)
    if not m:
        return None

    y, mo, d, hh, mm, ss = (int(x) for x in m.groups())
    ts = datetime(y, mo, d, hh, mm, ss)
    return ts.strftime("%Y-%m-%d_%H-%M-%S") + suffix.lower()


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

    for path in root.rglob("*"):
        if not path.is_file():
            continue

        new_name = desired_name(path.stem, path.suffix)
        if new_name is None:
            skipped += 1
            continue

        if rename_file(
            path,
            path.with_name(new_name),
            dry_run=args.dry_run,
            force=args.force,
        ):
            renamed += 1
        else:
            skipped += 1

    print(
        f"\nDone. Renamed: {renamed}, left unchanged (non-WhatsApp): {skipped}"
    )


if __name__ == "__main__":
    main()
