#!/usr/bin/env python3
"""
Script to check if C++ files contain the @Scope annotation with valid values above class declarations.
Only accepts @Scope("PROTOTYPE") or @Scope("SINGLETON"). Ignores processed annotations.
"""

import re
import argparse
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Set


def find_scope_macros(file_path: str) -> List[Dict[str, str]]:
    """
    Find all @Scope annotations in a C++ file and their context.
    
    Args:
        file_path: Path to the C++ file (.cpp, .h, or .hpp)
        
    Returns:
        List of dictionaries with 'macro', 'line_number', 'context', 'class_name', 'scope_value', and 'is_valid' keys
    """
    scope_macros = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
    except FileNotFoundError:
        # print(f"Error: File '{file_path}' not found")
        return []
    except Exception as e:
        # print(f"Error reading file '{file_path}': {e}")
        return []
    
    # Pattern to match @Scope annotation with parameter (search for /* @Scope("...") */ or /*@Scope("...")*/)
    # Also check for already processed /*--@Scope("...")--*/ pattern
    scope_annotation_pattern = re.compile(r'/\*\s*@Scope\s*\(\s*["\'](PROTOTYPE|SINGLETON)["\']\s*\)\s*\*/')
    scope_processed_pattern = re.compile(r'/\*--\s*@Scope\s*\(\s*["\'](PROTOTYPE|SINGLETON)["\']\s*\)\s*--\*/')
    
    # Pattern to match class declarations
    class_pattern = r'class\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:[:{])'
    
    for line_num, line in enumerate(lines, 1):
        stripped_line = line.strip()
        
        # Skip already processed annotations
        if scope_processed_pattern.search(stripped_line):
            continue
        
        # Skip other comments that aren't @Scope annotations
        # But allow /* @Scope("...") */ annotations to be processed
        if stripped_line.startswith('/*') and not scope_annotation_pattern.search(stripped_line):
            continue
        # Skip single-line comments
        if stripped_line.startswith('//'):
            continue
            
        # Check if line contains valid @Scope annotation
        scope_match = scope_annotation_pattern.search(stripped_line)
        if scope_match:
            annotation_text = scope_match.group(0)
            scope_value = scope_match.group(1)
            
            # Look ahead for class declaration (within next few lines)
            # Allow other annotations/macros to appear between @Scope and class
            class_found = False
            class_name = ""
            context_lines = []
            
            # Check next 5 lines for class declaration
            for i in range(line_num, min(line_num + 6, len(lines) + 1)):
                if i <= len(lines):
                    next_line = lines[i - 1].strip()
                    context_lines.append(next_line)
                    
                    # Skip other comments that aren't annotations
                    # But allow /* @Component */, /* @Scope */, /* @Autowired */ annotations to be processed
                    if next_line.startswith('/*') and not re.search(r'/\*\s*@(Component|Scope|Autowired)\s*\*/', next_line):
                        continue
                    # Skip single-line comments
                    if next_line.startswith('//'):
                        continue
                    
                    # Check for class declaration
                    class_match = re.search(class_pattern, next_line)
                    if class_match:
                        class_found = True
                        class_name = class_match.group(1)
                        break
                    
                    # Stop if we hit a blank line or something that's not an annotation/macro
                    if not next_line:
                        continue
                    # Allow annotations and common macros to continue searching
                    is_annotation_or_macro = (
                        re.search(r'///\s*@(Component|Scope|Autowired)\b', next_line) or
                        next_line.startswith(('COMPONENT', 'SCOPE', 'VALIDATE', 'AUTOWIRED'))
                    )
                    if not is_annotation_or_macro:
                        break
            
            scope_macros.append({
                'macro': annotation_text,
                'line_number': line_num,
                'context': context_lines,
                'class_name': class_name,
                'has_class': class_found,
                'scope_value': scope_value,
                'is_valid': scope_value in ['PROTOTYPE', 'SINGLETON']
            })
        
        # Check for legacy SCOPE macro (for backward compatibility)
        legacy_scope_pattern = r'SCOPE\s*\(\s*(PROTOTYPE|SINGLETON)\s*\)'
        legacy_scope_match = re.search(legacy_scope_pattern, stripped_line)
        if legacy_scope_match and not stripped_line.startswith('//') and not stripped_line.startswith('/*'):
            macro_text = legacy_scope_match.group(0)
            scope_value = legacy_scope_match.group(1)
            
            # Look ahead for class declaration
            class_found = False
            class_name = ""
            for i in range(line_num, min(line_num + 6, len(lines) + 1)):
                if i <= len(lines):
                    next_line = lines[i - 1].strip()
                    if next_line.startswith('//') or next_line.startswith('/*'):
                        continue
                    class_match = re.search(class_pattern, next_line)
                    if class_match:
                        class_found = True
                        class_name = class_match.group(1)
                        break
                    if not next_line or (next_line and not next_line.startswith(('COMPONENT', 'SCOPE', 'VALIDATE'))):
                        break
            
            scope_macros.append({
                'macro': macro_text,
                'line_number': line_num,
                'context': [],
                'class_name': class_name,
                'has_class': class_found,
                'scope_value': scope_value,
                'is_valid': scope_value in ['PROTOTYPE', 'SINGLETON']
            })
    
    return scope_macros


