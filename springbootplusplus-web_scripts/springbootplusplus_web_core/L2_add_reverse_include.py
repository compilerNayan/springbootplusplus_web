#!/usr/bin/env python3
"""
Script to add reverse include - finds interface header and adds current file as include.
Gets interface name, finds interface header path, then adds current file as include to that header.
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import find_interface_names
import L1_find_class_header
import get_current_file_path

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def get_interface_name_from_file(file_path: str) -> Optional[str]:
    """
    Get the interface name from a C++ file using find_interface_names script.
    
    Args:
        file_path: Path to the C++ file
        
    Returns:
        Interface name if found, None otherwise
    """
    try:
        interface_names = find_interface_names.find_interface_names(file_path)
        if interface_names:
            return interface_names[0]  # Take the first interface
        return None
    except Exception as e:
        return None


def find_interface_header_path(interface_name: str, include_paths: List[str], exclude_paths: List[str]) -> Optional[str]:
    """
    Find the interface header file path using L1_find_class_header function.
    
    Args:
        interface_name: Name of the interface to search for
        include_paths: List of include paths to search in
        exclude_paths: List of exclude paths to avoid
        
    Returns:
        Full path to the interface header file if found, None otherwise
    """
    try:
        # Use the function directly instead of calling as subprocess
        # Determine search root - use the script directory as default
        search_root = SCRIPT_DIR
        
        # Call the function directly
        header_path = L1_find_class_header.find_class_header_file(
            class_name=interface_name,
            search_root=search_root,
            include_folders=include_paths if include_paths else None,
            exclude_folders=exclude_paths if exclude_paths else None
        )
        
        return header_path
            
    except Exception as e:
        return None


def get_current_file_info(file_path: str) -> Optional[Dict[str, str]]:
    """
    Get current file information using get_current_file_path script.
    
    Args:
        file_path: Path to the current file
        
    Returns:
        Dictionary with file information or None if failed
    """
    try:
        # Get current file path information
        current_file_info = get_current_file_path.get_file_info(file_path)
        return current_file_info
    except Exception as e:
        # print(f"Error getting current file info: {e}")
        return None


def add_header_include(target_file: str, header_to_include: str, dry_run: bool = False) -> bool:
    """
    Add header include using the add_header_include script.
    
    Args:
        target_file: Target file to add include to
        header_to_include: Header file to include
        dry_run: If True, only show what would be done
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Build the command for add_header_include
        script_path = os.path.join(SCRIPT_DIR, 'add_header_include.py')
        cmd = ['python', script_path, target_file, '--header', header_to_include]
        
        if dry_run:
            cmd.append('--dry-run')
        
        # Execute the command
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
        
        if result.returncode == 0:
            return True
        else:
            return False
            
    except Exception as e:
        return False


def process_file(file_path: str, include_paths: List[str], exclude_paths: List[str], dry_run: bool = False) -> Dict[str, any]:
    """
    Process a single file to add reverse include.
    
    Args:
        file_path: Path to the C++ file to process
        include_paths: List of include paths to search in
        exclude_paths: List of exclude paths to avoid
        dry_run: If True, only show what would be done
        
    Returns:
        Dictionary with results and any errors
    """
    results = {
        'success': False,
        'interface_name': None,
        'interface_header_file': None,
        'current_file_info': None,
        'errors': [],
        'info': {}
    }
    
    try:
        # Step 1: Get interface name
        interface_name = get_interface_name_from_file(file_path)
        if not interface_name:
            results['errors'].append("No interface name found in the file")
            return results
        
        results['interface_name'] = interface_name
        
        # Step 2: Find interface header path
        interface_header_file = find_interface_header_path(interface_name, include_paths, exclude_paths)
        if not interface_header_file:
            results['errors'].append(f"Could not find header file for interface: {interface_name}")
            return results
        
        results['interface_header_file'] = interface_header_file
        
        # Step 3: Get current file information
        current_file_path = get_current_file_path.get_file_path(file_path)
        if not current_file_path:
            results['errors'].append("Could not get current file path")
            return results
        
        results['current_file_info'] = {'absolute_path': current_file_path}
        
        # Step 4: Add header include
        success = add_header_include(interface_header_file, current_file_path, dry_run)
        if success:
            results['success'] = True
        else:
            results['errors'].append("Failed to add header include")
        
    except Exception as e:
        results['errors'].append(f"Error processing file: {e}")
    
    return results


def process_multiple_files(file_paths: List[str], include_paths: List[str], exclude_paths: List[str], dry_run: bool = False) -> Dict[str, Dict[str, any]]:
    """
    Process multiple files to add reverse includes.
    
    Args:
        file_paths: List of file paths to process
        include_paths: List of include paths to search in
        exclude_paths: List of exclude paths to avoid
        dry_run: If True, only show what would be done
        
    Returns:
        Dictionary mapping file paths to results
    """
    all_results = {}
    
    for file_path in file_paths:
        results = process_file(file_path, include_paths, exclude_paths, dry_run)
        all_results[file_path] = results
        
        # Display results for this file
        if results['success']:
            if dry_run:
                # print(f"  Status: Would process successfully")
                pass
            else:
                # print(f"  Status: Processed successfully")
                pass
        else:
            # print(f"  Status: Failed to process")
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
    """Main function to handle command line arguments and execute the reverse include process."""
    parser = argparse.ArgumentParser(
        description="Add reverse include - find interface header and add current file as include"
    )
    parser.add_argument(
        "files", 
        nargs="+", 
        help="C++ source files to process (.cpp, .h, .hpp, etc.)"
    )
    parser.add_argument(
        "--include", 
        nargs="+",
        default=[],
        help="Include paths to search in (can be multiple paths)"
    )
    parser.add_argument(
        "--exclude", 
        nargs="+",
        default=[],
        help="Exclude paths to avoid (can be multiple paths)"
    )
    parser.add_argument(
        "--dry-run", 
        action="store_true",
        help="Show what would be done without modifying files"
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
    results = process_multiple_files(valid_files, args.include, args.exclude, args.dry_run)
    
    # Show summary if requested
    if args.summary:
        # print(f"\n=== Summary ===")
        # print(f"Files processed: {len(valid_files)}")
        # print(f"Files with successful processing: {len([r for r in results.values() if r['success']])}")
        # print(f"Include paths: {args.include if args.include else ['default']}")
        # print(f"Exclude paths: {args.exclude if args.exclude else ['none']}")
        # 
        # total_errors = sum(len(r['errors']) for r in results.values())
        # print(f"Total errors: {total_errors}")
        pass
    
    return results


# Export functions for other scripts to import
__all__ = [
    'get_interface_name_from_file',
    'find_interface_header_path',
    'get_current_file_info',
    'add_header_include',
    'process_file',
    'process_multiple_files',
    'main'
]


if __name__ == "__main__":
    # When run as script, execute main and store result
    result = main()
