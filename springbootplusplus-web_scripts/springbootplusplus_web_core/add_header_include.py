#!/usr/bin/env python3
"""
Script to add a #include statement to C++ header files.
Inserts #include "file-full-path" just before the last #endif.
"""

import re
import argparse
from pathlib import Path
from typing import List, Dict, Optional, Tuple


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


def generate_include_statement(header_path: str) -> str:
    """
    Generate the #include statement.
    
    Args:
        header_path: Full path to the header file to include
        
    Returns:
        Generated #include statement string
    """
    return f'#include "{header_path}"\n'


def inject_header_include(file_path: str, header_path: str, dry_run: bool = False) -> Dict[str, any]:
    """
    Inject a #include statement into a C++ file.
    
    Args:
        file_path: Path to the C++ file to modify
        header_path: Full path to the header file to include
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
        # Step 1: Find the last #endif
        endif_line = find_last_endif(file_path)
        if not endif_line:
            results['errors'].append("Could not find #endif in the file")
            return results
        
        line_num, line_content = endif_line
        results['info']['endif_line'] = line_num
        
        # Step 2: Generate the #include statement
        include_statement = generate_include_statement(header_path)
        results['injected_code'] = include_statement
        
        # Step 3: Check if include already exists
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                existing_lines = file.readlines()
            
            # Check if this include already exists
            include_statement_stripped = include_statement.strip()
            for existing_line in existing_lines:
                if existing_line.strip() == include_statement_stripped:
                    results['success'] = True
                    return results
        except Exception as e:
            pass
        
        # Step 4: Inject the code (or show what would be injected)
        if dry_run:
            results['success'] = True
        else:
            # Actually inject the code
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    lines = file.readlines()
                
                # Insert the #include statement before the #endif line
                lines.insert(line_num - 1, include_statement)
                
                # Write back to file
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.writelines(lines)
                
                results['success'] = True
                
            except Exception as e:
                import traceback
                traceback.print_exc()
                results['errors'].append(f"Failed to inject code: {e}")
                return results
        
    except Exception as e:
        results['errors'].append(f"Error processing file: {e}")
    
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
    """Main function to handle command line arguments and execute the injection process."""
    parser = argparse.ArgumentParser(
        description="Add a #include statement to C++ header files just before the last #endif"
    )
    parser.add_argument(
        "file", 
        help="C++ header file to process (.h, .hpp, etc.)"
    )
    parser.add_argument(
        "--header", 
        required=True,
        help="Full path to the header file to include"
    )
    parser.add_argument(
        "--dry-run", 
        action="store_true",
        help="Show what would be injected without modifying files"
    )
    
    args = parser.parse_args()
    
    # Validate C++ file
    if not validate_cpp_file(args.file):
        # print(f"Error: '{args.file}' is not a valid C++ file")
        return False
    
    # Process the file
    results = inject_header_include(args.file, args.header, args.dry_run)
    
    if results['success']:
        if args.dry_run:
            # print("Status: Would inject #include statement successfully")
            pass
        else:
            # print("Status: #include statement injected successfully")
            pass
        return True
    else:
        # print("Status: Failed to inject #include statement")
        if results['errors']:
            # print("Errors:")
            # for error in results['errors']:
            #     print(f"  {error}")
            pass
        return False


# Export functions for other scripts to import
__all__ = [
    'find_last_endif',
    'generate_include_statement',
    'inject_header_include',
    'main'
]


if __name__ == "__main__":
    # When run as script, execute main and store result
    success = main()
    exit(0 if success else 1)
