#!/usr/bin/env python3
"""
pad_portraits.py

Batch-process a folder of mixed-orientation images so they all end up with the
same outer aspect-ratio.  The script:

1. Determines the target aspect-ratio from the first landscape (width ≥ height)
   image it finds in the input folder.
2. For every portrait image, creates a new image with black bars on the
   left/right so that  new_width = height × target_ratio.
3. Copies landscape images unchanged (comment the relevant line if you do not
   want them duplicated).
4. Writes all results to `<input>/padded/`.

Usage
-----
    python pad_portraits.py [folder_with_images]
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable
from collections import Counter
from datetime import datetime
import argparse
import shutil
import re

from PIL import Image


SUPPORTED_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}

# ---------------------------------------------------------------------------
# Naming helpers
# ---------------------------------------------------------------------------
# Capture a YYYY-MM-DD sequence inside a filename.
_DATE_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")


def date_for_file(path: Path) -> str:
    """
    Return a date string 'YYYY-MM-DD' for *path*.

    1. If the filename already contains a valid date sequence, use it.
    2. Otherwise fall back to the file's modification timestamp.
    """
    m = _DATE_RE.search(path.stem)
    if m:
        return f"{m[1]}-{m[2]}-{m[3]}"
    return datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d")


def iter_images(folder: Path) -> Iterable[Path]:
    """
    Recursively yield image files inside *folder* whose extension is supported.

    Files that already live inside a directory named ``padded`` are skipped to
    avoid re-processing previous outputs.
    """
    for p in folder.rglob("*"):
        if (
            p.is_file()
            and p.suffix.lower() in SUPPORTED_SUFFIXES
            and "padded" not in p.parts
            and "collection" not in p.parts
        ):
            yield p


def most_common_aspect(
    img_paths: Iterable[Path], *, precision: int = 3
) -> float:
    """
    Return the most frequently occurring landscape aspect ratio.

    Ratios are rounded to *precision* decimal places so that files with the
    same shape but different resolutions collapse onto a single value
    (e.g. 6000×4000 and 3000×2000 → 1.500).

    Raises RuntimeError if no landscape images are found.
    """
    counts: Counter[float] = Counter()

    for path in img_paths:
        with Image.open(path) as im:
            w, h = im.size
            if w >= h:  # landscape
                counts[round(w / h, precision)] += 1

    if not counts:
        raise RuntimeError(
            "No landscape images found – specify an aspect ratio manually."
        )

    # Counter.most_common(1) → [(ratio, count)]
    return counts.most_common(1)[0][0]


def pad_portrait(src: Path, dest: Path) -> None:
    """
    Write *src* to *dest* so that the final image fits within a 1024x768 (4:3) frame.
    If the source image has a resolution greater than 1024x768, it is downscaled;
    otherwise, it is centered without upscaling. A black background is used for padding.
    """
    target_w, target_h = 1024, 768
    with Image.open(src) as im:
        w, h = im.size

        # Determine scaling factor (only downscale, do not upscale)
        scale_factor = min(1, target_w / w, target_h / h)
        new_w = int(w * scale_factor)
        new_h = int(h * scale_factor)
        resized_im = im.resize((new_w, new_h), resample=Image.Resampling.LANCZOS)

        # Create a new canvas with target dimensions and black background
        canvas_mode = "RGB" if im.mode in ("RGB", "RGBA") else im.mode
        canvas = Image.new(canvas_mode, (target_w, target_h), (0, 0, 0))
        paste_x = (target_w - new_w) // 2
        paste_y = (target_h - new_h) // 2
        canvas.paste(resized_im, (paste_x, paste_y))

        # Preserve alpha channel if necessary
        if im.mode == "RGBA":
            canvas = canvas.convert("RGBA")

        canvas.save(dest)


def main() -> None:
    # ------------------------------------------------------------------
    # Command-line interface
    # ------------------------------------------------------------------
    parser = argparse.ArgumentParser(
        description=(
            "Pad portrait photos with black sidebars so every file shares the "
            "same outer landscape aspect-ratio."
        )
    )
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Run without the interactive confirmation prompt.",
    )
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Folder with images (default is <script_dir>/img)"
    )
    args = parser.parse_args()
    non_interactive = args.yes or args.ratio is not None

    project_root = Path(__file__).resolve().parent
    folder = Path(args.input) if args.input else project_root / "img"
    out_dir = project_root / "collection"

    if not folder.is_dir():
        # Create the expected input directory on first run so users don’t have
        # to create it manually, then instruct them to add images.
        folder.mkdir(parents=True, exist_ok=True)
        print(
            f"Created empty input folder:\n  {folder}\n"
            "Add images to that directory and run the script again."
        )
        return

    images = list(iter_images(folder))
    if not images:
        sys.exit("No supported images found in the specified folder.")


    if not non_interactive:
        confirm = input("Proceed with padding? [y/N] ").strip().lower()
        if confirm != "y":
            print("Aborted by user.")
            return

    # Fresh output directory every run
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Save every processed file to collection/ with a sequential name: 0001-YYYY-MM-DD.ext
    for idx, img_path in enumerate(sorted(images), start=1):
        date_str = date_for_file(img_path)
        dest_path = out_dir / f"{idx:04d}-{date_str}{img_path.suffix.lower()}"
        pad_portrait(img_path, dest_path)

    # ------------------------------------------------------------------
    # Final report: aspect-ratio distribution for the new collection.
    # ------------------------------------------------------------------
    ratios: Counter[float] = Counter()
    for p in out_dir.iterdir():
        with Image.open(p) as im:
            w, h = im.size
            ratios[round(w / h, 3)] += 1

    print(f"\nFinished. Results saved to: {out_dir}\n")
    print("Aspect-ratio distribution in collection/:")
    for r, cnt in ratios.most_common():
        print(f"  {r:.3f} : {cnt}")


if __name__ == "__main__":
    main()
