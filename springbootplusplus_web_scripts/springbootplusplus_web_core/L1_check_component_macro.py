#!/usr/bin/env python3
"""
Script to check if C++ files contain the @Component or @Service annotation above class declarations that inherit from interfaces.
Validates that class inherits from interface and has @Component or @Service annotation.
@Service is treated as an alias for @Component.

This script:
1. Finds @Component or @Service annotations (/* @Component */, /* @Service */, or /*@Component*/, /*@Service*/) that are not processed
2. Validates that classes inherit from interfaces
3. Marks the @Component annotation as processed (/*--@Component--*/) and @Service as processed (/*--@Service--*/)
"""

import re
import argparse
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Set

# Import functions from our other scripts
try:
    from find_class_names import find_class_names
    from find_interface_names import find_interface_names
except ImportError:
    # print("Error: Could not import required modules. Make sure find_class_names.py and find_interface_names.py are in the same directory.")
    sys.exit(1)


def find_component_macros(file_path: str) -> List[Dict[str, str]]:
    """
    Find all @Component or @Service annotations in a C++ file and their context.
    @Service is treated as an alias for @Component.
    
    Args:
        file_path: Path to the C++ file (.cpp, .h, or .hpp)
        
    Returns:
        List of dictionaries with 'macro', 'line_number', 'context', 'class_name', 'has_class', and 'has_interface' keys
    """
    component_macros = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
    except FileNotFoundError:
        # print(f"Error: File '{file_path}' not found")
        return []
    except Exception as e:
        # print(f"Error reading file '{file_path}': {e}")
        return []
    
    # Pattern to match @Component annotation (search for /* @Component */ or /*@Component*/)
    # Also check for already processed /*--@Component--*/ pattern
    component_annotation_pattern = re.compile(r'/\*\s*@Component\s*\*/')
    component_processed_pattern = re.compile(r'/\*--\s*@Component\s*--\*/')
    
    # Pattern to match @Service annotation (alias for @Component)
    # Also check for already processed /*--@Service--*/ pattern
    service_annotation_pattern = re.compile(r'/\*\s*@Service\s*\*/')
    service_processed_pattern = re.compile(r'/\*--\s*@Service\s*--\*/')
    
    # Pattern to match class declarations
    class_pattern = r'class\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:[:{])'
    
    for line_num, line in enumerate(lines, 1):
        stripped_line = line.strip()
        
        # Skip already processed annotations
        if component_processed_pattern.search(stripped_line) or service_processed_pattern.search(stripped_line):
            continue
        
        # Skip other comments that aren't @Component or @Service annotations
        # But allow /* @Component */ or /* @Service */ annotations to be processed
        if stripped_line.startswith('/*') and not component_annotation_pattern.search(stripped_line) and not service_annotation_pattern.search(stripped_line):
            continue
        # Skip single-line comments
        if stripped_line.startswith('//'):
            continue
            
        # Check if line contains valid @Component or @Service annotation
        component_match = component_annotation_pattern.search(stripped_line)
        service_match = service_annotation_pattern.search(stripped_line)
        if component_match or service_match:
            annotation_text = component_match.group(0) if component_match else service_match.group(0)
            
            # Look ahead for class declaration (within next few lines)
            # Allow other annotations/macros to appear between @Component and class
            class_found = False
            class_name = ""
            context_lines = []
            
            # Check next 10 lines for class declaration (allowing for multiple annotations/macros)
            for i in range(line_num, min(line_num + 11, len(lines) + 1)):
                if i <= len(lines):
                    next_line = lines[i - 1].strip()
                    context_lines.append(next_line)
                    
                    # Skip other comments that aren't annotations
                    # But allow /* @Component */, /* @Service */, /* @Scope */, /* @Autowired */ annotations to be processed
                    if next_line.startswith('/*') and not re.search(r'/\*\s*@(Component|Service|Scope|Autowired)\s*\*/', next_line):
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
                        re.search(r'/\*\s*@(Component|Service|Scope|Autowired)\s*\*/', next_line) or
                        next_line.startswith(('COMPONENT', 'SCOPE', 'VALIDATE', 'AUTOWIRED'))
                    )
                    if not is_annotation_or_macro:
                        break
            
            component_macros.append({
                'macro': annotation_text,
                'line_number': line_num,
                'context': context_lines,
                'class_name': class_name,
                'has_class': class_found
            })
        
        # Check for legacy COMPONENT macro (for backward compatibility)
        if re.match(r'^COMPONENT\s*$', stripped_line) and not stripped_line.startswith('//') and not stripped_line.startswith('/*'):
            # Look ahead for class declaration
            class_found = False
            class_name = ""
            context_lines = []
            
            for i in range(line_num, min(line_num + 11, len(lines) + 1)):
                if i <= len(lines):
                    next_line = lines[i - 1].strip()
                    context_lines.append(next_line)
                    
                    if next_line.startswith('//') or next_line.startswith('/*'):
                        continue
                    
                    class_match = re.search(class_pattern, next_line)
                    if class_match:
                        class_found = True
                        class_name = class_match.group(1)
                        break
                    
                    if not next_line or (next_line and not next_line.startswith(('COMPONENT', 'SCOPE', 'VALIDATE'))):
                        break
            
            component_macros.append({
                'macro': 'COMPONENT',
                'line_number': line_num,
                'context': context_lines,
                'class_name': class_name,
                'has_class': class_found
            })
    
    return component_macros


