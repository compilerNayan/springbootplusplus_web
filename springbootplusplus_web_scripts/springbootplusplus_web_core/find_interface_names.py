#!/usr/bin/env python3
"""
Script to find interface names from class inheritance declarations in C++ files.
Parses class inheritance patterns and returns interface names for other scripts to consume.
"""

import re
import argparse
from pathlib import Path
from typing import List, Dict, Optional, Tuple


def find_interface_names(file_path: str) -> List[str]:
    """
    Find all interface names from class inheritance declarations in a C++ file.
    
    Args:
        file_path: Path to the C++ file (.cpp, .h, or .hpp)
        
    Returns:
        List of interface names found in the file
    """
    interface_names = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found")
        return []
    except Exception as e:
        print(f"Error reading file '{file_path}': {e}")
        return []
    
    # Pattern to match class inheritance declarations
    # Matches various inheritance patterns:
    # - class ClassName : public InterfaceName
    # - class ClassName final : public InterfaceName
    # - class ClassName : protected InterfaceName
    # - class ClassName : private InterfaceName
    # - class ClassName : public InterfaceName<Template>
    # - class ClassName : public InterfaceName, public AnotherInterface
    # - class ClassName : virtual public InterfaceName
    inheritance_pattern = r'class\s+[A-Za-z_][A-Za-z0-9_]*\s*(?:final\s+)?:\s*(?:virtual\s+)?(?:public|protected|private)\s+([A-Za-z_][A-Za-z0-9_]*)(?:<[^>]*>)?(?:\s*,\s*(?:virtual\s+)?(?:public|protected|private)\s+([A-Za-z_][A-Za-z0-9_]*)(?:<[^>]*>)?)*'
    
    # Find all matches
    matches = re.finditer(inheritance_pattern, content, re.MULTILINE | re.DOTALL)
    
    for match in matches:
        # Extract all interface names from the match
        for group in match.groups():
            if group:
                # Clean up the interface name (remove extra whitespace, etc.)
                interface_name = group.strip()
                if interface_name and interface_name not in interface_names:
                    interface_names.append(interface_name)
    
    return interface_names


def find_interface_names_in_files(file_paths: List[str]) -> Dict[str, List[str]]:
    """
    Find interface names from class inheritance declarations in multiple C++ files.
    
    Args:
        file_paths: List of file paths to search
        
    Returns:
        Dictionary mapping file paths to lists of interface names
    """
    results = {}
    
    for file_path in file_paths:
        interface_names = find_interface_names(file_path)
        if interface_names:
            results[file_path] = interface_names
    
    return results


def find_class_inheritance_details(file_path: str) -> List[Dict[str, str]]:
    """
    Find detailed class inheritance information including class names and their interfaces.
    
    Args:
        file_path: Path to the C++ file
        
    Returns:
        List of dictionaries with 'class_name' and 'interfaces' keys
    """
    inheritance_details = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
    except FileNotFoundError:
        # print(f"Error: File '{file_path}' not found")
        return []
    except Exception as e:
        # print(f"Error reading file '{file_path}': {e}")
        return []
    
    # Pattern to capture both class name and interfaces
    detailed_pattern = r'class\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:final\s+)?:\s*(?:virtual\s+)?(?:public|protected|private)\s+([A-Za-z_][A-Za-z0-9_]*)(?:<[^>]*>)?(?:\s*,\s*(?:virtual\s+)?(?:public|protected|private)\s+([A-Za-z_][A-Za-z0-9_]*)(?:<[^>]*>)?)*'
    
    matches = re.finditer(detailed_pattern, content, re.MULTILINE | re.DOTALL)
    
    for match in matches:
        class_name = match.group(1)
        interfaces = []
        
        # Extract all interface names from the match
        for group in match.groups()[1:]:  # Skip the first group (class name)
            if group:
                interface_name = group.strip()
                if interface_name:
                    interfaces.append(interface_name)
        
        if interfaces:
            inheritance_details.append({
                'class_name': class_name,
                'interfaces': interfaces
            })
    
    return inheritance_details


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
        description="Find interface names from class inheritance declarations in C++ files"
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
    parser.add_argument(
        "--detailed", 
        action="store_true",
        help="Show detailed class-interface relationships"
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
    
    # Find interface names in all files
    results = find_interface_names_in_files(valid_files)
    
    # Display results
    total_interfaces = 0
    unique_interfaces = set()
    
    for file_path, interface_names in results.items():
        # print(f"\nFile: {file_path}")
        if interface_names:
            # print(f"  Interfaces found: {', '.join(interface_names)}")
            total_interfaces += len(interface_names)
            unique_interfaces.update(interface_names)
        else:
            # print("  No interfaces found")
            pass
    
    # Show detailed relationships if requested
    if args.detailed:
        # print(f"\n=== Detailed Class-Interface Relationships ===")
        # for file_path in valid_files:
        #     details = find_class_inheritance_details(file_path)
        #     if details:
        #         print(f"\nFile: {file_path}")
        #         for detail in details:
        #             print(f"  Class '{detail['class_name']}' implements: {', '.join(detail['interfaces'])}")
        pass
    
    # Show summary if requested
    if args.summary:
        # print(f"\n=== Summary ===")
        # print(f"Files analyzed: {len(valid_files)}")
        # print(f"Files with interfaces: {len(results)}")
        # print(f"Total interface references: {total_interfaces}")
        # print(f"Unique interfaces: {len(unique_interfaces)}")
        # if unique_interfaces:
        #     print(f"Interface names: {', '.join(sorted(unique_interfaces))}")
        pass
    
    # Save to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            for file_path, interface_names in results.items():
                f.write(f"{file_path}:\n")
                for interface_name in interface_names:
                    f.write(f"  {interface_name}\n")
                f.write("\n")
        # print(f"\nResults saved to: {args.output}")
    
    # Return all interface names found for other scripts to consume
    all_interface_names = []
    for interface_names in results.values():
        all_interface_names.extend(interface_names)
    
    return all_interface_names


def get_interface_names_from_file(file_path: str) -> List[str]:
    """
    Convenience function to get interface names from a single file.
    
    Args:
        file_path: Path to the C++ file
        
    Returns:
        List of interface names found in the file
    """
    return find_interface_names(file_path)


def get_interface_names_from_files(file_paths: List[str]) -> Dict[str, List[str]]:
    """
    Convenience function to get interface names from multiple files.
    
    Args:
        file_paths: List of file paths to search
        
    Returns:
        Dictionary mapping file paths to lists of interface names
    """
    return find_interface_names_in_files(file_paths)


def get_inheritance_details_from_file(file_path: str) -> List[Dict[str, str]]:
    """
    Convenience function to get detailed inheritance information from a single file.
    
    Args:
        file_path: Path to the C++ file
        
    Returns:
        List of dictionaries with class-interface relationships
    """
    return find_class_inheritance_details(file_path)


# Export functions for other scripts to import
__all__ = [
    'find_interface_names', 
    'find_interface_names_in_files',
    'find_class_inheritance_details',
    'main', 
    'get_interface_names_from_file',
    'get_interface_names_from_files',
    'get_inheritance_details_from_file'
]


if __name__ == "__main__":
    # When run as script, execute main and store result
    result_interfaces = main()
