#!/usr/bin/env python3
"""
Script to process component files by running a sequence of scripts when @Component or @Service annotation is found.
Orchestrates multiple L1, L2, and L3 scripts to fully process a component file.
@Service is treated as an alias for @Component.
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import L1_check_component_macro

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def check_component_macro(file_path: str) -> bool:
    """
    Check if a file has the @Component or @Service annotation using L1_check_component_macro script.
    @Service is treated as an alias for @Component.
    
    Args:
        file_path: Path to the C++ file to check
        
    Returns:
        True if @Component or @Service annotation is found, False otherwise
    """
    try:
        # Check if the file has COMPONENT macro
        has_component = L1_check_component_macro.check_component_macro_exists(file_path)
        return has_component
    except Exception as e:
        # print(f"Error checking COMPONENT macro in {file_path}: {e}")
        return False


def run_script_sequence(file_path: str, include_paths: List[str], exclude_paths: List[str], dry_run: bool = False) -> Dict[str, any]:
    """
    Run the sequence of scripts to process a component file.
    
    Args:
        file_path: Path to the C++ file to process
        include_paths: List of include paths to search in
        exclude_paths: List of exclude paths to avoid
        dry_run: If True, only show what would be done without modifying files
        
    Returns:
        Dictionary with results and any errors
    """
    results = {
        'success': False,
        'steps_completed': [],
        'errors': [],
        'info': {}
    }
    
    try:
        # print(f"\nProcessing component file: {file_path}")
        
        # Step 1: L3_add_instance_code
        # print("\n--- Step 1: Adding instance code ---")
        script_path = os.path.join(SCRIPT_DIR, 'L3_add_instance_code.py')
        if dry_run:
            cmd = ['python', script_path, file_path, '--dry-run']
        else:
            cmd = ['python', script_path, file_path]
        
        # print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
        
        if result.returncode == 0:
            results['steps_completed'].append('L3_add_instance_code')
            # print("✓ Instance code step completed successfully")
            if dry_run:
                # print("Output (dry run):")
                # print(result.stdout)
                pass
        else:
            error_msg = f"L3_add_instance_code failed: {result.stderr}"
            results['errors'].append(error_msg)
            # print(f"✗ {error_msg}")
            return results
        
        # Step 2: L3_add_implementation_template
        # print("\n--- Step 2: Adding implementation template ---")
        script_path = os.path.join(SCRIPT_DIR, 'L3_add_implementation_template.py')
        if dry_run:
            cmd = ['python', script_path, file_path, '--dry-run']
        else:
            cmd = ['python', script_path, file_path]
        
        # print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
        
        if result.returncode == 0:
            results['steps_completed'].append('L3_add_implementation_template')
            # print("✓ Implementation template step completed successfully")
            if dry_run:
                # print("Output (dry run):")
                # print(result.stdout)
                pass
        else:
            error_msg = f"L3_add_implementation_template failed: {result.stderr}"
            results['errors'].append(error_msg)
            # print(f"✗ {error_msg}")
            return results
        
        # Step 3: L2_include_validator_header
        # print("\n--- Step 3: Including validator header ---")
        script_path = os.path.join(SCRIPT_DIR, 'L2_include_validator_header.py')
        cmd = ['python', script_path, file_path]
        
        # Add include paths
        if include_paths:
            cmd.extend(['--include'] + include_paths)
        
        # Add exclude paths
        if exclude_paths:
            cmd.extend(['--exclude'] + exclude_paths)
        
        if dry_run:
            cmd.append('--dry-run')
        
        # print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
        
        if result.returncode == 0:
            results['steps_completed'].append('L2_include_validator_header')
            # print("✓ Validator header step completed successfully")
            if dry_run:
                # print("Output (dry run):")
                # print(result.stdout)
                pass
        else:
            error_msg = f"L2_include_validator_header failed: {result.stderr}"
            results['errors'].append(error_msg)
            # print(f"✗ {error_msg}")
            return results
        
        # Step 4: L1_comment_interface_header
        # print("\n--- Step 4: Commenting interface header ---")
        script_path = os.path.join(SCRIPT_DIR, 'L1_comment_interface_header.py')
        if dry_run:
            cmd = ['python', script_path, file_path, '--dry-run']
        else:
            cmd = ['python', script_path, file_path]
        
        # print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
        
        if result.returncode == 0:
            results['steps_completed'].append('L1_comment_interface_header')
            # print("✓ Interface header commenting step completed successfully")
            if dry_run:
                # print("Output (dry run):")
                # print(result.stdout)
                pass
        else:
            error_msg = f"L1_comment_interface_header failed: {result.stderr}"
            results['errors'].append(error_msg)
            # print(f"✗ {error_msg}")
            return results
        
        # Step 5: L2_add_reverse_include
        script_path = os.path.join(SCRIPT_DIR, 'L2_add_reverse_include.py')
        cmd = ['python', script_path, file_path]
        
        # Add include paths (all in one --include argument)
        if include_paths:
            cmd.extend(['--include'] + include_paths)
        
        # Add exclude paths (all in one --exclude argument)
        if exclude_paths:
            cmd.extend(['--exclude'] + exclude_paths)
        
        if dry_run:
            cmd.append('--dry-run')
        
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
        
        if result.returncode == 0:
            results['steps_completed'].append('L2_add_reverse_include')
        else:
            error_msg = f"L2_add_reverse_include failed: {result.stderr}"
            results['errors'].append(error_msg)
            return results
        
        # Step 6: Mark @Component annotation as processed
        # print("\n--- Step 6: Processing @Component annotation ---")
        if dry_run:
            # print("Would process @Component annotation (dry run)")
            results['steps_completed'].append('comment_component_macro')
        else:
            try:
                success = L1_check_component_macro.comment_component_macro(file_path)
                if success:
                    results['steps_completed'].append('comment_component_macro')
                    # print("✓ @Component annotation processed successfully")
                else:
                    error_msg = "Failed to process @Component annotation"
                    results['errors'].append(error_msg)
                    # print(f"✗ {error_msg}")
                    return results
            except Exception as e:
                error_msg = f"Error processing @Component annotation: {e}"
                results['errors'].append(error_msg)
                # print(f"✗ {error_msg}")
                return results
        
        # All steps completed successfully
        results['success'] = True
        # print(f"\n🎉 All steps completed successfully for {file_path}")
        
    except Exception as e:
        error_msg = f"Error in script sequence: {e}"
        results['errors'].append(error_msg)
        # print(f"✗ {error_msg}")
    
    return results


def process_file(file_path: str, include_paths: List[str], exclude_paths: List[str], dry_run: bool = False) -> Dict[str, any]:
    """
    Process a single file to check for @Component annotation and run script sequence if found.
    
    Args:
        file_path: Path to the C++ file to process
        include_paths: List of include paths to search in
        exclude_paths: List of exclude paths to avoid
        dry_run: If True, only show what would be done without modifying files
        
    Returns:
        Dictionary with results and any errors
    """
    results = {
        'success': False,
        'has_component': False,
        'steps_completed': [],
        'errors': [],
        'info': {}
    }
    
    try:
        # print(f"\nProcessing file: {file_path}")
        
        # Step 1: Check if file has @Component annotation
        has_component = check_component_macro(file_path)
        results['has_component'] = has_component
        
        if has_component:
            # print(f"✓ @Component annotation found in {file_path}")
            # print("Running script sequence...")
            
            # Run the script sequence
            sequence_results = run_script_sequence(file_path, include_paths, exclude_paths, dry_run)
            
            # Merge results
            results['success'] = sequence_results['success']
            results['steps_completed'] = sequence_results['steps_completed']
            results['errors'].extend(sequence_results['errors'])
            
        else:
            # print(f"✗ No @Component annotation found in {file_path}")
            # print("Skipping file (no action needed)")
            results['success'] = True  # Successfully determined no action needed
        
    except Exception as e:
        results['errors'].append(f"Error processing file: {e}")
    
    return results


def process_multiple_files(file_paths: List[str], include_paths: List[str], exclude_paths: List[str], dry_run: bool = False) -> Dict[str, Dict[str, any]]:
    """
    Process multiple files to check for @Component annotation and run script sequence if found.
    
    Args:
        file_paths: List of file paths to process
        include_paths: List of include paths to search in
        exclude_paths: List of exclude paths to avoid
        dry_run: If True, only show what would be done without modifying files
        
    Returns:
        Dictionary mapping file paths to results
    """
    all_results = {}
    
    for file_path in file_paths:
        results = process_file(file_path, include_paths, exclude_paths, dry_run)
        all_results[file_path] = results
        
        # Display results for this file
        if results['success']:
            if results['has_component']:
                # print(f"  Status: Component file processed successfully")
                # print(f"  Steps completed: {', '.join(results['steps_completed'])}")
                pass
            else:
                # print(f"  Status: No COMPONENT macro found, skipped")
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
    """Main function to handle command line arguments and execute the component processing."""
    parser = argparse.ArgumentParser(
        description="Process component files by running a sequence of scripts when @Component annotation is found"
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
        # print(f"Files with COMPONENT macro: {len([r for r in results.values() if r['has_component']])}")
        # print(f"Files processed successfully: {len([r for r in results.values() if r['success']])}")
        # print(f"Include paths: {args.include if args.include else ['default']}")
        # print(f"Exclude paths: {args.exclude if args.exclude else ['none']}")
        # 
        # total_errors = sum(len(r['errors']) for r in results.values())
        # print(f"Total errors: {total_errors}")
        # 
        # # Show steps completed for component files
        # component_files = [r for r in results.values() if r['has_component']]
        # if component_files:
        #     print(f"\nComponent files processed:")
        #     for file_path, file_results in results.items():
        #         if file_results['has_component']:
        #             print(f"  {file_path}: {', '.join(file_results['steps_completed'])}")
        pass
    
    return results


# Export functions for other scripts to import
__all__ = [
    'check_component_macro',
    'run_script_sequence',
    'process_file',
    'process_multiple_files',
    'main'
]


if __name__ == "__main__":
    # When run as script, execute main and store result
    result = main()
