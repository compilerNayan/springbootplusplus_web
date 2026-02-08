#!/usr/bin/env python3
"""
Script to comment out interface header includes in C++ files.
Finds class names and interface names, then locates and comments out the corresponding #include statements.
"""

import re
import argparse
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import find_class_names
import find_interface_names


def find_interface_header_include(file_path: str, interface_name: str) -> List[Tuple[int, str]]:
    """
    Find lines that include the interface header file.
    
    Args:
        file_path: Path to the C++ file
        interface_name: Name of the interface to search for
        
    Returns:
        List of tuples (line_number, line_content) for matching include statements
    """
    include_lines = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
    except FileNotFoundError:
        # print(f"Error: File '{file_path}' not found")
        return []
    except Exception as e:
        # print(f"Error reading file '{file_path}': {e}")
        return []
    
    # Pattern to match #include statements containing interface name (case insensitive)
    # Matches various include patterns:
    # - #include "path/to/InterfaceName.h"
    # - #include <path/to/InterfaceName.hpp>
    # - #include INTERFACE "path/to/InterfaceName.h"
    # - #include CUSTOM_MACRO "path/to/InterfaceName.h"
    # The interface name can be anywhere in the path, before the extension
    include_pattern = rf'^\s*#include\s+(?:\w+\s+)?[<"][^>"]*{re.escape(interface_name)}\.(?:h|hpp)\s*[>"]\s*$'
    
    for line_num, line in enumerate(lines, 1):
        if re.match(include_pattern, line, re.IGNORECASE):
            include_lines.append((line_num, line.rstrip()))
    
    return include_lines


def comment_interface_header_includes(file_path: str, dry_run: bool = False) -> Dict[str, List[str]]:
    """
    Comment out interface header includes in a C++ file.
    
    Args:
        file_path: Path to the C++ file
        dry_run: If True, only show what would be changed without modifying the file
        
    Returns:
        Dictionary with 'commented_includes' and 'errors' keys
    """
    results = {
        'commented_includes': [],
        'errors': []
    }
    
    try:
        # Get class names from the file
        class_names = find_class_names.get_class_names_from_file(file_path)
        if not class_names:
            results['errors'].append("No classes found in the file")
            return results
        
        # Get interface names from the file
        interface_names = find_interface_names.find_interface_names(file_path)
        if not interface_names:
            results['errors'].append("No interfaces found in the file")
            return results
        
        # Find and comment out interface header includes
        for interface_name in interface_names:
            include_lines = find_interface_header_include(file_path, interface_name)
            
            if include_lines:
                for line_num, line_content in include_lines:
                    if dry_run:
                        results['commented_includes'].append(f"Would comment line {line_num}: {line_content}")
                    else:
                        # Actually comment out the line
                        try:
                            with open(file_path, 'r', encoding='utf-8') as file:
                                lines = file.readlines()
                            
                            # Add comment prefix
                            lines[line_num - 1] = f"// {line_content}\n"
                            
                            # Write back to file
                            with open(file_path, 'w', encoding='utf-8') as file:
                                file.writelines(lines)
                            
                            results['commented_includes'].append(f"Commented line {line_num}: {line_content}")
                            
                        except Exception as e:
                            results['errors'].append(f"Failed to comment line {line_num}: {e}")
            else:
                results['errors'].append(f"No include statement found for interface: {interface_name}")
        
    except Exception as e:
        results['errors'].append(f"Error processing file: {e}")
    
    return results


def comment_interface_headers_in_files(file_paths: List[str], dry_run: bool = False) -> Dict[str, Dict[str, List[str]]]:
    """
    Comment out interface header includes in multiple C++ files.
    
    Args:
        file_paths: List of file paths to process
        dry_run: If True, only show what would be changed without modifying files
        
    Returns:
        Dictionary mapping file paths to results
    """
    all_results = {}
    
    for file_path in file_paths:
        # print(f"\nProcessing: {file_path}")
        results = comment_interface_header_includes(file_path, dry_run)
        all_results[file_path] = results
        
        # Display results for this file
        if results['commented_includes']:
            # print("  Commented includes:")
            # for include in results['commented_includes']:
            #     print(f"    {include}")
            pass
        
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
    """Main function to handle command line arguments and execute the commenting process."""
    parser = argparse.ArgumentParser(
        description="Comment out interface header includes in C++ files"
    )
    parser.add_argument(
        "files", 
        nargs="+", 
        help="C++ source files to process (.cpp, .h, .hpp, etc.)"
    )
    parser.add_argument(
        "--dry-run", 
        action="store_true",
        help="Show what would be changed without modifying files"
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
    results = comment_interface_headers_in_files(valid_files, args.dry_run)
    
    # Show summary if requested
    if args.summary:
        # print(f"\n=== Summary ===")
        # print(f"Files processed: {len(valid_files)}")
        # print(f"Files with changes: {len([r for r in results.values() if r['commented_includes']])}")
        # 
        # total_commented = sum(len(r['commented_includes']) for r in results.values())
        # total_errors = sum(len(r['errors']) for r in results.values())
        # 
        # print(f"Total includes commented: {total_commented}")
        # print(f"Total errors: {total_errors}")
        pass
    
    return results


# Export functions for other scripts to import
__all__ = [
    'find_interface_header_include',
    'comment_interface_header_includes',
    'comment_interface_headers_in_files',
    'main'
]


if __name__ == "__main__":
    # When run as script, execute main and store result
    result = main()
