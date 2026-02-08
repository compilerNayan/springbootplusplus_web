#!/usr/bin/env python3
"""
Script to include validator header files by finding validator names and their header files.
Comments out VALIDATE macros and adds include statements for validator headers.
"""

import os
import sys
import re
import argparse
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

# Import functions from our other scripts
try:
    from L1_get_validator_name import get_validator_name, get_validator_info
    from find_interface_names import find_interface_names
    from find_cpp_files import find_cpp_files
except ImportError:
    # print("Error: Could not import required modules. Make sure L1_get_validator_name.py, find_interface_names.py, and find_cpp_files.py are in the same directory.")
    sys.exit(1)


def find_validator_header_path(validator_name: str, search_root: str = ".", include_folders: Optional[List[str]] = None, exclude_folders: Optional[List[str]] = None) -> Optional[str]:
    """
    Find the header file path for a validator class.
    
    Args:
        validator_name: Name of the validator class
        search_root: Root directory to search for validator headers
        include_folders: List of folders to include in search
        exclude_folders: List of folders to exclude from search
        
    Returns:
        Path to the validator header file, or None if not found
        
    Note:
        This function uses find_cpp_files.py and find_interface_names.py to locate validator headers.
    """
    # Use find_cpp_files to get all C++ files with include/exclude options
    all_files = find_cpp_files(
        root_dir=search_root,
        include_folders=include_folders,
        exclude_folders=exclude_folders
    )
    
    # Look for files ending with <validator_name>.h or <validator_name>.hpp
    potential_headers = []
    
    for file_path in all_files:
        file_name = Path(file_path).name.lower()
        
        # Check if file name matches validator name
        if (file_name.endswith(f"{validator_name.lower()}.h") or 
            file_name.endswith(f"{validator_name.lower()}.hpp")):
            potential_headers.append(file_path)
    
    if not potential_headers:
        # print(f"Warning: No header files found for validator '{validator_name}'")
        return None
    
    # If multiple headers found, prefer .h over .hpp
    preferred_headers = [h for h in potential_headers if h.lower().endswith('.h')]
    if preferred_headers:
        return preferred_headers[0]
    
    # Return the first one found
    return potential_headers[0]


def process_file_with_validator_include(file_path: str, search_root: str = ".", include_folders: Optional[List[str]] = None, exclude_folders: Optional[List[str]] = None, dry_run: bool = False) -> Dict[str, Any]:
    """
    Process a file to include validator headers and comment out VALIDATE macros.
    
    Args:
        file_path: Path to the C++ file to process
        search_root: Root directory to search for validator headers
        include_folders: List of folders to include in search
        exclude_folders: List of folders to exclude from search
        dry_run: If True, don't modify the file, just show what would be done
        
    Returns:
        Dictionary with processing results
    """
    # Step 1: Get validator information
    validator_info = get_validator_info(file_path)
    
    if not validator_info or not validator_info['validator_name']:
        return {
            'file_path': file_path,
            'has_validator': False,
            'validator_name': None,
            'validator_header': None,
            'changes_made': [],
            'status': 'no_validator'
        }
    
    validator_name = validator_info['validator_name']
    # print(f"Found validator: {validator_name}")
    
    # Step 2: Find validator header file
    validator_header = find_validator_header_path(
        validator_name, 
        search_root, 
        include_folders, 
        exclude_folders
    )
    
    if not validator_header:
        return {
            'file_path': file_path,
            'has_validator': True,
            'validator_name': validator_name,
            'validator_header': None,
            'changes_made': [],
            'status': 'validator_header_not_found'
        }
    
    # print(f"Found validator header: {validator_header}")
    
    # Step 3: Read the file and process VALIDATE macros
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
    except Exception as e:
        # print(f"Error reading file '{file_path}': {e}")
        return {
            'file_path': file_path,
            'has_validator': True,
            'validator_name': validator_name,
            'validator_header': validator_header,
            'changes_made': [],
            'status': 'read_error',
            'error': str(e)
        }
    
    # Step 4: Process each line to find and modify VALIDATE macros
    modified_lines = []
    changes_made = []
    
    for line_num, line in enumerate(lines, 1):
        stripped_line = line.strip()
        
        # Check for VALIDATE macro (standalone or with parameter)
        if stripped_line == 'VALIDATE' or stripped_line.startswith('VALIDATE('):
            # Comment out the VALIDATE macro and add include
            original_line = line.rstrip()
            include_statement = f"#include \"{validator_header}\""
            
            if dry_run:
                # For dry run, just show what would be changed
                new_line = f"/* {original_line} */ {include_statement}\n"
                changes_made.append({
                    'line_number': line_num,
                    'original': original_line,
                    'new': new_line.rstrip(),
                    'type': 'validator_include'
                })
                modified_lines.append(new_line)
            else:
                # Actually modify the line
                new_line = f"/* {original_line} */ {include_statement}\n"
                modified_lines.append(new_line)
                changes_made.append({
                    'line_number': line_num,
                    'original': original_line,
                    'new': new_line.rstrip(),
                    'type': 'validator_include'
                })
        else:
            # Keep the line unchanged
            modified_lines.append(line)
    
    # Step 5: Write the modified file (if not dry run)
    if not dry_run and changes_made:
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.writelines(modified_lines)
            # print(f"Modified file: {file_path}")
        except Exception as e:
            # print(f"Error writing file '{file_path}': {e}")
            return {
                'file_path': file_path,
                'has_validator': True,
                'validator_name': validator_name,
                'validator_header': validator_header,
                'changes_made': changes_made,
                'status': 'write_error',
                'error': str(e)
            }
    
    return {
        'file_path': file_path,
        'has_validator': True,
        'validator_name': validator_name,
        'validator_header': validator_header,
        'changes_made': changes_made,
        'status': 'success' if changes_made else 'no_changes_needed'
    }


