#!/usr/bin/env python3
"""
Script to check if C++ files contain the VALIDATE macro above class declarations.
Detects VALIDATE, VALIDATE(ClassName), and validates their placement above classes.
"""

import re
import argparse
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Set


def find_validate_macros(file_path: str) -> List[Dict[str, str]]:
    """
    Find all VALIDATE macros in a C++ file and their context.
    
    Args:
        file_path: Path to the C++ file (.cpp, .h, or .hpp)
        
    Returns:
        List of dictionaries with 'macro', 'line_number', 'context', and 'class_name' keys
    """
    validate_macros = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
    except FileNotFoundError:
        # print(f"Error: File '{file_path}' not found")
        return []
    except Exception as e:
        # print(f"Error reading file '{file_path}': {e}")
        return []
    
    # Pattern to match VALIDATE macro (case sensitive)
    # Matches: VALIDATE, VALIDATE(ClassName), VALIDATE(ClassName, ...)
    # Must be standalone: not commented, not part of other text
    validate_pattern = r'^VALIDATE(?:\s*\(([^)]+)\))?\s*$'
    
    # Pattern to match class declarations
    class_pattern = r'class\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:[:{])'
    
    for line_num, line in enumerate(lines, 1):
        # Check for VALIDATE macro - must be standalone line (not commented, not part of other text)
        stripped_line = line.strip()
        
        # Skip commented lines
        if stripped_line.startswith('//') or stripped_line.startswith('/*') or stripped_line.startswith('*'):
            continue
            
        # Skip lines that are part of other text (not standalone VALIDATE)
        if stripped_line and not stripped_line.startswith('VALIDATE'):
            continue
            
        validate_match = re.search(validate_pattern, stripped_line)
        if validate_match:
            macro_text = validate_match.group(0)
            class_name_param = validate_match.group(1) if validate_match.group(1) else ""
            
            # Look ahead for class declaration (within next few lines)
            class_found = False
            class_name = ""
            context_lines = []
            
            # Check next 5 lines for class declaration
            for i in range(line_num, min(line_num + 6, len(lines) + 1)):
                if i <= len(lines):
                    next_line = lines[i - 1].strip()
                    context_lines.append(next_line)
                    
                    # Check for class declaration
                    class_match = re.search(class_pattern, next_line)
                    if class_match:
                        class_found = True
                        class_name = class_match.group(1)
                        break
                    
                    # Stop if we hit a blank line or different macro
                    if not next_line or (next_line and not next_line.startswith(('COMPONENT', 'SCOPE', 'VALIDATE'))):
                        break
            
            validate_macros.append({
                'macro': macro_text,
                'line_number': line_num,
                'context': context_lines,
                'class_name': class_name,
                'has_class': class_found,
                'class_name_param': class_name_param
            })
    
    return validate_macros