def check_component_macro_exists(file_path: str) -> bool:
    """
    Simple check if @Component or @Service annotation or COMPONENT macro exists in the file.
    Supports both new annotation format and legacy macro format for backward compatibility.
    @Service is treated as an alias for @Component.
    
    Args:
        file_path: Path to the C++ file
        
    Returns:
        True if active @Component or @Service annotation or COMPONENT macro is found, False otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        component_annotation_pattern = re.compile(r'/\*\s*@Component\s*\*/')
        component_processed_pattern = re.compile(r'/\*--\s*@Component\s*--\*/')
        service_annotation_pattern = re.compile(r'/\*\s*@Service\s*\*/')
        service_processed_pattern = re.compile(r'/\*--\s*@Service\s*--\*/')
        
        # Check each line for @Component or @Service annotation or legacy COMPONENT macro
        for line in lines:
            stripped_line = line.strip()
            
            # Skip already processed annotations
            if component_processed_pattern.search(stripped_line) or service_processed_pattern.search(stripped_line):
                continue
            
            # Skip other comments that aren't @Component or @Service annotations
            # But allow /* @Component */ or /* @Service */ annotations to be processed
            if stripped_line.startswith('/*') and not component_annotation_pattern.search(stripped_line) and not service_annotation_pattern.search(stripped_line):
                continue
            # Skip single-line comments
            if stripped_line.startswith('//'):
                continue
                
            # Check if line contains @Component or @Service annotation
            if component_annotation_pattern.search(stripped_line) or service_annotation_pattern.search(stripped_line):
                return True
            
            # Check for legacy COMPONENT macro (for backward compatibility)
            if stripped_line == 'COMPONENT':
                return True
        
        return False
    except Exception:
        return False


def validate_component_macro_requirements(file_path: str) -> Dict[str, any]:
    """
    Comprehensive validation of COMPONENT macro requirements.
    
    Args:
        file_path: Path to the C++ file
        
    Returns:
        Dictionary with validation results
    """
    # Step 1: Get class names from the file
    class_names = find_class_names(file_path)
    
    # Step 2: Get interface names from the file
    interface_names = find_interface_names(file_path)
    
    # Step 3: Find COMPONENT macros
    component_macros = find_component_macros(file_path)
    
    # Step 4: Validate requirements
    has_classes = len(class_names) > 0
    has_interfaces = len(interface_names) > 0
    has_component_macro = len(component_macros) > 0
    
    # Check if classes inherit from interfaces
    classes_with_inheritance = []
    for class_name in class_names:
        if interface_names:  # If there are interfaces, assume inheritance
            classes_with_inheritance.append(class_name)
    
    # All three conditions must be met:
    # 1. Has COMPONENT macro
    # 2. Has class names
    # 3. Has interface names (meaning classes inherit from interfaces)
    all_requirements_met = has_component_macro and has_classes and has_interfaces and len(classes_with_inheritance) > 0
    
    # Build validation result
    validation_result = {
        'file_path': file_path,
        'has_component_macro': has_component_macro,
        'has_classes': has_classes,
        'has_interfaces': has_interfaces,
        'classes_with_inheritance': classes_with_inheritance,
        'all_requirements_met': all_requirements_met,
        'component_macros': component_macros,
        'class_names': class_names,
        'interface_names': interface_names,
        'status': 'valid' if all_requirements_met else 'invalid'
    }
    
    return validation_result


def check_multiple_files(file_paths: List[str]) -> Dict[str, Dict[str, any]]:
    """
    Check COMPONENT macro requirements in multiple files.
    
    Args:
        file_paths: List of file paths to check
        
    Returns:
        Dictionary mapping file paths to validation results
    """
    results = {}
    
    for file_path in file_paths:
        results[file_path] = validate_component_macro_requirements(file_path)
    
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


def comment_component_macro(file_path: str) -> bool:
    """
    Mark @Component or @Service annotation as processed in a C++ file.
    Replaces /* @Component */ with /*--@Component--*/ and /* @Service */ with /*--@Service--*/.
    
    Args:
        file_path: Path to the C++ file to modify
        
    Returns:
        True if file was modified successfully, False otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        component_annotation_pattern = re.compile(r'/\*\s*@Component\s*\*/')
        component_processed_pattern = re.compile(r'/\*--\s*@Component\s*--\*/')
        service_annotation_pattern = re.compile(r'/\*\s*@Service\s*\*/')
        service_processed_pattern = re.compile(r'/\*--\s*@Service\s*--\*/')
        
        modified = False
        modified_lines = []
        
        for i, line in enumerate(lines):
            stripped_line = line.strip()
            
            # Skip already processed annotations
            if component_processed_pattern.search(stripped_line) or service_processed_pattern.search(stripped_line):
                modified_lines.append(line)
                continue
            
            # Check if line contains @Component annotation
            component_match = component_annotation_pattern.search(stripped_line)
            if component_match:
                indent = len(line) - len(line.lstrip())
                indent_str = line[:indent]
                processed_line = f"{indent_str}/*--@Component--*/\n"
                modified_lines.append(processed_line)
                modified = True
                continue
            
            # Check if line contains @Service annotation
            service_match = service_annotation_pattern.search(stripped_line)
            if service_match:
                indent = len(line) - len(line.lstrip())
                indent_str = line[:indent]
                processed_line = f"{indent_str}/*--@Service--*/\n"
                modified_lines.append(processed_line)
                modified = True
                continue
            
            # Check for legacy COMPONENT macro (for backward compatibility)
            if re.match(r'^COMPONENT\s*$', stripped_line):
                modified_lines.append('// ' + line)
                modified = True
                continue
            
            modified_lines.append(line)
        
        # Write back to file if modifications were made
        if modified:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.writelines(modified_lines)
            # print(f"✓ Processed @Component annotation in: {file_path}")
        else:
            # print(f"ℹ No @Component annotation found to process in: {file_path}")
            pass
        
        return True
        
    except FileNotFoundError:
        # print(f"Error: File '{file_path}' not found")
        return False
    except Exception as e:
        # print(f"Error modifying file '{file_path}': {e}")
        return False


