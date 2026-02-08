#!/usr/bin/env python3
"""
Script to find class/interface header files by searching for the specified class name.
Uses find_cpp_files.py to search directories and locates the correct class header.
"""

import os
import sys
import argparse
from pathlib import Path
from typing import List, Optional, Tuple

# Import functions from our other scripts
try:
    from find_cpp_files import find_cpp_files
except ImportError:
    # print("Error: Could not import required modules. Make sure find_cpp_files.py is in the same directory.")
    sys.exit(1)


def find_class_header_file(class_name: str, search_root: str = ".", include_folders: Optional[List[str]] = None, exclude_folders: Optional[List[str]] = None) -> Optional[str]:
    """
    Find the header file for a given class/interface name.
    
    Args:
        class_name: Name of the class/interface to search for
        search_root: Root directory to search for class headers
        include_folders: List of folders to include in search (if None, search all)
        exclude_folders: List of folders to exclude from search
        
    Returns:
        Path to the class header file, or None if not found
    """
    # Step 1: Get all C++ source files in the search directory with include/exclude options
    all_files_raw = find_cpp_files(
        root_dir=search_root,
        include_folders=include_folders,
        exclude_folders=exclude_folders
    )
    
    # Deduplicate all_files by resolving all paths to absolute and using a set
    seen_files = set()
    all_files = []
    for file_path in all_files_raw:
        resolved = str(Path(file_path).resolve())
        if resolved not in seen_files:
            seen_files.add(resolved)
            all_files.append(resolved)
    
    # Step 2: Find files that end with <class-name>.h or <class-name>.hpp (case insensitive)
    potential_headers = []
    class_name_lower = class_name.lower()
    seen_paths = set()  # Track seen paths to avoid duplicates
    
    for file_path in all_files:
        file_name = Path(file_path).name.lower()
        if (file_name.endswith(f"{class_name_lower}.h") or 
            file_name.endswith(f"{class_name_lower}.hpp")):
            # Resolve to absolute path and normalize to avoid duplicates
            # file_path should already be resolved from all_files deduplication, but resolve again to be sure
            resolved_path = str(Path(file_path).resolve())
            if resolved_path not in seen_paths:
                seen_paths.add(resolved_path)
                potential_headers.append(resolved_path)
    
    if not potential_headers:
        return None
    
    # Step 3: Check class names in each potential header
    matching_headers = []
    seen_matching = set()  # Track seen matching headers to avoid duplicates
    
    for header_file in potential_headers:
        try:
            with open(header_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Enhanced pattern to find class declarations including templates, final, etc.
            import re
            # Matches various class declaration patterns:
            # - class ClassName
            # - class ClassName : public Base
            # - class ClassName final : public Base
            # - template<typename T> class ClassName
            # - template<typename T> class ClassName final : public Base
            # - class ClassName final
            # - class ClassName : public Base, public AnotherBase
            class_pattern = r'(?:template\s*<[^>]*>\s*)?class\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:final\s+)?(?:\s*[:{])'
            matches = re.findall(class_pattern, content)
            
            if matches:
                found_class_name = matches[0]  # Take the first class found
                
                # Check if class name matches target class name (case insensitive)
                if found_class_name.lower() == class_name_lower:
                    # Deduplicate matching headers
                    if header_file not in seen_matching:
                        seen_matching.add(header_file)
                        matching_headers.append(header_file)
                
        except Exception as e:
            import traceback
            traceback.print_exc()
    
    # Step 4: Validate results
    if len(matching_headers) == 0:
        return None
    elif len(matching_headers) > 1:
        return None
    else:
        # Exactly one matching header found
        class_header = matching_headers[0]
        return class_header


def find_class_headers_for_names(class_names: List[str], search_root: str = ".", include_folders: Optional[List[str]] = None, exclude_folders: Optional[List[str]] = None) -> dict:
    """
    Find class header files for multiple class names.
    
    Args:
        class_names: List of class/interface names to search for
        search_root: Root directory to search for class headers
        include_folders: List of folders to include in search (if None, search all)
        exclude_folders: List of folders to exclude from search
        
    Returns:
        Dictionary mapping class names to their header files
    """
    results = {}
    
    for class_name in class_names:
        # print(f"\n{'='*60}")
        # print(f"Processing: {class_name}")
        # print(f"{'='*60}")
        
        class_header = find_class_header_file(class_name, search_root, include_folders, exclude_folders)
        if class_header:
            results[class_name] = class_header
        else:
            results[class_name] = None
    
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
    """Main function to handle command line arguments and execute the search."""
    parser = argparse.ArgumentParser(
        description="Find class/interface header files by searching for the specified class names"
    )
    parser.add_argument(
        "class_names", 
        nargs="+", 
        help="Class/interface names to search for"
    )
    parser.add_argument(
        "--search-root", 
        default=".", 
        help="Root directory to search for class headers (default: current directory)"
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
    parser.add_argument(
        "--summary", 
        action="store_true",
        help="Show summary statistics"
    )
    
    args = parser.parse_args()
    
    # Get class names from arguments
    class_names = args.class_names
    
    if not class_names:
        # print("No class names provided")
        return {}
    
    # Find class headers for all class names
    results = find_class_headers_for_names(class_names, args.search_root, args.include, args.exclude)
    
    # Show summary if requested
    if args.summary:
        # print(f"\n{'='*60}")
        # print("SUMMARY")
        # print(f"{'='*60}")
        # print(f"Classes searched: {len(class_names)}")
        # print(f"Class headers found: {len([r for r in results.values() if r is not None])}")
        # print(f"Classes without headers: {len([r for r in results.values() if r is None])}")
        # 
        # print(f"\nResults:")
        # for class_name, class_header in results.items():
        #     if class_header:
        #         print(f"  ✓ {class_name} -> {class_header}")
        #     else:
        #         print(f"  ✗ {class_name} -> No class header found")
        pass
    
    # Save to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            for class_name, class_header in results.items():
                if class_header:
                    f.write(f"{class_name} -> {class_header}\n")
                else:
                    f.write(f"{class_name} -> No class header found\n")
        # print(f"\nResults saved to: {args.output}")
    
    return results


def get_class_header_for_name(class_name: str, search_root: str = ".", include_folders: Optional[List[str]] = None, exclude_folders: Optional[List[str]] = None) -> Optional[str]:
    """
    Convenience function to get class header for a single class name.
    
    Args:
        class_name: Name of the class/interface to search for
        search_root: Root directory to search for class headers
        include_folders: List of folders to include in search (if None, search all)
        exclude_folders: List of folders to exclude from search
        
    Returns:
        Path to the class header file, or None if not found
    """
    return find_class_header_file(class_name, search_root, include_folders, exclude_folders)


def get_class_headers_for_names(class_names: List[str], search_root: str = ".", include_folders: Optional[List[str]] = None, exclude_folders: Optional[List[str]] = None) -> dict:
    """
    Convenience function to get class headers for multiple class names.
    
    Args:
        class_names: List of class/interface names to search for
        search_root: Root directory to search for class headers
        include_folders: List of folders to include in search (if None, search all)
        exclude_folders: List of folders to exclude from search
        
    Returns:
        Dictionary mapping class names to their header files
    """
    return find_class_headers_for_names(class_names, search_root, include_folders, exclude_folders)


# Backward compatibility aliases
def find_interface_header_file(source_file: str, search_root: str = ".", include_folders: Optional[List[str]] = None, exclude_folders: Optional[List[str]] = None) -> Optional[str]:
    """
    Backward compatibility function - extracts class name from source file and finds its header.
    This is kept for compatibility with existing scripts that import this function.
    """
    # For backward compatibility, we'll need to extract class name from the source file
    # This would require importing find_class_names.py
    try:
        from find_class_names import find_class_names
        class_names = find_class_names(source_file)
        if class_names:
            return find_class_header_file(class_names[0], search_root, include_folders, exclude_folders)
    except ImportError:
        # print("Warning: find_class_names.py not available for backward compatibility")
        pass
    return None

# Export functions for other scripts to import
__all__ = [
    'find_class_header_file',
    'find_class_headers_for_names', 
    'get_class_header_for_name',
    'get_class_headers_for_names',
    'find_interface_header_file',  # backward compatibility
    'main'
]


if __name__ == "__main__":
    # When run as script, execute main and store result
    result_headers = main()
