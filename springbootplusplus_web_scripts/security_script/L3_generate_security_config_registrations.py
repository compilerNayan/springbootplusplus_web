#!/usr/bin/env python3
"""
Generate ISecurityConfig registration lines (make_shared + Register) and inject them
by replacing // PLACEHOLDER FOR SECURITY CONFIG REGISTRATIONS inside
RegisterAllSecurityConfigs().
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import List, Sequence, Tuple

# Matches the placeholder line; leading whitespace is preserved for generated lines.
_PLACEHOLDER_LINE_RE = re.compile(
    r"^(\s*)//\s*PLACEHOLDER\s+FOR\s+SECURITY\s+CONFIG\s+REGISTRATIONS\s*$",
    re.IGNORECASE | re.MULTILINE,
)


def generate_registration_snippet(
    class_names: Sequence[str],
    *,
    indent: str = "        ",
) -> str:
    """
    Build the registration snippet (no trailing newline after last line).

    Args:
        class_names: Concrete config class names (e.g. Config1, MySecurityConfig).
        indent: Leading whitespace per line (default 8 spaces, matches SecurityConfigRegistry.h).

    Returns:
        Joined lines: Register(make_shared<Name>()); for each name.
    """
    lines = [f"{indent}Register(make_shared<{name}>());" for name in class_names]
    return "\n".join(lines)


def replace_placeholder_with_registrations(
    source: str,
    class_names: Sequence[str],
) -> Tuple[str, bool]:
    """
    Replace the first line matching the security-config placeholder with generated registrations.

    Returns:
        (new_source, True) if replacement was done, (source, False) if placeholder not found.
    """
    if _PLACEHOLDER_LINE_RE.search(source) is None:
        return source, False

    out_lines: List[str] = []
    replaced = False
    for line in source.splitlines(keepends=True):
        if not replaced:
            m = _PLACEHOLDER_LINE_RE.match(line.rstrip("\r\n"))
            if m:
                indent = m.group(1)
                if class_names:
                    body = generate_registration_snippet(class_names, indent=indent)
                    out_lines.append(body + "\n")
                else:
                    # Remove placeholder only; leave no registration lines.
                    pass
                replaced = True
                continue
        out_lines.append(line)

    if not replaced:
        return source, False
    return "".join(out_lines), True


def inject_registrations_into_file(
    file_path: str,
    class_names: Sequence[str],
    *,
    dry_run: bool = False,
) -> bool:
    """
    Read file_path, replace placeholder line with Register(make_shared<...>()); lines, write back.

    Returns:
        True if the placeholder was found and the file was updated (or dry_run would update).
    """
    path = Path(file_path)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return False

    new_text, did_replace = replace_placeholder_with_registrations(text, class_names)
    if not did_replace:
        return False
    if dry_run:
        return True
    path.write_text(new_text, encoding="utf-8")
    return True


def validate_cpp_file(file_path: str) -> bool:
    cpp_extensions = {".cpp", ".h", ".hpp", ".cc", ".cxx", ".hh", ".hxx"}
    return Path(file_path).suffix.lower() in cpp_extensions


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate security config registrations or inject them into a header/source file."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("generate", help="Print snippet only")
    gen.add_argument("classes", nargs="+", help="Class names, e.g. Config1 Config2")

    inj = sub.add_parser("inject", help="Replace placeholder in file with registrations")
    inj.add_argument("file", help="Path to file containing RegisterAllSecurityConfigs placeholder")
    inj.add_argument("classes", nargs="*", help="Class names (omit for empty body)")
    inj.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not write; exit 0 if placeholder would be replaced",
    )

    args = parser.parse_args()

    if args.command == "generate":
        print(generate_registration_snippet(args.classes))
        return

    if args.command == "inject":
        if not validate_cpp_file(args.file):
            raise SystemExit(1)
        ok = inject_registrations_into_file(args.file, args.classes, dry_run=args.dry_run)
        raise SystemExit(0 if ok else 1)


__all__ = [
    "generate_registration_snippet",
    "replace_placeholder_with_registrations",
    "inject_registrations_into_file",
    "main",
]


if __name__ == "__main__":
    main()