def comment_component_macros_in_multiple_files(file_paths: List[str]) -> Dict[str, bool]:
    """
    Comment out COMPONENT macros in multiple files.
    
    Args:
        file_paths: List of file paths to modify
        
    Returns:
        Dictionary mapping file paths to success status
    """
    results = {}
    
    for file_path in file_paths:
        results[file_path] = comment_component_macro(file_path)
    
    return results


def main():
    """Main function to handle command line arguments and execute the validation."""
    parser = argparse.ArgumentParser(
        description="Check if C++ files contain @Component annotation above class declarations that inherit from interfaces"
    )
    parser.add_argument(
        "files", 
        nargs="+", 
        help="C++ source files to analyze (.cpp, .h, .hpp, etc.)"
    )
    parser.add_argument(
        "--simple", 
        action="store_true",
        help="Simple check: just show if COMPONENT exists or not"
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
            has_component = check_component_macro_exists(file_path)
            results[file_path] = {'has_component': has_component}
            
            # status = "✓ @Component found" if has_component else "✗ No @Component"
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
        #     if result['has_component_macro']:
        #         print(f"✓ @Component annotation found ({len(result['component_macros'])} occurrences)")
        #         print(f"  Classes found: {', '.join(result['class_names']) if result['class_names'] else 'None'}")
        #         print(f"  Interfaces found: {', '.join(result['interface_names']) if result['interface_names'] else 'None'}")
        #         print(f"  Classes with inheritance: {', '.join(result['classes_with_inheritance']) if result['classes_with_inheritance'] else 'None'}")
        #         
        #         if result['all_requirements_met']:
        #             print(f"  Status: ✓ All requirements met - @Component annotation is valid")
        #         else:
        #             print(f"  Status: ✗ Requirements not met - @Component annotation has no significance")
        #         
        #         if args.detailed and result['component_macros']:
        #             print(f"\n  Detailed annotation information:")
        #             for macro in result['component_macros']:
        #                 print(f"    Line {macro['line_number']}: {macro['macro']}")
        #                 if macro['has_class']:
        #                     print(f"      → Class: {macro['class_name']}")
        #                 else:
        #                     print(f"      → No class found")
        #     else:
        #         print("✗ No @Component annotation found")
        pass
    
    # Show summary if requested
    if args.summary and not args.simple:
        # print(f"\n{'='*60}")
        # print("SUMMARY")
        # print(f"{'='*60}")
        # total_files = len(valid_files)
        # files_with_component = len([r for r in results.values() if r['has_component_macro']])
        # files_with_valid_component = len([r for r in results.values() if r.get('all_requirements_met', False)])
        # 
        # print(f"Files analyzed: {total_files}")
        # print(f"Files with @Component annotation: {files_with_component}")
        # print(f"Files with valid @Component annotation: {files_with_valid_component}")
        # print(f"Files with invalid @Component annotation: {files_with_component - files_with_valid_component}")
        pass
    
    # Save to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            if args.simple:
                for file_path, result in results.items():
                    status = "@Component found" if result['has_component'] else "No @Component"
                    f.write(f"{file_path}: {status}\n")
            else:
                for file_path, result in results.items():
                    f.write(f"{file_path}:\n")
                    if result['has_component_macro']:
                        f.write(f"  @Component annotations: {len(result['component_macros'])}\n")
                        f.write(f"  Classes: {', '.join(result['class_names']) if result['class_names'] else 'None'}\n")
                        f.write(f"  Interfaces: {', '.join(result['interface_names']) if result['interface_names'] else 'None'}\n")
                        f.write(f"  Valid: {result['all_requirements_met']}\n")
                    else:
                        f.write(f"  No @Component annotation found\n")
                    f.write("\n")
        # print(f"\nResults saved to: {args.output}")
    
    return results


# Export functions for other scripts to import
__all__ = [
    'find_component_macros',
    'check_component_macro_exists',
    'validate_component_macro_requirements',
    'check_multiple_files',
    'comment_component_macro',
    'comment_component_macros_in_multiple_files',
    'main'
]


if __name__ == "__main__":
    # When run as script, execute main and store result
    result = main()
