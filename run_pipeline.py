#!/usr/bin/env python3
"""
run_pipeline.py

Run the full image-processing workflow in three simple steps:

    1. rename_whatsapp.py      – normalise WhatsApp filenames
    2. pad_portraits.py --yes  – add side-bars / copy images to collection/
    3. verify_collection.py    – be sure every original has a counterpart

If any command exits with a non-zero status the pipeline stops and propagates
that same exit-code.

CLI
---
    python run_pipeline.py [options]

Options
-------
    --dry-rename       run rename_whatsapp.py with -n (no changes)
    --force-rename     pass -f to rename_whatsapp.py (overwrite clashes)
    --ratio R          forward -r R to pad_portraits.py (aspect override)
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def run(cmd: list[str]) -> None:
    """Run *cmd* and abort the pipeline if its exit-code is non-zero."""
    print("\n»", " ".join(cmd))
    rc = subprocess.call(cmd)
    if rc != 0:
        sys.exit(rc)


def main() -> None:
    parser = argparse.ArgumentParser(description="Full image processing pipeline")
    parser.add_argument("--dry-rename", action="store_true", help="Dry-run for renaming")
    parser.add_argument("--force-rename", action="store_true", help="Overwrite on rename clashes")
    parser.add_argument("--ratio", type=float, help="Aspect-ratio to pass to pad_portraits.py")
    parser.add_argument("--input", type=str, default=None, help="Folder with original images (default is img/)")
    args = parser.parse_args()

    # ---------------------------------------------------------------
    # 1. rename_whatsapp.py (dry-run mode to preserve originals in img)
    # ---------------------------------------------------------------
    ren_cmd = [sys.executable, str(ROOT / "rename_whatsapp.py"), "-n"]
    run(ren_cmd)

    # ---------------------------------------------------------------
    # 2. pad_portraits.py
    # ---------------------------------------------------------------
    pad_cmd = [sys.executable, str(ROOT / "pad_portraits.py"), "--yes"]
    if args.ratio is not None:
        pad_cmd.extend(["-r", str(args.ratio)])
    if args.input:
        pad_cmd.extend(["--input", args.input])
    run(pad_cmd)

    # ---------------------------------------------------------------
    # 3. verify_collection.py
    # ---------------------------------------------------------------
    ver_cmd = [sys.executable, str(ROOT / "verify_collection.py")]
    if args.input:
        ver_cmd.extend(["--input", args.input])
    run(ver_cmd)

    print("\nPipeline completed successfully.")


if __name__ == "__main__":
    main()
