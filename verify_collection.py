#!/usr/bin/env python3
"""
verify_collection.py

Check that every image file found under img/ has a counterpart (same
filename) inside collection/.

Exit status:
    0 – everything present
    1 – at least one file missing
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable

# ---------------------------------------------------------------------------
# Re-use the same SUPPORTED_SUFFIXES and iter_images() logic as pad_portraits.
# (Duplicated here for self-containment.)
# ---------------------------------------------------------------------------
SUPPORTED_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}


def iter_images(folder: Path) -> Iterable[Path]:
    for p in folder.rglob("*"):
        if (
            p.is_file()
            and p.suffix.lower() in SUPPORTED_SUFFIXES
            and "padded" not in p.parts
            and "collection" not in p.parts
        ):
            yield p


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Verify collection against original images")
    parser.add_argument("--input", type=str, default=None, help="Folder with original images (default is img/)")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    src_dir = Path(args.input) if args.input else root / "img"
    dst_dir = root / "collection"

    if not src_dir.is_dir():
        sys.exit("No img/ directory – nothing to check.")
    if not dst_dir.is_dir():
        sys.exit("No collection/ directory – run pad_portraits.py first.")

    sources = list(iter_images(src_dir))
    dest_files = [p for p in dst_dir.iterdir() if p.is_file()]

    print(
        f"Verification report\n"
        f"  originals : {len(sources)}\n"
        f"  in output : {len(dest_files)}\n"
    )

    if len(sources) != len(dest_files):
        print("\nMismatch in file counts between img/ and collection/")
        sys.exit(1)

    print("\nAll files are present.")
    sys.exit(0)


if __name__ == "__main__":
    main()
