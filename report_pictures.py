#!/usr/bin/env python3
"""
report_pictures.py

Print a frequency table of the aspect-ratios found in a folder
(default: ./collection).

Usage examples
--------------
    python report_pictures.py                 # scan ./collection
    python report_pictures.py out -p 2        # scan ./out, round to 2 decimals
"""
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Iterable

from PIL import Image

SUPPORTED_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}


def iter_images(folder: Path) -> Iterable[Path]:
    for p in folder.iterdir():
        if p.is_file() and p.suffix.lower() in SUPPORTED_SUFFIXES:
            yield p


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Report aspect-ratio distribution for images in a folder"
    )
    parser.add_argument("folder", nargs="?", default="collection", help="Folder to scan")
    parser.add_argument(
        "-p",
        "--precision",
        type=int,
        default=3,
        help="Decimal places to keep when grouping ratios (default: 3)",
    )
    args = parser.parse_args()

    root = Path(args.folder).resolve()
    if not root.is_dir():
        raise SystemExit(f"Directory not found: {root}")

    ratios: Counter[float] = Counter()

    for img_path in iter_images(root):
        with Image.open(img_path) as im:
            w, h = im.size
            ratios[round(w / h, args.precision)] += 1

    if not ratios:
        print("No images found.")
        return

    print(f"Aspect-ratio distribution in {root}:")
    for ratio, count in ratios.most_common():
        print(f"  {ratio:.{args.precision}f} : {count}")


if __name__ == "__main__":
    main()
