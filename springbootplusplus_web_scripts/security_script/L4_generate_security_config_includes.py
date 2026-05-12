#!/usr/bin/env python3
"""
Generate #include lines for security config headers and inject them immediately after
``#include <StandardDefines.h>`` in a target file.

The anchor line may be written as ``// #include <...>``; it is always rewritten as an
active ``#include <StandardDefines.h>``.

Any consecutive ``#include "..."`` lines that match the paths we are about to inject are
removed first (so re-runs stay idempotent) without touching other headers (e.g.
``IEndpointSecurityRuleManager.h``) that follow after a blank line or unrelated include.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import List, Sequence, Tuple

_STANDARD_DEFINES_LINE = "#include <StandardDefines.h>"

# First line only: StandardDefines (optional // line comment).
_STANDARD_DEFINES_LINE_RE = re.compile(
    r"^[ \t]*(?://[ \t]*)?#include\s*<StandardDefines\.h>\s*\r?\n",
    re.MULTILINE | re.IGNORECASE,
)

_QUOTED_INCLUDE_RE = re.compile(
    r"^[ \t]*#include\s+\"([^\"]+)\"\s*\r?\n",
    re.MULTILINE,
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
    """
    lines: List[str] = []
    for p in _unique_preserve(header_paths):
        norm = p.strip()
        if not norm:
            continue
        if norm.replace("\\", "/").lower() in ("standarddefines.h", "<standarddefines.h>"):
            continue
        lines.append(f'#include "{norm}"')
    return lines


def generate_include_snippet(header_paths: Sequence[str]) -> str:
    """Single string: one #include per line, no trailing newline after last line."""
    return "\n".join(generate_include_lines(header_paths))


def _strip_trailing_generated_includes(
    source: str, start: int, header_paths: Sequence[str]
) -> int:
    """
    From ``start``, drop consecutive ``#include "rel/path"`` lines whose path is in
    ``header_paths`` (posix-normalized). Stops at the first line that is not such an include.
    Returns the index in ``source`` after removed material.
    """
    want = {Path(p.strip()).as_posix() for p in header_paths if p.strip()}
    if not want:
        return start

    pos = start
    while pos < len(source):
        m = _QUOTED_INCLUDE_RE.match(source, pos)
        if not m:
            break
        inc_path = Path(m.group(1)).as_posix()
        if inc_path not in want:
            break
        pos = m.end()
    return pos


def replace_standard_defines_include_block(source: str, header_paths: Sequence[str]) -> Tuple[str, bool]:
    """
    Rewrite the ``#include <StandardDefines.h>`` line and refresh generated quoted includes
    immediately after it.

    Returns:
        (new_source, True) if the StandardDefines include line was found.
    """
    m = _STANDARD_DEFINES_LINE_RE.search(source)
    if not m:
        return source, False

    anchor_line = _STANDARD_DEFINES_LINE + "\n"
    after_anchor = m.end()
    stripped_end = _strip_trailing_generated_includes(source, after_anchor, header_paths)

    extra = generate_include_lines(header_paths)
    if extra:
        insertion = anchor_line + "\n".join(extra) + "\n"
    else:
        insertion = anchor_line

    new_source = source[: m.start()] + insertion + source[stripped_end:]
    return new_source, True


# Backward-compatible name for callers
replace_registry_include_block = replace_standard_defines_include_block


def inject_security_config_includes(
    file_path: str,
    header_paths: Sequence[str],
    *,
    dry_run: bool = False,
) -> bool:
    """
    Read ``file_path`` (UTF-8), replace the StandardDefines include block, write back unless dry_run.

    Returns:
        True if the anchor include line was found.
    """
    path = Path(file_path)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return False

    new_text, ok = replace_standard_defines_include_block(text, header_paths)
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
        description="Generate security-config #include lines or inject them after #include <StandardDefines.h>"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("generate", help="Print #include lines to stdout")
    gen.add_argument("headers", nargs="+", help='Header paths as in #include "...", e.g. auth/Foo.h Foo.h')

    inj = sub.add_parser("inject", help="Patch file: refresh includes after #include <StandardDefines.h>")
    inj.add_argument("file", help="Target source/header (e.g. SecurityConfigRegistry.h)")
    inj.add_argument("headers", nargs="*", help='Headers to #include after #include <StandardDefines.h>')
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
    "replace_standard_defines_include_block",
    "replace_registry_include_block",
    "inject_security_config_includes",
    "main",
]


if __name__ == "__main__":
    main()
