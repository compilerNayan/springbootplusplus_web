#!/usr/bin/env python3
"""
Script to add implementation template code to C++ header files.
Inserts template specializations for Implementation<InterfaceName> and Implementation<InterfaceName*> 
just before the last #endif.
"""

import re
import argparse
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import find_class_names
import find_interface_names


def find_last_endif(file_path: str) -> Optional[Tuple[int, str]]:
    """
    Find the line containing the last #endif in the file.
    
    Args:
        file_path: Path to the C++ file
        
    Returns:
        Tuple of (line_number, line_content) or None if not found
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
    except FileNotFoundError:
        # print(f"Error: File '{file_path}' not found")
        return None
    except Exception as e:
        # print(f"Error reading file '{file_path}': {e}")
        return None
    
    # Look for the last #endif in the file (with or without comments)
    last_endif_line = None
    for line_num, line in enumerate(lines, 1):
        stripped_line = line.strip()
        if stripped_line.startswith('#endif'):
            last_endif_line = (line_num, line)
    
    return last_endif_line


def generate_implementation_template_code(interface_name: str, class_name: str) -> str:
    """
    Generate the implementation template code.
    
    Args:
        interface_name: Name of the interface
        class_name: Name of the class
        
    Returns:
        Generated template code string to inject
    """
    return f"""template <>
struct Implementation<{interface_name}> {{
    using type = {class_name};
}};

template <>
struct Implementation<{interface_name}*> {{
    using type = {class_name}*;
}};

"""


def inject_implementation_template(file_path: str, dry_run: bool = False) -> Dict[str, any]:
    """
    Inject implementation template code into a C++ file.
    
    Args:
        file_path: Path to the C++ file
        dry_run: If True, only show what would be injected without modifying the file
        
    Returns:
        Dictionary with results and any errors
    """
    results = {
        'success': False,
        'injected_code': '',
        'errors': [],
        'info': {}
    }
    
    try:
        # Step 1: Get class names
        class_names = find_class_names.find_class_names(file_path)
        if not class_names:
            results['errors'].append("No classes found in the file")
            return results
        
        class_name = class_names[0]  # Take the first class
        results['info']['class_name'] = class_name
        # print(f"Class name: {class_name}")
        
        # Step 2: Get interface names
        interface_names = find_interface_names.find_interface_names(file_path)
        if not interface_names:
            results['errors'].append("No interfaces found in the file")
            return results
        
        interface_name = interface_names[0]  # Take the first interface
        results['info']['interface_name'] = interface_name
        # print(f"Interface name: {interface_name}")
        
        # Step 3: Find the last #endif
        endif_line = find_last_endif(file_path)
        if not endif_line:
            results['errors'].append("Could not find #endif in the file")
            return results
        
        line_num, line_content = endif_line
        results['info']['endif_line'] = line_num
        # print(f"Last #endif found at line {line_num}")
        
        # Step 4: Generate the implementation template code
        template_code = generate_implementation_template_code(interface_name, class_name)
        results['injected_code'] = template_code
        # print(f"Generated implementation template code")
        
        # Step 5: Inject the code (or show what would be injected)
        if dry_run:
            # print(f"\nWould inject the following code before line {line_num} (before '#endif'):")
            # print("=" * 60)
            # print(template_code.rstrip())
            # print("=" * 60)
            results['success'] = True
        else:
            # Actually inject the code
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    lines = file.readlines()
                
                # Insert the template code before the #endif line
                lines.insert(line_num - 1, template_code)
                
                # Write back to file
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.writelines(lines)
                
                # print(f"Successfully injected implementation template code before line {line_num}")
                results['success'] = True
                
            except Exception as e:
                results['errors'].append(f"Failed to inject code: {e}")
                return results
        
    except Exception as e:
        results['errors'].append(f"Error processing file: {e}")
    
    return results


def inject_implementation_template_in_files(file_paths: List[str], dry_run: bool = False) -> Dict[str, Dict[str, any]]:
    """
    Inject implementation template code into multiple C++ files.
    
    Args:
        file_paths: List of file paths to process
        dry_run: If True, only show what would be injected without modifying files
        
    Returns:
        Dictionary mapping file paths to results
    """
    all_results = {}
    
    for file_path in file_paths:
        # print(f"\nProcessing: {file_path}")
        results = inject_implementation_template(file_path, dry_run)
        all_results[file_path] = results
        
        # Display results for this file
        if results['success']:
            if dry_run:
                # print("  Status: Would inject implementation template code successfully")
                pass
            else:
                # print("  Status: Implementation template code injected successfully")
                pass
        else:
            # print("  Status: Failed to inject implementation template code")
            if results['errors']:
                # print("  Errors:")
                # for error in results['errors']:
                #     print(f"    {error}")
                pass
    
    return all_results


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
    """Main function to handle command line arguments and execute the injection process."""
    parser = argparse.ArgumentParser(
        description="Add implementation template code to C++ header files"
    )
    parser.add_argument(
        "files", 
        nargs="+", 
        help="C++ header files to process (.h, .hpp, etc.)"
    )
    parser.add_argument(
        "--dry-run", 
        action="store_true",
        help="Show what would be injected without modifying files"
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
    
    # Process all files
    results = inject_implementation_template_in_files(valid_files, args.dry_run)
    
    # Show summary if requested
    if args.summary:
        # print(f"\n=== Summary ===")
        # print(f"Files processed: {len(valid_files)}")
        # print(f"Files with successful injection: {len([r for r in results.values() if r['success']])}")
        # 
        # total_errors = sum(len(r['errors']) for r in results.values())
        # print(f"Total errors: {total_errors}")
        pass
    
    return results


# Export functions for other scripts to import
__all__ = [
    'find_last_endif',
    'generate_implementation_template_code',
    'inject_implementation_template',
    'inject_implementation_template_in_files',
    'main'
]


if __name__ == "__main__":
    # When run as script, execute main and store result
    result = main()
