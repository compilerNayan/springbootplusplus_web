#!/usr/bin/env python3
"""
Generate #include lines for security config headers and inject them after
#include "ISecurityConfigRegistry.h" in a target file.

Replaces the registry #include line together with any immediately following
contiguous quoted #include lines (blank lines stop the run), so repeated
injection refreshes the block without duplicating lines.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import List, Sequence, Tuple

_REGISTRY_INCLUDE_LINE = '#include "ISecurityConfigRegistry.h"'

# Registry line + zero or more following #include "..." lines; \s* may span newlines
# so a blank line between includes stops the tail (next #include must follow only horizontal whitespace on its line).
_INCLUDE_BLOCK_RE = re.compile(
    r'(^[ \t]*#include\s+"ISecurityConfigRegistry\.h"\s*\r?\n)'
    r'(?:^[ \t]*#include\s+"[^"]+"\s*\r?\n)*',
    re.MULTILINE | re.IGNORECASE,
)


def _unique_preserve(paths: Sequence[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for p in paths:
        if p in seen:
            continue
        seen.add(p)
        out.append(p)
    return out


def generate_include_lines(header_paths: Sequence[str]) -> List[str]:
    """
    Build one #include "path" string per path (deduplicated, order preserved).

    Paths are used exactly as given (e.g. ``auth/MyConfig.h`` or ``MyConfig.h``).
    ``ISecurityConfigRegistry.h`` is skipped if present; that line stays fixed in the target file.
    """
    lines: List[str] = []
    for p in _unique_preserve(header_paths):
        norm = p.strip()
        if not norm:
            continue
        if norm.replace("\\", "/").endswith("ISecurityConfigRegistry.h"):
            continue
        lines.append(f'#include "{norm}"')
    return lines


def generate_include_snippet(header_paths: Sequence[str]) -> str:
    """Single string: one #include per line, no trailing newline after last line."""
    return "\n".join(generate_include_lines(header_paths))


def replace_registry_include_block(source: str, header_paths: Sequence[str]) -> Tuple[str, bool]:
    """
    Replace the first occurrence of the ISecurityConfigRegistry #include line and any
    contiguous quoted #includes immediately after it with the registry line plus new includes.

    Returns:
        (new_source, True) if the registry include was found.
    """
    m = _INCLUDE_BLOCK_RE.search(source)
    if not m:
        return source, False

    registry_line = _REGISTRY_INCLUDE_LINE + "\n"
    extra = generate_include_lines(header_paths)
    if extra:
        insertion = registry_line + "\n".join(extra) + "\n"
    else:
        insertion = registry_line

    new_source = source[: m.start()] + insertion + source[m.end() :]
    return new_source, True


def inject_security_config_includes(
    file_path: str,
    header_paths: Sequence[str],
    *,
    dry_run: bool = False,
) -> bool:
    """
    Read ``file_path`` (UTF-8), replace the registry include block, write back unless dry_run.

    Returns:
        True if the registry include block was found.
    """
    path = Path(file_path)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return False

    new_text, ok = replace_registry_include_block(text, header_paths)
    if not ok:
        return False
    if dry_run:
        return True
    path.write_text(new_text, encoding="utf-8")
    return True


def validate_cpp_like_file(file_path: str) -> bool:
    suffix = Path(file_path).suffix.lower()
    return suffix in {".cpp", ".h", ".hpp", ".cc", ".cxx", ".hh", ".hxx"}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate security-config #include lines or inject them after ISecurityConfigRegistry.h"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("generate", help="Print #include lines to stdout")
    gen.add_argument("headers", nargs="+", help='Header paths as in #include "...", e.g. auth/Foo.h Foo.h')

    inj = sub.add_parser("inject", help="Patch file: keep registry include, add/replace following includes")
    inj.add_argument("file", help="Target source/header (e.g. SecurityConfigRegistry.h)")
    inj.add_argument("headers", nargs="*", help="Headers to #include after the registry line")
    inj.add_argument("--dry-run", action="store_true", help="Do not write the file")

    args = parser.parse_args()

    if args.command == "generate":
        print(generate_include_snippet(args.headers))
        return

    if args.command == "inject":
        if not validate_cpp_like_file(args.file):
            raise SystemExit(1)
        ok = inject_security_config_includes(args.file, args.headers, dry_run=args.dry_run)
        raise SystemExit(0 if ok else 1)


__all__ = [
    "generate_include_lines",
    "generate_include_snippet",
    "replace_registry_include_block",
    "inject_security_config_includes",
    "main",
]


if __name__ == "__main__":
    main()
