#!/usr/bin/env python3
"""
Mark /* @Configuration */ as processed by rewriting to /*--@Configuration--*/,
matching the REST preprocessor style for processed mapping annotations (see
L6_generate_code_for_all_sources.comment_rest_macros).

Skips lines that already match the processed pattern.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import List

configuration_annotation_pattern = re.compile(r"/\*\s*@Configuration\s*\*/")
configuration_processed_pattern = re.compile(r"/\*--\s*@Configuration\s*--\*/")


def comment_configuration_annotation(file_path: str, dry_run: bool = False) -> bool:
    """
    Replace each active /* @Configuration */ line with /*--@Configuration--*/ (same indent).

    Args:
        file_path: C++ source/header path.
        dry_run: If True, do not write; still returns whether any line would change.

    Returns:
        True if the file was modified or would be modified, False if nothing matched or IO error.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except OSError:
        return False

    modified = False
    out: List[str] = []

    for line in lines:
        stripped = line.strip()
        if configuration_processed_pattern.search(stripped):
            out.append(line)
            continue

        if configuration_annotation_pattern.search(stripped):
            indent = len(line) - len(line.lstrip())
            indent_str = line[:indent]
            processed_line = f"{indent_str}/*--@Configuration--*/\n"
            if not dry_run:
                out.append(processed_line)
            else:
                out.append(line)
            modified = True
            continue

        out.append(line)

    if modified and not dry_run:
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.writelines(out)
        except OSError:
            return False

    return modified


def comment_configuration_annotation_many(
    file_paths: List[str],
    *,
    dry_run: bool = False,
) -> dict[str, bool]:
    """Run comment_configuration_annotation on each path; returns path -> changed."""
    return {fp: comment_configuration_annotation(fp, dry_run=dry_run) for fp in file_paths}


def validate_cpp_file(file_path: str) -> bool:
    cpp_extensions = {".cpp", ".h", ".hpp", ".cc", ".cxx", ".hh", ".hxx"}
    return Path(file_path).suffix.lower() in cpp_extensions


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Rewrite /* @Configuration */ to /*--@Configuration--*/ (processed marker)."
    )
    parser.add_argument("files", nargs="+", help="C++ headers/sources to update")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not write files; exit 0 if any file would change",
    )

    args = parser.parse_args()

    any_change = False
    for fp in args.files:
        if not validate_cpp_file(fp):
            continue
        if comment_configuration_annotation(fp, dry_run=args.dry_run):
            any_change = True

    if args.dry_run:
        raise SystemExit(0 if any_change else 1)
    raise SystemExit(0 if any_change else 1)


__all__ = [
    "comment_configuration_annotation",
    "comment_configuration_annotation_many",
    "main",
]


if __name__ == "__main__":
    main()
