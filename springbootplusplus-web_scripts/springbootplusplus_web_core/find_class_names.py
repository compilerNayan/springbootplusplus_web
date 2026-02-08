#!/usr/bin/env python3
"""
Script to find class names in C++ source files.
Parses class declarations and returns class names for other scripts to consume.
"""

import re
import argparse
from pathlib import Path
from typing import List, Optional, Tuple


def find_class_names(file_path: str) -> List[str]:
    """
    Find all class names in a C++ source file.
    
    Args:
        file_path: Path to the C++ file (.cpp, .h, or .hpp)
        
    Returns:
        List of class names found in the file
    """
    class_names = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
    except FileNotFoundError:
        # print(f"Error: File '{file_path}' not found")
        return []
    except Exception as e:
        # print(f"Error reading file '{file_path}': {e}")
        return []
    
    # Enhanced pattern to match class declarations including final, template, etc.
    # Matches various class declaration patterns:
    # - class ClassName
    # - class ClassName : public BaseClass
    # - class ClassName final : public BaseClass
    # - template<typename T> class ClassName
    # - template<typename T> class ClassName final : public BaseClass
    # - class ClassName final
    # - class ClassName : public Base, public AnotherBase
    class_pattern = r'(?:template\s*<[^>]*>\s*)?class\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:final\s+)?(?:[:<][^;{]*)?\s*{'
    
    # Find all matches
    matches = re.finditer(class_pattern, content, re.MULTILINE | re.DOTALL)
    
    for match in matches:
        class_name = match.group(1)
        if class_name not in class_names:
            class_names.append(class_name)
    
    return class_names


def find_class_names_in_files(file_paths: List[str]) -> dict:
    """
    Find class names in multiple C++ files.
    
    Args:
        file_paths: List of file paths to search
        
    Returns:
        Dictionary mapping file paths to lists of class names
    """
    results = {}
    
    for file_path in file_paths:
        class_names = find_class_names(file_path)
        if class_names:
            results[file_path] = class_names
    
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
        description="Find class names in C++ source files"
    )
    parser.add_argument(
        "files", 
        nargs="+", 
        help="C++ source files to analyze (.cpp, .h, .hpp, etc.)"
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
        return []
    
    # Find class names in all files
    results = find_class_names_in_files(valid_files)
    
    # Display results
    total_classes = 0
    for file_path, class_names in results.items():
        # print(f"\nFile: {file_path}")
        if class_names:
            # print(f"  Classes found: {', '.join(class_names)}")
            total_classes += len(class_names)
        else:
            # print("  No classes found")
            pass
    
    # Show summary if requested
    if args.summary:
        # print(f"\n=== Summary ===")
        # print(f"Files analyzed: {len(valid_files)}")
        # print(f"Files with classes: {len(results)}")
        # print(f"Total classes found: {total_classes}")
        pass
    
    # Save to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            for file_path, class_names in results.items():
                f.write(f"{file_path}:\n")
                for class_name in class_names:
                    f.write(f"  {class_name}\n")
                f.write("\n")
        # print(f"\nResults saved to: {args.output}")
    
    # Return all class names found for other scripts to consume
    all_class_names = []
    for class_names in results.values():
        all_class_names.extend(class_names)
    
    return all_class_names


def get_class_names_from_file(file_path: str) -> List[str]:
    """
    Convenience function to get class names from a single file.
    
    Args:
        file_path: Path to the C++ file
        
    Returns:
        List of class names found in the file
    """
    return find_class_names(file_path)


def get_class_names_from_files(file_paths: List[str]) -> dict:
    """
    Convenience function to get class names from multiple files.
    
    Args:
        file_paths: List of file paths to search
        
    Returns:
        Dictionary mapping file paths to lists of class names
    """
    return find_class_names_in_files(file_paths)


# Export functions for other scripts to import
__all__ = [
    'find_class_names', 
    'find_class_names_in_files', 
    'main', 
    'get_class_names_from_file',
    'get_class_names_from_files'
]


if __name__ == "__main__":
    # When run as script, execute main and store result
    result_classes = main()
