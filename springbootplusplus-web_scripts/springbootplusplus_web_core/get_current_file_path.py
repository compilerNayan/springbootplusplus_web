#!/usr/bin/env python3
"""
Script to get the full absolute path of input files.
Returns the resolved absolute paths for other scripts to consume.
"""

import os
import sys
import argparse
from pathlib import Path


def get_file_path(file_path: str) -> str:
    """
    Get the full absolute path of a given file.
    
    Args:
        file_path: Path to the file (can be relative or absolute)
        
    Returns:
        Absolute path of the file
    """
    # Convert to absolute path and resolve any symlinks
    absolute_path = os.path.abspath(file_path)
    resolved_path = os.path.realpath(absolute_path)
    
    return resolved_path


def get_directory_path(file_path: str) -> str:
    """
    Get the full absolute path of the directory containing the given file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Absolute path of the directory containing the file
    """
    file_abs_path = get_file_path(file_path)
    directory_path = os.path.dirname(file_abs_path)
    
    return directory_path


def get_relative_path_from_root(file_path: str, root_dir: str = ".") -> str:
    """
    Get the relative path of a file from a specified root directory.
    
    Args:
        file_path: Path to the file
        root_dir: Root directory to calculate relative path from (default: current working directory)
        
    Returns:
        Relative path from root directory to the file
    """
    file_abs_path = get_file_path(file_path)
    root_path = os.path.abspath(root_dir)
    
    try:
        relative_path = os.path.relpath(file_abs_path, root_path)
        return relative_path
    except ValueError:
        # If file is not under root directory
        return file_abs_path


def get_current_file_path() -> str:
    """
    Get the full absolute path of the current source file.
    
    Returns:
        Absolute path of the current file
    """
    # Get the path of the current file
    current_file = __file__
    
    # Convert to absolute path and resolve any symlinks
    absolute_path = os.path.abspath(current_file)
    resolved_path = os.path.realpath(absolute_path)
    
    return resolved_path


def get_current_directory_path() -> str:
    """
    Get the full absolute path of the directory containing the current file.
    
    Returns:
        Absolute path of the current directory
    """
    current_file_path = get_current_file_path()
    directory_path = os.path.dirname(current_file_path)
    
    return directory_path


def main():
    """Main function to display file path information."""
    parser = argparse.ArgumentParser(
        description="Get full absolute paths of input files"
    )
    parser.add_argument(
        "files", 
        nargs="+", 
        help="Files to get paths for"
    )
    parser.add_argument(
        "--root", 
        default=".", 
        help="Root directory for relative path calculation (default: current directory)"
    )
    
    args = parser.parse_args()
    
    # Process each input file
    file_paths = []
    
    for file_path in args.files:
        # print(f"\nFile: {file_path}")
        # print(f"  Absolute path: {get_file_path(file_path)}")
        # print(f"  Directory: {get_directory_path(file_path)}")
        
        # Show relative path from specified root
        try:
            relative_path = get_relative_path_from_root(file_path, args.root)
            # print(f"  Relative path from {args.root}: {relative_path}")
        except Exception as e:
            # print(f"  Could not calculate relative path: {e}")
            pass
        
        file_paths.append(get_file_path(file_path))
    
    # If only one file, return its path; otherwise return list of paths
    if len(file_paths) == 1:
        return file_paths[0]
    else:
        return file_paths


# Export functions for other scripts to import
__all__ = [
    'get_file_path',
    'get_directory_path',
    'get_relative_path_from_root',
    'get_current_file_path',
    'get_current_directory_path', 
    'main'
]


if __name__ == "__main__":
    # When run as script, execute main and store result
    result_paths = main()