def check_validate_macro_exists(file_path: str) -> bool:
    """
    Simple check if VALIDATE macro exists in the file.
    
    Args:
        file_path: Path to the C++ file
        
    Returns:
        True if VALIDATE macro is found, False otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Simple pattern to check if VALIDATE exists anywhere
        return 'VALIDATE' in content
    except Exception:
        return False


def validate_macro_placement(file_path: str) -> Dict[str, any]:
    """
    Comprehensive validation of VALIDATE macro placement and usage.
    
    Args:
        file_path: Path to the C++ file
        
    Returns:
        Dictionary with validation results
    """
    validate_macros = find_validate_macros(file_path)
    
    if not validate_macros:
        return {
            'file_path': file_path,
            'has_validate': False,
            'validate_count': 0,
            'valid_placements': 0,
            'invalid_placements': 0,
            'issues': ['No VALIDATE macro found']
        }
    
    valid_placements = 0
    invalid_placements = 0
    issues = []
    
    for macro_info in validate_macros:
        if macro_info['has_class']:
            valid_placements += 1
            # VALIDATE parameter doesn't need to match class name - it's just a label
        else:
            invalid_placements += 1
            issues.append(f"VALIDATE macro at line {macro_info['line_number']} not followed by class declaration")
    
    return {
        'file_path': file_path,
        'has_validate': True,
        'validate_count': len(validate_macros),
        'valid_placements': valid_placements,
        'invalid_placements': invalid_placements,
        'issues': issues,
        'macros': validate_macros
    }


def check_multiple_files(file_paths: List[str]) -> Dict[str, Dict[str, any]]:
    """
    Check VALIDATE macro in multiple files.
    
    Args:
        file_paths: List of file paths to check
        
    Returns:
        Dictionary mapping file paths to validation results
    """
    results = {}
    
    for file_path in file_paths:
        results[file_path] = validate_macro_placement(file_path)
    
    return results


def validate_cpp_file(file_path: str) -> bool:
    """
    Check if the file is a valid C++ source file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        True if it's a C++ file, False otherwise
    """
    cpp_extensions = {'.cpp', '.h', '.hpp', '.cc', '.cxx', '.hh', '.hxx'}
    return Path(file_path).suffix.lower() in cpp_extensions


def main():
    """Main function to handle command line arguments and execute the validation."""
    parser = argparse.ArgumentParser(
        description="Check if C++ files contain VALIDATE macro above class declarations"
    )
    parser.add_argument(
        "files", 
        nargs="+", 
        help="C++ source files to analyze (.cpp, .h, .hpp, etc.)"
    )
    parser.add_argument(
        "--simple", 
        action="store_true",
        help="Simple check: just show if VALIDATE exists or not"
    )
    parser.add_argument(
        "--detailed", 
        action="store_true",
        help="Show detailed validation information"
    )
    parser.add_argument(
        "--output", 
        help="Output file to save results (optional)"
    )
    parser.add_argument(
        "--summary", 
        action="store_true",
        help="Show summary statistics"
    )
    
    args = parser.parse_args()
    
    # Filter valid C++ files
    valid_files = [f for f in args.files if validate_cpp_file(f)]
    invalid_files = [f for f in args.files if not validate_cpp_file(f)]
    
    if invalid_files:
        # print(f"Warning: Skipping non-C++ files: {', '.join(invalid_files)}")
        pass
    
    if not valid_files:
        # print("No valid C++ files provided")
        return {}
    
    # Check files
    if args.simple:
        # Simple check mode
        results = {}
        for file_path in valid_files:
            has_validate = check_validate_macro_exists(file_path)
            results[file_path] = {'has_validate': has_validate}
            
            # status = "✓ VALIDATE found" if has_validate else "✗ No VALIDATE"
            # print(f"{file_path}: {status}")
    else:
        # Detailed validation mode
        results = check_multiple_files(valid_files)
        
        # Display results
        # for file_path, result in results.items():
        #     print(f"\n{'='*60}")
        #     print(f"File: {file_path}")
        #     print(f"{'='*60}")
        #     
        #     if result['has_validate']:
        #         print(f"✓ VALIDATE macro found ({result['validate_count']} occurrences)")
        #         print(f"  Valid placements: {result['valid_placements']}")
        #         print(f"  Invalid placements: {result['invalid_placements']}")
        #         
        #         if args.detailed and result['macros']:
        #             print(f"\n  Detailed macro information:")
        #             for macro in result['macros']:
        #                 print(f"    Line {macro['line_number']}: {macro['macro']}")
        #                 if macro['has_class']:
        #                     print(f"      → Class: {macro['class_name']}")
        #                 else:
        #                     print(f"      → No class found")
        #         
        #         if result['issues']:
        #             print(f"\n  Issues found:")
        #             for issue in result['issues']:
        #                 print(f"    ⚠ {issue}")
        #     else:
        #         print("✗ No VALIDATE macro found")
        pass
    
    # Show summary if requested
    if args.summary and not args.simple:
        # print(f"\n{'='*60}")
        # print("SUMMARY")
        # print(f"{'='*60}")
        # total_files = len(valid_files)
        # files_with_validate = len([r for r in results.values() if r['has_validate']])
        # total_validates = sum([r.get('validate_count', 0) for r in results.values()])
        # total_valid_placements = sum([r.get('valid_placements', 0) for r in results.values()])
        # total_invalid_placements = sum([r.get('invalid_placements', 0) for r in results.values()])
        # 
        # print(f"Files analyzed: {total_files}")
        # print(f"Files with VALIDATE: {files_with_validate}")
        # print(f"Files without VALIDATE: {total_files - files_with_validate}")
        # print(f"Total VALIDATE macros: {total_validates}")
        # print(f"Valid placements: {total_valid_placements}")
        # print(f"Invalid placements: {total_invalid_placements}")
        pass
    
    # Save to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            if args.simple:
                for file_path, result in results.items():
                    status = "VALIDATE found" if result['has_validate'] else "No VALIDATE"
                    f.write(f"{file_path}: {status}\n")
            else:
                for file_path, result in results.items():
                    f.write(f"{file_path}:\n")
                    if result['has_validate']:
                        f.write(f"  VALIDATE macros: {result['validate_count']}\n")
                        f.write(f"  Valid placements: {result['valid_placements']}\n")
                        f.write(f"  Invalid placements: {result['invalid_placements']}\n")
                        if result['issues']:
                            f.write(f"  Issues: {', '.join(result['issues'])}\n")
                    else:
                        f.write(f"  No VALIDATE macro found\n")
                    f.write("\n")
        # print(f"\nResults saved to: {args.output}")
    
    return results


# Export functions for other scripts to import
__all__ = [
    'find_validate_macros',
    'check_validate_macro_exists',
    'validate_macro_placement',
    'check_multiple_files',
    'main'
]


if __name__ == "__main__":
    # When run as script, execute main and store result
    result = main()
