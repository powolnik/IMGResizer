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
import argparse
import shutil

from PIL import Image


SUPPORTED_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}


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


def find_target_aspect(img_paths: Iterable[Path]) -> float:
    """
    Return the aspect ratio (width / height) of the first landscape image.

    Raises RuntimeError if no landscape image is found.
    """
    for path in img_paths:
        with Image.open(path) as im:
            w, h = im.size
            if w >= h:  # landscape
                return w / h
    raise RuntimeError(
        "No landscape images found – specify an aspect ratio manually."
    )


def pad_portrait(src: Path, ratio: float, dest: Path) -> None:
    """
    Write *src* to *dest* so the result matches the supplied aspect *ratio*.

    • Portrait images receive black bars left/right.  
    • Landscape images are copied unchanged.
    """
    with Image.open(src) as im:
        w, h = im.size

        # Landscape – copy as-is
        if w >= h:
            im.save(dest)
            return

        # Portrait – build a new canvas
        new_w = int(round(h * ratio))
        pad_left = (new_w - w) // 2

        # Use an RGB black background regardless of original mode
        background = (0, 0, 0)
        canvas_mode = "RGB" if im.mode in ("RGB", "RGBA") else im.mode
        new_im = Image.new(canvas_mode, (new_w, h), background)
        new_im.paste(im, (pad_left, 0))

        # Preserve transparency if source had an alpha channel
        if im.mode == "RGBA":
            new_im = new_im.convert("RGBA")

        new_im.save(dest)


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
        "-r",
        "--ratio",
        type=float,
        help="Override the detected target aspect-ratio (implies --yes).",
    )
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Run without the interactive confirmation prompt.",
    )
    args = parser.parse_args()
    non_interactive = args.yes or args.ratio is not None

    project_root = Path(__file__).resolve().parent
    folder = project_root / "img"
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

    detected_ratio = find_target_aspect(images)

    # -------------------- analysis report -----------------------------
    n_landscape = 0
    for p in images:
        with Image.open(p) as im:
            if im.size[0] >= im.size[1]:
                n_landscape += 1
    n_portrait = len(images) - n_landscape

    print(
        "Analysis:\n"
        f"  total files   : {len(images)}\n"
        f"  landscape     : {n_landscape}\n"
        f"  portrait      : {n_portrait}\n"
        f"  target ratio  : {detected_ratio:.3f}"
    )

    # Decide which ratio to use
    ratio = args.ratio if args.ratio is not None else detected_ratio

    if not non_interactive:
        custom = input(
            f"\nEnter aspect ratio to use "
            f"[press Enter to accept {ratio:.3f}]: "
        ).strip()
        if custom:
            try:
                ratio = float(custom)
            except ValueError:
                print("Invalid number – keeping previous value.")

        confirm = input("Proceed with padding? [y/N] ").strip().lower()
        if confirm != "y":
            print("Aborted by user.")
            return

    # Fresh output directory every run
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for img_path in images:
        dest_path = out_dir / img_path.name
        pad_portrait(img_path, ratio, dest_path)

    print(f"Finished. Results saved to: {out_dir}")


if __name__ == "__main__":
    main()
