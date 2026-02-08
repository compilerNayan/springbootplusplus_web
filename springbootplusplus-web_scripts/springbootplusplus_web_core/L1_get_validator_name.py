#!/usr/bin/env python3
"""
Script to determine the validator name for a C++ file based on VALIDATE macro usage.
Combines check_validate_macro.py and find_class_names.py functionality.
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

# Import functions from our other scripts
try:
    from check_validate_macro import find_validate_macros, check_validate_macro_exists
    from find_class_names import find_class_names
except ImportError:
    # print("Error: Could not import required modules. Make sure check_validate_macro.py and find_class_names.py are in the same directory.")
    sys.exit(1)


def get_validator_name(file_path: str) -> Optional[str]:
    """
    Determine the validator name for a C++ file based on VALIDATE macro usage.
    
    Args:
        file_path: Path to the C++ file (.cpp, .h, or .hpp)
        
    Returns:
        Validator name if found, None otherwise
    """
    # Step 1: Check if file has VALIDATE macro
    if not check_validate_macro_exists(file_path):
        return None
    
    # Step 2: Get detailed VALIDATE macro information
    validate_macros = find_validate_macros(file_path)
    if not validate_macros:
        return None
    
    # Step 3: Get class names from the file
    class_names = find_class_names(file_path)
    if not class_names:
        # print(f"Warning: No classes found in {file_path}")
        return None
    
    # For now, take the first class found (assuming one class per file)
    # This could be enhanced to handle multiple classes if needed
    class_name = class_names[0]
    
    # Step 4: Determine validator name based on VALIDATE macro usage
    for macro_info in validate_macros:
        macro_text = macro_info['macro']
        
        if macro_text == 'VALIDATE':
            # VALIDATE without parameter: validator name is ClassName + "Validator"
            validator_name = f"{class_name}Validator"
            # print(f"Found VALIDATE macro without parameter")
            # print(f"Class name: {class_name}")
            # print(f"Validator name: {validator_name}")
            return validator_name
            
        elif macro_text.startswith('VALIDATE_WITH('):
            # VALIDATE_WITH with parameter: validator name is the parameter
            # Extract parameter from VALIDATE_WITH(ParamName)
            param_start = macro_text.find('(') + 1
            param_end = macro_text.find(')')
            if param_start > 0 and param_end > param_start:
                validator_name = macro_text[param_start:param_end].strip()
                # print(f"Found VALIDATE_WITH macro with parameter: {macro_text}")
                # print(f"Class name: {class_name}")
                # print(f"Validator name: {validator_name}")
                return validator_name
    
    # If we get here, something went wrong
    # print(f"Error: Could not determine validator name from VALIDATE macro")
    return None


def get_validator_info(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Get comprehensive validator information for a C++ file.
    
    Args:
        file_path: Path to the C++ file
        
    Returns:
        Dictionary with validator information or None if not found
    """
    # Step 1: Check if file has VALIDATE macro
    if not check_validate_macro_exists(file_path):
        return None
    
    # Step 2: Get detailed VALIDATE macro information
    validate_macros = find_validate_macros(file_path)
    if not validate_macros:
        return None
    
    # Step 3: Get class names from the file
    class_names = find_class_names(file_path)
    if not class_names:
        return None
    
    # Step 4: Build comprehensive info
    validator_info = {
        'file_path': file_path,
        'has_validate': True,
        'validate_macros': validate_macros,
        'class_names': class_names,
        'primary_class': class_names[0],
        'validator_name': None,
        'validate_type': None
    }
    
    # Determine validator name and type
    for macro_info in validate_macros:
        macro_text = macro_info['macro']
        
        if macro_text == 'VALIDATE':
            validator_info['validate_type'] = 'standalone'
            validator_info['validator_name'] = f"{class_names[0]}Validator"
            break
            
        elif macro_text.startswith('VALIDATE_WITH('):
            validator_info['validate_type'] = 'parameterized'
            param_start = macro_text.find('(') + 1
            param_end = macro_text.find(')')
            if param_start > 0 and param_end > param_start:
                validator_info['validator_name'] = macro_text[param_start:param_end].strip()
            break
    
    return validator_info


def process_multiple_files(file_paths: list) -> Dict[str, Optional[Dict[str, Any]]]:
    """
    Process multiple files to get validator information.
    
    Args:
        file_paths: List of file paths to process
        
    Returns:
        Dictionary mapping file paths to validator information
    """
    results = {}
    
    for file_path in file_paths:
        # print(f"\n{'='*60}")
        # print(f"Processing: {file_path}")
        # print(f"{'='*60}")
        
        validator_info = get_validator_info(file_path)
        results[file_path] = validator_info
        
        if validator_info:
            # print(f"✓ VALIDATE macro found")
            # print(f"  Class: {validator_info['primary_class']}")
            # print(f"  Validator: {validator_info['validator_name']}")
            # print(f"  Type: {validator_info['validate_type']}")
            pass
        else:
            # print("✗ No VALIDATE macro found")
            pass
    
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
    """Main function to handle command line arguments and execute the validation."""
    parser = argparse.ArgumentParser(
        description="Determine validator name for C++ files based on VALIDATE macro usage"
    )
    parser.add_argument(
        "files", 
        nargs="+", 
        help="C++ source files to analyze (.cpp, .h, .hpp, etc.)"
    )
    parser.add_argument(
        "--simple", 
        action="store_true",
        help="Simple output: just show validator name"
    )
    parser.add_argument(
        "--detailed", 
        action="store_true",
        help="Show detailed validator information"
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
        # Single file - show validator name
        file_path = valid_files[0]
        validator_name = get_validator_name(file_path)
        
        if validator_name:
            if args.simple:
                # print(validator_name)
                pass
            else:
                # print(f"\nValidator name: {validator_name}")
                pass
        else:
            # print("No VALIDATE macro found in file")
            pass
            
        results = {file_path: get_validator_info(file_path)}
    else:
        # Multiple files - process all
        results = process_multiple_files(valid_files)
    
    # Show summary if requested
    if args.summary and len(valid_files) > 1:
        # print(f"\n{'='*60}")
        # print("SUMMARY")
        # print(f"{'='*60}")
        # total_files = len(valid_files)
        # files_with_validate = len([r for r in results.values() if r is not None])
        # files_without_validate = total_files - files_with_validate
        # 
        # print(f"Files analyzed: {total_files}")
        # print(f"Files with VALIDATE: {files_with_validate}")
        # print(f"Files without VALIDATE: {files_without_validate}")
        # 
        # if args.detailed:
        #     print(f"\nDetailed results:")
        #     for file_path, info in results.items():
        #         if info:
        #             print(f"  {file_path}: {info['validator_name']} ({info['validate_type']})")
        #         else:
        #             print(f"  {file_path}: No VALIDATE")
        pass
    
    # Save to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            for file_path, info in results.items():
                f.write(f"{file_path}:\n")
                if info:
                    f.write(f"  Class: {info['primary_class']}\n")
                    f.write(f"  Validator: {info['validator_name']}\n")
                    f.write(f"  Type: {info['validate_type']}\n")
                else:
                    f.write(f"  No VALIDATE macro found\n")
                f.write("\n")
        # print(f"\nResults saved to: {args.output}")
    
    return results


# Export functions for other scripts to import
__all__ = [
    'get_validator_name',
    'get_validator_info',
    'process_multiple_files',
    'main'
]


if __name__ == "__main__":
    # When run as script, execute main and store result
    result = main()
