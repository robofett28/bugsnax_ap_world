"""
build_apworld.py

Packages an unzipped apworld source folder into a real .apworld file.

Example:
    python build_apworld.py manual_bugsnax
    produces manual_bugsnax.apworld in the same directory
"""

import sys
import zipfile
from pathlib import Path


def build(source_folder: str):
    source_path = Path(source_folder).resolve()
    if not source_path.is_dir():
        print(f"'{source_path}' is not a folder.")
        sys.exit(1)

    output_path = source_path.parent / f"{source_path.name}.apworld"

    if output_path.exists():
        output_path.unlink()

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in source_path.rglob("*"):
            if file.is_file():
                arcname = source_path.name / file.relative_to(source_path)
                zf.write(file, arcname)

    print(f"Built: {output_path}")

    # Sanity check, same as the one that caught the original naming bug
    with zipfile.ZipFile(output_path) as zf:
        dirs = [f.name for f in zipfile.Path(zf).iterdir() if f.is_dir()]
        stem = output_path.stem
        ok = len(dirs) == 1 and dirs[0] in stem
        print(f"Naming check: {'PASS' if ok else 'FAIL — will not install correctly!'}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python build_apworld.py <path-to-source-folder>")
        sys.exit(1)
    build(sys.argv[1])