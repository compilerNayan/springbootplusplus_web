#!/usr/bin/env python3
"""
Script to determine the final scope of a C++ file based on @Scope annotation and validator presence.
Combines @Scope annotation detection and validator logic to determine final scope.
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

# Import functions from our other scripts
try:
    from check_scope_macro import find_scope_macros, check_scope_macro_exists
    from L1_get_validator_name import get_validator_name, get_validator_info
except ImportError:
    # print("Error: Could not import required modules. Make sure check_scope_macro.py and L1_get_validator_name.py are in the same directory.")
    sys.exit(1)


def get_file_scope(file_path: str) -> str:
    """
    Determine the final scope of a C++ file based on SCOPE macro and validator presence.
    
    Args:
        file_path: Path to the C++ file (.cpp, .h, or .hpp)
        
    Returns:
        Final scope string: SINGLETON, PROTOTYPE, SINGLETON_VALIDATOR, or PROTOTYPE_VALIDATOR
    """
    # Step 1: Check for @Scope annotation
    scope_macros = find_scope_macros(file_path)
    
    # Determine base scope
    base_scope = "SINGLETON"  # Default scope
    
    if scope_macros:
        # Use the first @Scope annotation found (assuming one per file)
        scope_macro = scope_macros[0]
        base_scope = scope_macro['scope_value']
        # print(f"Found @Scope annotation: {scope_macro['macro']}")
        # print(f"Base scope: {base_scope}")
    else:
        # print(f"No @Scope annotation found, using default: {base_scope}")
        pass
    
    # Step 2: Check for validator
    validator_name = get_validator_name(file_path)
    
    if validator_name:
        # print(f"Found validator: {validator_name}")
        # If validator exists, scope becomes SCOPE_VALIDATOR
        final_scope = f"{base_scope}_VALIDATOR"
        # print(f"Final scope: {final_scope}")
        return final_scope
    else:
        # print("No validator found")
        # If no validator, scope is just the base scope
        final_scope = base_scope
        # print(f"Final scope: {final_scope}")
        return final_scope


def get_file_scope_info(file_path: str) -> Dict[str, Any]:
    """
    Get comprehensive scope information for a C++ file.
    
    Args:
        file_path: Path to the C++ file
        
    Returns:
        Dictionary with complete scope information
    """
    # Step 1: Get @Scope annotation information
    scope_macros = find_scope_macros(file_path)
    
    # Step 2: Get validator information
    validator_info = get_validator_info(file_path)
    
    # Step 3: Determine base scope
    base_scope = "SINGLETON"  # Default scope
    scope_source = "default"
    
    if scope_macros:
        scope_macro = scope_macros[0]
        base_scope = scope_macro['scope_value']
        scope_source = "annotation"
    
    # Step 4: Determine final scope
    has_validator = validator_info is not None
    validator_name = validator_info['validator_name'] if validator_info else None
    
    if has_validator:
        final_scope = f"{base_scope}_VALIDATOR"
    else:
        final_scope = base_scope
    
    # Step 5: Build comprehensive info
    scope_info = {
        'file_path': file_path,
        'base_scope': base_scope,
        'scope_source': scope_source,  # "default" or "macro"
        'has_validator': has_validator,
        'validator_name': validator_name,
        'final_scope': final_scope,
        'scope_macros': scope_macros,
        'validator_info': validator_info
    }
    
    return scope_info


def process_multiple_files(file_paths: list) -> Dict[str, Dict[str, Any]]:
    """
    Process multiple files to get scope information.
    
    Args:
        file_paths: List of file paths to process
        
    Returns:
        Dictionary mapping file paths to scope information
    """
    results = {}
    
    for file_path in file_paths:
        # print(f"\n{'='*60}")
        # print(f"Processing: {file_path}")
        # print(f"{'='*60}")
        
        scope_info = get_file_scope_info(file_path)
        results[file_path] = scope_info
        
        # Display results
        # print(f"Base scope: {scope_info['base_scope']} ({scope_info['scope_source']})")
        if scope_info['has_validator']:
            # print(f"Validator: {scope_info['validator_name']}")
            pass
        else:
            # print("Validator: None")
            pass
        # print(f"Final scope: {scope_info['final_scope']}")
    
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
    """Main function to handle command line arguments and execute the scope detection."""
    parser = argparse.ArgumentParser(
        description="Determine the final scope of C++ files based on @Scope annotation and validator presence"
    )
    parser.add_argument(
        "files", 
        nargs="+", 
        help="C++ source files to analyze (.cpp, .h, .hpp, etc.)"
    )
    parser.add_argument(
        "--simple", 
        action="store_true",
        help="Simple output: just show final scope"
    )
    parser.add_argument(
        "--detailed", 
        action="store_true",
        help="Show detailed scope information"
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
        # Single file - show scope
        file_path = valid_files[0]
        final_scope = get_file_scope(file_path)
        
        if args.simple:
            # print(final_scope)
            pass
        else:
            # print(f"\nFinal scope: {final_scope}")
            pass
            
        results = {file_path: get_file_scope_info(file_path)}
    else:
        # Multiple files - process all
        results = process_multiple_files(valid_files)
    
    # Show summary if requested
    if args.summary and len(valid_files) > 1:
        # print(f"\n{'='*60}")
        # print("SUMMARY")
        # print(f"{'='*60}")
        # 
        # # Count different scope types
        # scope_counts = {}
        # validator_counts = {'with_validator': 0, 'without_validator': 0}
        # 
        # for file_path, info in results.items():
        #     final_scope = info['final_scope']
        #     scope_counts[final_scope] = scope_counts.get(final_scope, 0) + 1
        #     
        #     if info['has_validator']:
        #         validator_counts['with_validator'] += 1
        #     else:
        #         validator_counts['without_validator'] += 1
        # 
        # print(f"Files analyzed: {len(valid_files)}")
        # print(f"\nScope distribution:")
        # for scope, count in sorted(scope_counts.items()):
        #     print(f"  {scope}: {count}")
        # 
        # print(f"\nValidator distribution:")
        # print(f"  With validator: {validator_counts['with_validator']}")
        # print(f"  Without validator: {validator_counts['without_validator']}")
        # 
        # if args.detailed:
        #     print(f"\nDetailed results:")
        #     for file_path, info in results.items():
        #         print(f"  {file_path}: {info['final_scope']}")
        #         if info['has_validator']:
        #             print(f"    → {info['base_scope']} + {info['validator_name']}")
        #         else:
        #             print(f"    → {info['base_scope']} (default)")
        pass
    
    # Save to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            for file_path, info in results.items():
                f.write(f"{file_path}:\n")
                f.write(f"  Base scope: {info['base_scope']} ({info['scope_source']})\n")
                f.write(f"  Has validator: {info['has_validator']}\n")
                if info['has_validator']:
                    f.write(f"  Validator: {info['validator_name']}\n")
                f.write(f"  Final scope: {info['final_scope']}\n")
                f.write("\n")
        # print(f"\nResults saved to: {args.output}")
    
    return results


# Export functions for other scripts to import
__all__ = [
    'get_file_scope',
    'get_file_scope_info',
    'process_multiple_files',
    'main'
]


if __name__ == "__main__":
    # When run as script, execute main and store result
    result = main()
