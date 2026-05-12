#!/usr/bin/env python3
"""
Check if C++ files contain the /* @Configuration */ annotation above a class declaration.

Mirrors the approach in springbootplusplus_web_core/L1_check_rest_controller.py:
- Active annotation: /* @Configuration */ or /*@Configuration*/
- Skips already-processed markers like /*--@Configuration--*/ (same family as REST preprocessor)
- Requires a class declaration within the next few lines (with the same
  lookahead rules for intervening annotations / empty lines).
"""

import argparse
import re
from pathlib import Path
from typing import Any, Dict, List

# Pattern to match @Configuration annotation
configuration_annotation_pattern = re.compile(r"/\*\s*@Configuration\s*\*/")
configuration_processed_pattern = re.compile(r"/\*--\s*@Configuration\s*--\*/")

# Same idea as L1_check_rest_controller: class name + optional tokens before : or {
class_pattern = re.compile(
    r"class\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:.*?[:{]|[:{])",
)


def find_configuration_annotations(file_path: str) -> List[Dict[str, Any]]:
    """
    Find all /* @Configuration */ annotations and whether a class follows.

    Args:
        file_path: Path to the C++ file (.cpp, .h, or .hpp)

    Returns:
        List of dicts with keys: macro, line_number, context, class_name, has_class
    """
    found: List[Dict[str, Any]] = []

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            lines = file.readlines()
    except FileNotFoundError:
        return []
    except OSError:
        return []

    for line_num, line in enumerate(lines, 1):
        stripped_line = line.strip()

        if configuration_processed_pattern.search(stripped_line):
            continue

        if not configuration_annotation_pattern.search(stripped_line):
            continue

        macro_text = "/* @Configuration */"
        class_found = False
        class_name = ""
        context_lines: List[str] = []

        for i in range(line_num + 1, min(line_num + 11, len(lines) + 1)):
            next_line = lines[i - 1].strip()
            context_lines.append(next_line)

            if configuration_processed_pattern.search(next_line):
                continue

            if next_line.startswith("/*"):
                continue
            if next_line.startswith("//") and not re.search(r"///\s*@\w+\b", next_line):
                continue

            class_match = class_pattern.search(next_line)
            if class_match:
                class_found = True
                class_name = class_match.group(1)
                break

            if not next_line:
                continue

            # Allow other Spring-style annotations / doclets between @Configuration and class
            is_annotation_or_macro = (
                re.search(
                    r"///\s*@(Configuration|Bean|Import|ComponentScan|EnableWebSecurity|"
                    r"Order|Primary|Profile|Value|Component|Autowired|Scope|Conditional)\b",
                    next_line,
                )
                or next_line.startswith(
                    (
                        "Bean",
                        "Import",
                        "COMPONENT",
                        "SCOPE",
                        "VALIDATE",
                    )
                )
                or re.match(r"^[A-Z][A-Za-z0-9_]*\s*(?:\(|$)", next_line)
            )

            if not is_annotation_or_macro:
                break

        found.append(
            {
                "macro": macro_text,
                "line_number": line_num,
                "context": context_lines,
                "class_name": class_name,
                "has_class": class_found,
            }
        )

    return found


def check_configuration_annotation_exists(file_path: str) -> bool:
    """
    Return True if an active /* @Configuration */ appears above a class declaration.
    """
    for macro_info in find_configuration_annotations(file_path):
        if macro_info["has_class"]:
            return True
    return False


def validate_configuration_annotation_placement(file_path: str) -> Dict[str, Any]:
    """Full validation result for one file (same shape as RestController validator)."""
    macros = find_configuration_annotations(file_path)

    if not macros:
        return {
            "file_path": file_path,
            "has_configuration": False,
            "configuration_count": 0,
            "valid_placements": 0,
            "invalid_placements": 0,
            "issues": ["No @Configuration annotation found"],
        }

    valid_placements = 0
    invalid_placements = 0
    issues: List[str] = []

    for macro_info in macros:
        if macro_info["has_class"]:
            valid_placements += 1
        else:
            invalid_placements += 1
            issues.append(
                f"@Configuration at line {macro_info['line_number']} not followed by class declaration"
            )

    return {
        "file_path": file_path,
        "has_configuration": True,
        "configuration_count": len(macros),
        "valid_placements": valid_placements,
        "invalid_placements": invalid_placements,
        "issues": issues,
        "macros": macros,
    }


def check_multiple_files(file_paths: List[str]) -> Dict[str, Dict[str, Any]]:
    return {fp: validate_configuration_annotation_placement(fp) for fp in file_paths}


def validate_cpp_file(file_path: str) -> bool:
    cpp_extensions = {".cpp", ".h", ".hpp", ".cc", ".cxx", ".hh", ".hxx"}
    return Path(file_path).suffix.lower() in cpp_extensions


def main() -> Dict[str, Dict[str, Any]]:
    parser = argparse.ArgumentParser(
        description="Check if C++ files contain /* @Configuration */ above a class declaration"
    )
    parser.add_argument("files", nargs="+", help="C++ source files to analyze")
    parser.add_argument(
        "--simple",
        action="store_true",
        help="Simple check: only whether @Configuration (with class) exists",
    )
    parser.add_argument("--detailed", action="store_true", help="Reserved for detailed console output")
    parser.add_argument("--output", help="Optional results file path")
    parser.add_argument("--summary", action="store_true", help="Reserved for summary statistics")

    args = parser.parse_args()

    valid_files = [f for f in args.files if validate_cpp_file(f)]
    if not valid_files:
        return {}

    if args.simple:
        results = {
            fp: {"has_configuration": check_configuration_annotation_exists(fp)}
            for fp in valid_files
        }
    else:
        results = check_multiple_files(valid_files)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            if args.simple:
                for fp, result in results.items():
                    label = "Configuration found" if result["has_configuration"] else "No Configuration"
                    f.write(f"{fp}: {label}\n")
            else:
                for fp, result in results.items():
                    f.write(f"{fp}:\n")
                    if result["has_configuration"]:
                        f.write(f"  @Configuration annotations: {result['configuration_count']}\n")
                        f.write(f"  Valid placements: {result['valid_placements']}\n")
                        f.write(f"  Invalid placements: {result['invalid_placements']}\n")
                        if result["issues"]:
                            f.write(f"  Issues: {', '.join(result['issues'])}\n")
                    else:
                        f.write("  No @Configuration annotation found\n")
                    f.write("\n")

    _ = args.detailed
    _ = args.summary

    return results


__all__ = [
    "find_configuration_annotations",
    "check_configuration_annotation_exists",
    "validate_configuration_annotation_placement",
    "check_multiple_files",
    "main",
]

if __name__ == "__main__":
    main()
