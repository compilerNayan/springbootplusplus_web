#!/usr/bin/env python3
"""
Resolve a single header/source that uses /* @Configuration */ into the concrete
ISecurityConfig class name and the file's absolute path.

Uses L1_check_configuration_annotation (annotation + class placement) and
L2_get_security_config_class_name (class inheriting ISecurityConfig).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Optional

script_dir = str(Path(__file__).resolve().parent)
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

import L1_check_configuration_annotation as L1  # noqa: E402
import L2_get_security_config_class_name as L2  # noqa: E402


def resolve_security_configuration_file(file_path: str) -> Optional[Dict[str, str]]:
    """
    If ``file_path`` has a valid /* @Configuration */ with a following class that
    inherits ISecurityConfig, return ``{"class_name": ..., "file_path": <absolute>}``.

    Returns:
        Dict with keys ``class_name`` and ``file_path``, or None if the file does not
        qualify (missing annotation, unreadable file, or no ISecurityConfig subclass found).
    """
    path = Path(file_path)
    try:
        resolved = path.resolve()
    except OSError:
        return None

    if not resolved.is_file():
        return None

    if not L1.check_configuration_annotation_exists(str(resolved)):
        return None

    class_name = L2.get_security_config_class_name(str(resolved))
    if not class_name:
        return None

    return {
        "class_name": class_name,
        "file_path": str(resolved),
    }


def validate_cpp_file(file_path: str) -> bool:
    suffix = Path(file_path).suffix.lower()
    return suffix in {".cpp", ".h", ".hpp", ".cc", ".cxx", ".hh", ".hxx"}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="If file has @Configuration + ISecurityConfig subclass, print class name and absolute path."
    )
    parser.add_argument("file", help="Path to a C++ header or source file")
    parser.add_argument(
        "--format",
        choices=("json", "lines"),
        default="json",
        help='json: one JSON object; lines: class name on first line, path on second',
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")

    args = parser.parse_args()

    if not validate_cpp_file(args.file):
        raise SystemExit(2)

    result = resolve_security_configuration_file(args.file)
    if not result:
        raise SystemExit(1)

    if args.format == "json":
        if args.pretty:
            print(json.dumps(result, indent=2))
        else:
            print(json.dumps(result))
    else:
        print(result["class_name"])
        print(result["file_path"])

    raise SystemExit(0)


__all__ = ["resolve_security_configuration_file", "main"]


if __name__ == "__main__":
    main()
