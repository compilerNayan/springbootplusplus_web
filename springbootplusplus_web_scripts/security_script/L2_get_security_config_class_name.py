#!/usr/bin/env python3
"""
Extract the concrete class name for a /* @Configuration */ security config:
the class declared after the annotation that inherits (directly) from ISecurityConfig.

Uses the same @Configuration discovery and lookahead as L1_check_configuration_annotation.py,
then parses the class line so that ISecurityConfig must appear in the base-clause.

Supported on a single line, for example:
  class SomeConfig : public ISecurityConfig
  class SomeConfig final : public ISecurityConfig
  class SomeConfig : public IOther, public ISecurityConfig
  template<typename T> class SomeConfig : public ISecurityConfig   (template on same line only)

If ``class`` appears only after a multi-line ``template<...>`` block, L1 lookahead may not
see the class line; split declarations are not supported yet.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

import L1_check_configuration_annotation as L1  # noqa: E402

# Derived class name, optional "final", optional single-level template<...> on same line.
# Base-clause must list ISecurityConfig (direct base), not a substring of another identifier.
_SECURITY_CONFIG_CLASS_RE = re.compile(
    r"""
    ^\s*
    (?:template\s*<[^>]+>\s*)?
    class\s+
    (?P<name>[A-Za-z_][A-Za-z0-9_:]*)
    \s*
    (?:final\s*)?
    :\s*
    (?P<bases>[^;{]+)
    """,
    re.VERBOSE,
)

_IS_SECURITY_CONFIG_BASE = re.compile(r"\bISecurityConfig\b")


def _parse_derived_class_name(class_line: str) -> Optional[str]:
    stripped = class_line.strip()
    m = _SECURITY_CONFIG_CLASS_RE.match(stripped)
    if not m:
        return None
    bases = m.group("bases")
    if not _IS_SECURITY_CONFIG_BASE.search(bases):
        return None
    return m.group("name")


def get_security_config_class_name(file_path: str) -> Optional[str]:
    """
    Return the first derived class name after /* @Configuration */ that inherits ISecurityConfig.

    Returns:
        Class name string, or None if not found or file unreadable.
    """
    for name in get_all_security_config_class_names(file_path):
        return name
    return None


def get_all_security_config_class_names(file_path: str) -> List[str]:
    """
    Return all derived class names for each /* @Configuration */ block whose following
    class inherits ISecurityConfig (in order of appearance).
    """
    names: List[str] = []
    for macro in L1.find_configuration_annotations(file_path):
        for ctx_line in macro.get("context", []):
            derived = _parse_derived_class_name(ctx_line)
            if derived:
                names.append(derived)
                break
    return names


def get_security_config_class_info(file_path: str) -> Dict[str, Any]:
    """
    Structured result for tooling: success flag, class name(s), and issues.
    """
    names = get_all_security_config_class_names(file_path)
    if not names:
        has_cfg = L1.check_configuration_annotation_exists(file_path)
        issue = (
            "No class inheriting ISecurityConfig found after @Configuration"
            if has_cfg
            else "No valid /* @Configuration */ with following class found"
        )
        return {
            "file_path": file_path,
            "success": False,
            "class_name": None,
            "class_names": [],
            "issues": [issue],
        }
    return {
        "file_path": file_path,
        "success": True,
        "class_name": names[0],
        "class_names": names,
        "issues": [],
    }


def validate_cpp_file(file_path: str) -> bool:
    cpp_extensions = {".cpp", ".h", ".hpp", ".cc", ".cxx", ".hh", ".hxx"}
    return Path(file_path).suffix.lower() in cpp_extensions


def main() -> Optional[str]:
    parser = argparse.ArgumentParser(
        description="Get the ISecurityConfig implementation class name after /* @Configuration */"
    )
    parser.add_argument("file", help="C++ header/source path")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Print all matching class names (one per line) instead of only the first",
    )
    args = parser.parse_args()

    if not validate_cpp_file(args.file):
        return None

    if args.all:
        for n in get_all_security_config_class_names(args.file):
            print(n)
        return None

    name = get_security_config_class_name(args.file)
    if name:
        print(name)
    return name


__all__ = [
    "get_security_config_class_name",
    "get_all_security_config_class_names",
    "get_security_config_class_info",
    "main",
]


if __name__ == "__main__":
    main()