def process_multiple_files(file_paths: List[str], search_root: str = ".", include_folders: Optional[List[str]] = None, exclude_folders: Optional[List[str]] = None, dry_run: bool = False) -> Dict[str, Dict[str, Any]]:
    """
    Process multiple files to include validator headers.
    
    Args:
        file_paths: List of file paths to process
        search_root: Root directory to search for validator headers
        include_folders: List of folders to include in search
        exclude_folders: List of folders to exclude from search
        dry_run: If True, don't modify files, just show what would be done
        
    Returns:
        Dictionary mapping file paths to processing results
    """
    results = {}
    
    for file_path in file_paths:
        # print(f"\n{'='*60}")
        # print(f"Processing: {file_path}")
        # print(f"{'='*60}")
        
        result = process_file_with_validator_include(
            file_path, 
            search_root, 
            include_folders, 
            exclude_folders, 
            dry_run
        )
        results[file_path] = result
        
        # Display results
        # if result['has_validator']:
        #     print(f"Validator: {result['validator_name']}")
        #     if result['validator_header']:
        #         print(f"Header: {result['validator_header']}")
        #         if result['changes_made']:
        #             print(f"Changes made: {len(result['changes_made'])}")
        #             for change in result['changes_made']:
        #                 print(f"  Line {change['line_number']}: {change['original']} → {change['new']}")
        #         else:
        #             print("No changes needed")
        #     else:
        #         print("Validator header not found")
        # else:
        #     print("No validator found")
    
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
    """Main function to handle command line arguments and execute the processing."""
    parser = argparse.ArgumentParser(
        description="Include validator header files and comment out VALIDATE macros"
    )
    parser.add_argument(
        "files", 
        nargs="+", 
        help="C++ source files to process (.cpp, .h, .hpp, etc.)"
    )
    parser.add_argument(
        "--search-root", 
        default=".", 
        help="Root directory to search for validator headers (default: current directory)"
    )
    parser.add_argument(
        "--include", 
        nargs="+", 
        help="Folders to include in search (can be multiple)"
    )
    parser.add_argument(
        "--exclude", 
        nargs="+", 
        help="Folders to exclude from search (can be multiple)"
    )
    parser.add_argument(
        "--dry-run", 
        action="store_true",
        help="Show what would be changed without modifying files"
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
    
    # Process files
    if len(valid_files) == 1:
        # Single file
        file_path = valid_files[0]
        result = process_file_with_validator_include(
            file_path, 
            args.search_root, 
            args.include, 
            args.exclude, 
            args.dry_run
        )
        results = {file_path: result}
    else:
        # Multiple files
        results = process_multiple_files(
            valid_files, 
            args.search_root, 
            args.include, 
            args.exclude, 
            args.dry_run
        )
    
    # Show summary if requested
    if args.summary:
        # print(f"\n{'='*60}")
        # print("SUMMARY")
        # print(f"{'='*60}")
        # 
        # total_files = len(valid_files)
        # files_with_validator = len([r for r in results.values() if r['has_validator']])
        # files_modified = len([r for r in results.values() if r['status'] == 'success'])
        # files_no_changes = len([r for r in results.values() if r['status'] == 'no_changes_needed'])
        # files_errors = len([r for r in results.values() if 'error' in r])
        # 
        # print(f"Files analyzed: {total_files}")
        # print(f"Files with validator: {files_with_validator}")
        # print(f"Files modified: {files_modified}")
        # print(f"Files no changes needed: {files_no_changes}")
        # print(f"Files with errors: {files_errors}")
        # 
        # if args.dry_run:
        #     print(f"\nDRY RUN MODE - No files were actually modified")
        pass
    
    # Save to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            for file_path, result in results.items():
                f.write(f"{file_path}:\n")
                if result['has_validator']:
                    f.write(f"  Validator: {result['validator_name']}\n")
                    if result['validator_header']:
                        f.write(f"  Header: {result['validator_header']}\n")
                    f.write(f"  Status: {result['status']}\n")
                    if result['changes_made']:
                        f.write(f"  Changes: {len(result['changes_made'])}\n")
                        for change in result['changes_made']:
                            f.write(f"    Line {change['line_number']}: {change['original']} → {change['new']}\n")
                else:
                    f.write(f"  No validator found\n")
                f.write("\n")
        # print(f"\nResults saved to: {args.output}")
    
    return results


# Export functions for other scripts to import
__all__ = [
    'find_validator_header_path',
    'process_file_with_validator_include',
    'process_multiple_files',
    'main'
]


if __name__ == "__main__":
    # When run as script, execute main and store result
    result = main()
