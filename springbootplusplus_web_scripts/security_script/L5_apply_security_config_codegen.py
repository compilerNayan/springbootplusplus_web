#!/usr/bin/env python3
"""
Orchestrate security-config codegen: L4 (includes after ISecurityConfigRegistry.h) +
L3 (Register(make_shared<...>()) in RegisterAllSecurityConfigs placeholder) on one target file.

Reads the target once, applies both transforms, writes once (unless --dry-run).
Both markers must be present for a successful apply.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any, Dict, Sequence

script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

import L3_generate_security_config_registrations as L3  # noqa: E402
import L4_generate_security_config_includes as L4  # noqa: E402


def _log_security_codegen_diagnostics(
    target_file: str, text: str, includes_ok: bool, regs_ok: bool
) -> None:
    """Explain L5 failures on stderr (build logs)."""
    if includes_ok and regs_ok:
        return
    if not includes_ok:
        if "ISecurityConfigRegistry.h" not in text:
            print(
                f"[springbootplusplus_web] L5 security codegen: {target_file}: "
                f'missing #include "ISecurityConfigRegistry.h" (registry header unchanged).',
                file=sys.stderr,
            )
        else:
            print(
                f"[springbootplusplus_web] L5 security codegen: {target_file}: "
                f"could not match the ISecurityConfigRegistry #include block "
                f'(expected `#include \"ISecurityConfigRegistry.h\"` or `// #include \"...\"` on one line).',
                file=sys.stderr,
            )
    if not regs_ok:
        if "PLACEHOLDER" not in text.upper() or "SECURITY" not in text.upper():
            print(
                f"[springbootplusplus_web] L5 security codegen: {target_file}: "
                f"registration placeholder not found (expected // PLACEHOLDER FOR SECURITY CONFIG REGISTRATIONS).",
                file=sys.stderr,
            )
        else:
            print(
                f"[springbootplusplus_web] L5 security codegen: {target_file}: "
                f"placeholder text present but line did not match the expected pattern.",
                file=sys.stderr,
            )


def apply_security_config_codegen(
    target_file: str,
    header_paths: Sequence[str],
    class_names: Sequence[str],
    *,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Update ``target_file`` with L4 include block and L3 registration block.

    Args:
        target_file: Path to the registry header (e.g. SecurityConfigRegistry.h).
        header_paths: Values for ``#include "..."`` lines after ``ISecurityConfigRegistry.h``.
        class_names: Concrete ISecurityConfig implementation class names for ``make_shared``.

    Returns:
        Dict with keys: ``success``, ``includes_applied``, ``registrations_applied``.
        ``success`` is True only if both replacements matched. The file is written only when
        ``success`` and not ``dry_run``.
    """
    path = Path(target_file)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return {
            "success": False,
            "includes_applied": False,
            "registrations_applied": False,
            "error": "could not read target file",
        }

    text, includes_ok = L4.replace_registry_include_block(text, header_paths)
    text, regs_ok = L3.replace_placeholder_with_registrations(text, class_names)
    success = bool(includes_ok and regs_ok)

    if not success:
        _log_security_codegen_diagnostics(str(path), text, includes_ok, regs_ok)

    if success and not dry_run:
        path.write_text(text, encoding="utf-8")

    return {
        "success": success,
        "includes_applied": includes_ok,
        "registrations_applied": regs_ok,
    }


def validate_cpp_like_file(file_path: str) -> bool:
    suffix = Path(file_path).suffix.lower()
    return suffix in {".cpp", ".h", ".hpp", ".cc", ".cxx", ".hh", ".hxx"}


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Apply L4 includes + L3 Register(make_shared<...>()) to a single target "
            "(e.g. SecurityConfigRegistry.h)."
        )
    )
    parser.add_argument(
        "--target",
        required=True,
        help="Header to patch (must contain ISecurityConfigRegistry include + registration placeholder)",
    )
    parser.add_argument(
        "--files",
        nargs="*",
        default=[],
        help='Header paths for #include "..." after ISecurityConfigRegistry.h (order preserved)',
    )
    parser.add_argument(
        "--classes",
        nargs="*",
        default=[],
        help="Class names for Register(make_shared<Class>()); in RegisterAllSecurityConfigs",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Check that both markers exist and transforms apply; do not write the file",
    )

    args = parser.parse_args()

    if not validate_cpp_like_file(args.target):
        raise SystemExit(2)

    result = apply_security_config_codegen(
        args.target,
        args.files,
        args.classes,
        dry_run=args.dry_run,
    )

    if not result["success"]:
        if os.environ.get("SPRINGBOOTPLUSPLUS_WEB_SECURITY_CODEGEN_VERBOSE"):
            print(f"[springbootplusplus_web] L5 result: {result}", file=sys.stderr)
        raise SystemExit(1)

    raise SystemExit(0)


__all__ = ["apply_security_config_codegen", "main"]


if __name__ == "__main__":
    main()
