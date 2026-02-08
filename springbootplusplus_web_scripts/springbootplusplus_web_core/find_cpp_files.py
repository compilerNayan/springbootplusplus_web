#!/usr/bin/env python3
"""
Script to find C++ source files with include/exclude folder options.
Returns results in a format that other Python scripts can consume.
"""

import os
import argparse
from pathlib import Path
from typing import List, Set, Optional


def find_cpp_files(
    root_dir: str = ".",
    include_folders: Optional[List[str]] = None,
    exclude_folders: Optional[List[str]] = None
) -> List[str]:
    """
    Find all C++ source files in the specified directories.
    
    Args:
        root_dir: Root directory to start searching from
        include_folders: List of folders to include (if None, search all)
        exclude_folders: List of folders to exclude from search
        
    Returns:
        List of absolute paths to C++ source files
    """
    cpp_extensions = {'.cpp', '.h', '.hpp'}
    found_files = []
    
    # Convert to Path objects for easier manipulation
    root_path = Path(root_dir).resolve()
    
    # Normalize include folders
    if include_folders:
        include_paths = [root_path / folder for folder in include_folders]
    else:
        include_paths = [root_path]
    
    # Normalize exclude folders
    exclude_paths = set()
    if exclude_folders:
        for exclude_folder in exclude_folders:
            # Handle both absolute and relative paths
            if os.path.isabs(exclude_folder):
                exclude_paths.add(Path(exclude_folder))
            else:
                exclude_paths.add(root_path / exclude_folder)
    
    def should_exclude(path: Path) -> bool:
        """Check if a path should be excluded."""
        for exclude_path in exclude_paths:
            try:
                # Check if the path is within any excluded directory
                if path.resolve().is_relative_to(exclude_path):
                    return True
            except ValueError:
                # Path is not relative to exclude_path, continue checking
                pass
        return False
    
    # Search through include folders
    for include_path in include_paths:
        if not include_path.exists():
            # print(f"Warning: Include folder '{include_path}' does not exist")
            continue
            
        if not include_path.is_dir():
            # print(f"Warning: Include path '{include_path}' is not a directory")
            continue
        
        # Walk through the directory tree
        for root, dirs, files in os.walk(include_path):
            root_path_obj = Path(root)
            
            # Skip excluded directories
            if should_exclude(root_path_obj):
                continue
            
            # Check files in current directory
            for file in files:
                file_path = root_path_obj / file
                
                # Check if it's a C++ file
                if file_path.suffix.lower() in cpp_extensions:
                    found_files.append(str(file_path.resolve()))
    
    return sorted(found_files)


def main():
    """Main function to handle command line arguments and execute the search."""
    parser = argparse.ArgumentParser(
        description="Find C++ source files with include/exclude folder options"
    )
    parser.add_argument(
        "--root", 
        default=".", 
        help="Root directory to start searching from (default: current directory)"
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
        "--output", 
        help="Output file to save results (optional)"
    )
    
    args = parser.parse_args()
    
    # Find C++ files
    cpp_files = find_cpp_files(
        root_dir=args.root,
        include_folders=args.include,
        exclude_folders=args.exclude
    )
    
    # Print summary
    # print(f"Found {len(cpp_files)} C++ source files")
    
    # Print files if not too many
    if len(cpp_files) <= 20:
        # print("\nFiles found:")
        # for file_path in cpp_files:
        #     print(f"  {file_path}")
        pass
    else:
        # print(f"\nFirst 20 files (showing {min(20, len(cpp_files))} of {len(cpp_files)}):")
        # for file_path in cpp_files[:20]:
        #     print(f"  {file_path}")
        # print("  ... (use --output to save full list)")
        pass
    
    # Save to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            for file_path in cpp_files:
                f.write(f"{file_path}\n")
        # print(f"\nFull list saved to: {args.output}")
    
    # Return the list for other scripts to consume
    return cpp_files


# Export functions for other scripts to import
__all__ = ['find_cpp_files', 'main', 'get_cpp_files_command']

def get_cpp_files_command():
    """Command-line interface function that returns the list of C++ files."""
    return main()

if __name__ == "__main__":
    # When run as script, execute main and store result
    result_files = main()