def check_scope_macro_exists(file_path: str) -> bool:
    """
    Simple check if @Scope annotation or SCOPE macro exists in the file.
    Supports both new annotation format and legacy macro format for backward compatibility.
    
    Args:
        file_path: Path to the C++ file
        
    Returns:
        True if @Scope annotation or SCOPE macro is found, False otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        scope_annotation_pattern = re.compile(r'///\s*@Scope\s*\(\s*["\'](PROTOTYPE|SINGLETON)["\']\s*\)')
        scope_processed_pattern = re.compile(r'/\*\s*@Scope\s*\(\s*["\'](PROTOTYPE|SINGLETON)["\']\s*\)\s*\*/')
        
        # Check each line for @Scope annotation
        for line in lines:
            stripped_line = line.strip()
            
            # Skip already processed annotations
            if scope_processed_pattern.search(stripped_line):
                continue
            
            # Skip comments (but not annotations)
            if stripped_line.startswith('/*'):
                continue
            if stripped_line.startswith('//') and not scope_annotation_pattern.search(stripped_line):
                continue
                
            # Check if line contains @Scope annotation
            if scope_annotation_pattern.search(stripped_line):
                return True
        
        # Also check for legacy SCOPE macro (for backward compatibility)
        # Check for SCOPE(PROTOTYPE) or SCOPE(SINGLETON) patterns
        content = ''.join(lines)
        legacy_pattern = re.compile(r'SCOPE\s*\(\s*(PROTOTYPE|SINGLETON)\s*\)')
        return bool(legacy_pattern.search(content))
    except Exception:
        return False


def validate_scope_macro_placement(file_path: str) -> Dict[str, any]:
    """
    Comprehensive validation of @Scope annotation placement and usage.
    
    Args:
        file_path: Path to the C++ file
        
    Returns:
        Dictionary with validation results
    """
    scope_macros = find_scope_macros(file_path)
    
    if not scope_macros:
        return {
            'file_path': file_path,
            'has_scope': False,
            'scope_count': 0,
            'valid_placements': 0,
            'invalid_placements': 0,
            'valid_values': 0,
            'invalid_values': 0,
            'issues': ['No @Scope annotation found']
        }
    
    valid_placements = 0
    invalid_placements = 0
    valid_values = 0
    invalid_values = 0
    issues = []
    
    for macro_info in scope_macros:
        # Check placement (must be above class)
        if macro_info['has_class']:
            valid_placements += 1
        else:
            invalid_placements += 1
            issues.append(f"@Scope annotation at line {macro_info['line_number']} not followed by class declaration")
        
        # Check scope value (must be PROTOTYPE or SINGLETON)
        if macro_info['is_valid']:
            valid_values += 1
        else:
            invalid_values += 1
            issues.append(f"@Scope annotation at line {macro_info['line_number']} has invalid value: {macro_info['scope_value']}")
    
    return {
        'file_path': file_path,
        'has_scope': True,
        'scope_count': len(scope_macros),
        'valid_placements': valid_placements,
        'invalid_placements': invalid_placements,
        'valid_values': valid_values,
        'invalid_values': invalid_values,
        'issues': issues,
        'macros': scope_macros
    }


def check_multiple_files(file_paths: List[str]) -> Dict[str, Dict[str, any]]:
    """
    Check SCOPE macro in multiple files.
    
    Args:
        file_paths: List of file paths to check
        
    Returns:
        Dictionary mapping file paths to validation results
    """
    results = {}
    
    for file_path in file_paths:
        results[file_path] = validate_scope_macro_placement(file_path)
    
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
        description="Check if C++ files contain @Scope annotation with valid values (PROTOTYPE/SINGLETON) above class declarations"
    )
    parser.add_argument(
        "files", 
        nargs="+", 
        help="C++ source files to analyze (.cpp, .h, .hpp, etc.)"
    )
    parser.add_argument(
        "--simple", 
        action="store_true",
        help="Simple check: just show if SCOPE exists or not"
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
            has_scope = check_scope_macro_exists(file_path)
            results[file_path] = {'has_scope': has_scope}
            
            # status = "✓ @Scope found" if has_scope else "✗ No @Scope"
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
        #     if result['has_scope']:
        #         print(f"✓ @Scope annotation found ({result['scope_count']} occurrences)")
        #         print(f"  Valid placements: {result['valid_placements']}")
        #         print(f"  Invalid placements: {result['invalid_placements']}")
        #         print(f"  Valid values: {result['valid_values']}")
        #         print(f"  Invalid values: {result['invalid_values']}")
        #         
        #         if args.detailed and result['macros']:
        #             print(f"\n  Detailed annotation information:")
        #             for macro in result['macros']:
        #                 print(f"    Line {macro['line_number']}: {macro['macro']}")
        #                 print(f"      Scope value: {macro['scope_value']}")
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
        #         print("✗ No @Scope annotation found")
        pass
    
    # Show summary if requested
    if args.summary and not args.simple:
        # print(f"\n{'='*60}")
        # print("SUMMARY")
        # print(f"{'='*60}")
        # total_files = len(valid_files)
        # files_with_scope = len([r for r in results.values() if r['has_scope']])
        # total_scopes = sum([r.get('scope_count', 0) for r in results.values()])
        # total_valid_placements = sum([r.get('valid_placements', 0) for r in results.values()])
        # total_invalid_placements = sum([r.get('invalid_placements', 0) for r in results.values()])
        # total_valid_values = sum([r.get('valid_values', 0) for r in results.values()])
        # total_invalid_values = sum([r.get('invalid_values', 0) for r in results.values()])
        # 
        # print(f"Files analyzed: {total_files}")
        # print(f"Files with @Scope: {files_with_scope}")
        # print(f"Files without @Scope: {total_files - files_with_scope}")
        # print(f"Total @Scope annotations: {total_scopes}")
        # print(f"Valid placements: {total_valid_placements}")
        # print(f"Invalid placements: {total_invalid_placements}")
        # print(f"Valid values: {total_valid_values}")
        # print(f"Invalid values: {total_invalid_values}")
        pass
    
    # Save to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            if args.simple:
                for file_path, result in results.items():
                    status = "@Scope found" if result['has_scope'] else "No @Scope"
                    f.write(f"{file_path}: {status}\n")
            else:
                for file_path, result in results.items():
                    f.write(f"{file_path}:\n")
                    if result['has_scope']:
                        f.write(f"  @Scope annotations: {result['scope_count']}\n")
                        f.write(f"  Valid placements: {result['valid_placements']}\n")
                        f.write(f"  Invalid placements: {result['invalid_placements']}\n")
                        f.write(f"  Valid values: {result['valid_values']}\n")
                        f.write(f"  Invalid values: {result['invalid_values']}\n")
                        if result['issues']:
                            f.write(f"  Issues: {', '.join(result['issues'])}\n")
                    else:
                        f.write(f"  No @Scope annotation found\n")
                    f.write("\n")
        # print(f"\nResults saved to: {args.output}")
    
    return results


def mark_scope_annotation_processed(file_path: str) -> bool:
    """
    Mark @Scope annotation as processed in a C++ file.
    Replaces /* @Scope("...") */ with /*--@Scope("...")--*/.
    
    Args:
        file_path: Path to the C++ file to modify
        
    Returns:
        True if file was modified successfully, False otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        scope_annotation_pattern = re.compile(r'/\*\s*@Scope\s*\(\s*["\'](PROTOTYPE|SINGLETON)["\']\s*\)\s*\*/')
        scope_processed_pattern = re.compile(r'/\*--\s*@Scope\s*\(\s*["\'](PROTOTYPE|SINGLETON)["\']\s*\)\s*--\*/')
        
        modified = False
        modified_lines = []
        
        for i, line in enumerate(lines):
            stripped_line = line.strip()
            
            # Skip already processed annotations
            if scope_processed_pattern.search(stripped_line):
                modified_lines.append(line)
                continue
            
            # Check if line contains @Scope annotation
            scope_match = scope_annotation_pattern.search(stripped_line)
            if scope_match:
                indent = len(line) - len(line.lstrip())
                indent_str = line[:indent]
                # Preserve the full annotation with parameter
                full_annotation = scope_match.group(0)
                scope_value = scope_match.group(1)
                processed_line = f"{indent_str}/*--@Scope(\"{scope_value}\")--*/\n"
                modified_lines.append(processed_line)
                modified = True
                continue
            
            # Check for legacy SCOPE macro (for backward compatibility)
            legacy_scope_pattern = re.compile(r'SCOPE\s*\(\s*(PROTOTYPE|SINGLETON)\s*\)')
            legacy_match = legacy_scope_pattern.search(stripped_line)
            if legacy_match and not stripped_line.startswith('//') and not stripped_line.startswith('/*'):
                modified_lines.append('// ' + line)
                modified = True
                continue
            
            modified_lines.append(line)
        
        # Write back to file if modifications were made
        if modified:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.writelines(modified_lines)
            # print(f"✓ Processed @Scope annotation in: {file_path}")
        else:
            # print(f"ℹ No @Scope annotation found to process in: {file_path}")
            pass
        
        return True
        
    except FileNotFoundError:
        # print(f"Error: File '{file_path}' not found")
        return False
    except Exception as e:
        # print(f"Error modifying file '{file_path}': {e}")
        return False


# Export functions for other scripts to import
__all__ = [
    'find_scope_macros',
    'check_scope_macro_exists',
    'validate_scope_macro_placement',
    'check_multiple_files',
    'mark_scope_annotation_processed',
    'main'
]


if __name__ == "__main__":
    # When run as script, execute main and store result
    result = main()
