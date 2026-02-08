#!/usr/bin/env python3
"""
Script to extract the base URL from @RequestMapping annotation above class declarations.
Finds @RequestMapping annotation above a class and extracts the value from /* @RequestMapping("/xyz") */.
Returns "/xyz" as the base URL string, or "/" if not present.
"""

import re
import argparse
from pathlib import Path
from typing import Optional, Dict, Any


def find_request_mapping_macro(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Find @RequestMapping annotation above class declarations in a C++ file.
    
    Args:
        file_path: Path to the C++ file (.cpp, .h, or .hpp)
        
    Returns:
        Dictionary with 'url', 'line_number', 'class_name' if found, None otherwise
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
    
    # Pattern to match @RequestMapping annotation with value (search for /* @RequestMapping("/xyz") */ or /*@RequestMapping("/xyz")*/)
    # Also check for already processed /*--@RequestMapping("...")--*/ pattern
    request_mapping_annotation_pattern = re.compile(r'/\*\s*@RequestMapping\s*\(\s*["\']([^"\']+)["\']\s*\)\s*\*/')
    request_mapping_processed_pattern = re.compile(r'/\*--\s*@RequestMapping\s*\(\s*["\'][^"\']+["\']\s*\)\s*--\*/')
    
    # Pattern to match legacy RequestMapping macro (for backward compatibility)
    request_mapping_macro_pattern = re.compile(r'RequestMapping\s*\(\s*["\']([^"\']+)["\']')
    
    # Pattern to match class declarations
    class_pattern = r'class\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:.*?[:{]|[:{])'
    
    # First, find all class declarations and their line numbers
    class_lines = []
    for line_num, line in enumerate(lines, 1):
        stripped_line = line.strip()
        
        # Allow annotations (/* @... */) to be present before the class, but skip other comments
        if stripped_line.startswith('/*') and not re.search(r'/\*\s*@\w+', stripped_line):
            continue
        if stripped_line.startswith('//'):
            continue
        
        # Check for class declaration
        class_match = re.search(class_pattern, stripped_line)
        if class_match:
            class_lines.append({
                'line_number': line_num,
                'class_name': class_match.group(1),
                'line': stripped_line
            })
    
    # For each class, look backwards for @RequestMapping annotation
    for class_info in class_lines:
        class_line_num = class_info['line_number']
        
        # Look backwards up to 10 lines before the class
        # Start from class_line_num - 2 (line before the class, since lines is 0-indexed)
        start_idx = class_line_num - 2  # Convert 1-indexed to 0-indexed and go back one more
        end_idx = max(-1, class_line_num - 12)  # Go back up to 10 lines
        
        for i in range(start_idx, end_idx, -1):
            if i < 0:
                break
            line = lines[i].strip()
            
            # Skip already processed annotations
            if request_mapping_processed_pattern.search(line):
                continue
            
            # Skip other comments that aren't @RequestMapping annotations
            # But allow /* @RequestMapping("...") */ annotations to be processed
            if line.startswith('/*') and not request_mapping_annotation_pattern.search(line):
                continue
            # Skip single-line comments
            if line.startswith('//'):
                continue
            
            # Skip empty lines
            if not line:
                continue
            
            # Check if this line contains @RequestMapping annotation
            request_mapping_match = request_mapping_annotation_pattern.search(line)
            if request_mapping_match:
                url_value = request_mapping_match.group(1)
                return {
                    'url': url_value,
                    'line_number': i + 1,  # Convert to 1-indexed
                    'class_name': class_info['class_name']
                }
            
            # Fallback: check for legacy RequestMapping macro (for backward compatibility)
            request_mapping_match = request_mapping_macro_pattern.search(line)
            if request_mapping_match:
                url_value = request_mapping_match.group(1)
                return {
                    'url': url_value,
                    'line_number': i + 1,  # Convert to 1-indexed
                    'class_name': class_info['class_name']
                }
            
            # Stop looking if we hit something that's not an annotation/macro (like a class declaration)
            # Allow common annotations/macros to continue searching backwards
            if not (re.search(r'/\*\s*@(RestController|RequestMapping|GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping|Component|Autowired|Scope)\s*\*/', line) or
                   line.startswith(('RestController', 'RequestMapping', 'GetMapping', 
                                    'PostMapping', 'PutMapping', 'DeleteMapping', 'PatchMapping',
                                    'COMPONENT', 'SCOPE', 'VALIDATE')) or 
                   re.match(r'^[A-Z][A-Za-z0-9_]*\s*(?:\(|$)', line)):
                # Not an annotation/macro, stop looking backwards
                break
    
    return None


def get_base_url(file_path: str) -> str:
    """
    Get the base URL from @RequestMapping annotation above class declarations.
    
    Args:
        file_path: Path to the C++ file
    
    Returns:
        Base URL string (e.g., "/xyz") or "/" if not found
    """
    request_mapping_info = find_request_mapping_macro(file_path)
    
    if request_mapping_info and request_mapping_info['url']:
        return request_mapping_info['url']
    
    return "/"


def get_base_url_info(file_path: str) -> Dict[str, Any]:
    """
    Get comprehensive base URL information from @RequestMapping annotation.
    
    Args:
        file_path: Path to the C++ file
    
    Returns:
        Dictionary with base URL information
    """
    request_mapping_info = find_request_mapping_macro(file_path)
    
    if request_mapping_info:
        return {
            'file_path': file_path,
            'base_url': request_mapping_info['url'],
            'found': True,
            'line_number': request_mapping_info['line_number'],
            'class_name': request_mapping_info['class_name']
        }
    else:
        return {
            'file_path': file_path,
            'base_url': "/",
            'found': False,
            'line_number': None,
            'class_name': None
        }


def process_multiple_files(file_paths: list) -> Dict[str, Dict[str, Any]]:
    """
    Process multiple files to get base URL information.
    
    Args:
        file_paths: List of file paths to process
        
    Returns:
        Dictionary mapping file paths to base URL information
    """
    results = {}
    
    for file_path in file_paths:
        results[file_path] = get_base_url_info(file_path)
    
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
    """Main function to handle command line arguments and execute the base URL extraction."""
    parser = argparse.ArgumentParser(
        description="Extract base URL from @RequestMapping annotation above class declarations"
    )
    parser.add_argument(
        "files", 
        nargs="+", 
        help="C++ source files to analyze (.cpp, .h, .hpp, etc.)"
    )
    parser.add_argument(
        "--simple", 
        action="store_true",
        help="Simple output: just show base URL"
    )
    parser.add_argument(
        "--detailed", 
        action="store_true",
        help="Show detailed base URL information"
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
        # Single file - show base URL
        file_path = valid_files[0]
        base_url = get_base_url(file_path)
        
        if args.simple:
            # print(base_url)
            pass
        else:
            base_url_info = get_base_url_info(file_path)
            # if base_url_info['found']:
            #     print(f"\nBase URL: {base_url_info['base_url']}")
            #     print(f"Found at line {base_url_info['line_number']} above class {base_url_info['class_name']}")
            # else:
            #     print(f"\nBase URL: {base_url_info['base_url']} (default - RequestMapping not found)")
            pass
            
        results = {file_path: get_base_url_info(file_path)}
    else:
        # Multiple files - process all
        results = process_multiple_files(valid_files)
        
        # Display results
        # for file_path, info in results.items():
        #     if args.simple:
        #         print(f"{file_path}: {info['base_url']}")
        #     else:
        #         print(f"\n{'='*60}")
        #         print(f"File: {file_path}")
        #         print(f"{'='*60}")
        #         
        #         if info['found']:
        #             print(f"Base URL: {info['base_url']}")
        #             print(f"Found at line {info['line_number']} above class {info['class_name']}")
        #         else:
        #             print(f"Base URL: {info['base_url']} (default - RequestMapping not found)")
        pass
    
    # Show summary if requested
    if args.summary and len(valid_files) > 1:
        # print(f"\n{'='*60}")
        # print("SUMMARY")
        # print(f"{'='*60}")
        # 
        # files_with_mapping = len([r for r in results.values() if r['found']])
        # files_without_mapping = len([r for r in results.values() if not r['found']])
        # 
        # print(f"Files analyzed: {len(valid_files)}")
        # print(f"Files with RequestMapping: {files_with_mapping}")
        # print(f"Files without RequestMapping: {files_without_mapping}")
        # 
        # if args.detailed:
        #     print(f"\nDetailed results:")
        #     for file_path, info in results.items():
        #         if info['found']:
        #             print(f"  {file_path}: {info['base_url']} (line {info['line_number']}, class {info['class_name']})")
        #         else:
        #             print(f"  {file_path}: {info['base_url']} (default)")
        pass
    
    # Save to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            for file_path, info in results.items():
                f.write(f"{file_path}:\n")
                f.write(f"  Base URL: {info['base_url']}\n")
                if info['found']:
                    f.write(f"  Found: Yes\n")
                    f.write(f"  Line number: {info['line_number']}\n")
                    f.write(f"  Class name: {info['class_name']}\n")
                else:
                    f.write(f"  Found: No (using default '/')\n")
                f.write("\n")
        # print(f"\nResults saved to: {args.output}")
    
    return results


# Export functions for other scripts to import
__all__ = [
    'find_request_mapping_macro',
    'get_base_url',
    'get_base_url_info',
    'process_multiple_files',
    'main'
]


if __name__ == "__main__":
    # When run as script, execute main and store result
    result = main()
