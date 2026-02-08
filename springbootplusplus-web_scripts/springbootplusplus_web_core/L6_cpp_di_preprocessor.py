#!/usr/bin/env python3
"""
L6 CPP DI Preprocessor Script

This script orchestrates the complete dependency injection preprocessing workflow by:
1. Finding all C++ source files in the specified include/exclude paths
2. Running L5_process_di.py on each source file to process COMPONENT and AUTOWIRED macros

This is the highest-level script that automates the entire DI preprocessing pipeline.
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path
from typing import List, Dict, Optional

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def find_cpp_files(include_paths: List[str], exclude_paths: List[str]) -> List[str]:
    """
    Find all C++ source files in the specified include/exclude paths.
    
    Args:
        include_paths: List of include paths to search in
        exclude_paths: List of exclude paths to avoid
        
    Returns:
        List of C++ file paths
    """
    cpp_files = []
    
    # If no include paths specified, search current directory
    if not include_paths:
        include_paths = ["."]
    
    for include_path in include_paths:
        if not Path(include_path).exists():
            # print(f"⚠️  Warning: Include path '{include_path}' does not exist")
            continue
            
        # Find all C++ source files (.h, .hpp, .cpp, .cc, .cxx)
        for file_path in Path(include_path).rglob("*.h"):
            if not any(str(file_path).startswith(exclude) for exclude in exclude_paths):
                cpp_files.append(str(file_path))
        
        for file_path in Path(include_path).rglob("*.hpp"):
            if not any(str(file_path).startswith(exclude) for exclude in exclude_paths):
                cpp_files.append(str(file_path))
        
        for file_path in Path(include_path).rglob("*.cpp"):
            if not any(str(file_path).startswith(exclude) for exclude in exclude_paths):
                cpp_files.append(str(file_path))
        
        for file_path in Path(include_path).rglob("*.cc"):
            if not any(str(file_path).startswith(exclude) for exclude in exclude_paths):
                cpp_files.append(str(file_path))
        
        for file_path in Path(include_path).rglob("*.cxx"):
            if not any(str(file_path).startswith(exclude) for exclude in exclude_paths):
                cpp_files.append(str(file_path))
    
    return sorted(cpp_files)


def run_l5_process_di(file_path: str, include_paths: List[str], exclude_paths: List[str], dry_run: bool = False) -> Dict[str, any]:
    """
    Run L5_process_di.py on a single file.
    
    Args:
        file_path: Path to the C++ file to process
        include_paths: List of include paths
        exclude_paths: List of exclude paths
        dry_run: Whether to run in dry-run mode
        
    Returns:
        Dictionary with results
    """
    try:
        # Build the command - use script in same directory
        script_path = os.path.join(SCRIPT_DIR, "L5_process_di.py")
        cmd = ["python", script_path, file_path]
        
        # Add include paths if provided
        if include_paths:
            cmd.extend(["--include"] + include_paths)
        
        # Add exclude paths if provided
        if exclude_paths:
            cmd.extend(["--exclude"] + exclude_paths)
        
        # Add dry-run flag if specified
        if dry_run:
            cmd.append("--dry-run")
        
        # Run the command
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=".")
        
        # Parse results
        results = {
            'success': result.returncode == 0,
            'return_code': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'errors': []
        }
        
        # Check for specific error patterns in output
        if result.stdout:
            if "Overall Result: ❌ FAILED" in result.stdout:
                results['success'] = False
                results['errors'].append("L5 script reported failure")
            elif "Overall Result: ✅ SUCCESS" in result.stdout:
                results['success'] = True
        
        if result.stderr:
            results['errors'].append(f"Stderr: {result.stderr}")
        
        # Display results in one line - just show the emoji
        if results['success']:
            # print("✅")
            pass
        else:
            # print("❌")
            if results['errors']:
                # for error in results['errors']:
                #     print(f"      Error: {error}")
                pass
        
        return results
        
    except Exception as e:
        error_result = {
            'success': False,
            'return_code': -1,
            'stdout': '',
            'stderr': str(e),
            'errors': [f"Exception: {e}"]
        }
        # print(f"   ❌ Exception: {e}")
        return error_result


def process_all_files(cpp_files: List[str], include_paths: List[str], exclude_paths: List[str], dry_run: bool = False) -> Dict[str, any]:
    """
    Process all C++ files with L5_process_di.py.
    
    Args:
        cpp_files: List of C++ file paths to process
        include_paths: List of include paths
        exclude_paths: List of exclude paths
        dry_run: Whether to run in dry-run mode
        
    Returns:
        Dictionary with overall results
    """
    # print(f"\n🚀 Starting DI preprocessing for {len(cpp_files)} C++ files")
    # print("=" * 80)
    
    results = {
        'total_files': len(cpp_files),
        'successful_files': 0,
        'failed_files': 0,
        'file_results': {},
        'errors': []
    }
    
    for i, file_path in enumerate(cpp_files, 1):
        # Process the file
        file_result = run_l5_process_di(file_path, include_paths, exclude_paths, dry_run)
        results['file_results'][file_path] = file_result
        
        # Update counters
        if file_result['success']:
            results['successful_files'] += 1
        else:
            results['failed_files'] += 1
            if file_result['errors']:
                results['errors'].extend([f"{file_path}: {error}" for error in file_result['errors']])
    
    return results


def display_summary(results: Dict[str, any], dry_run: bool = False):
    """
    Display a summary of the processing results.
    
    Args:
        results: Results dictionary from process_all_files
        dry_run: Whether this was a dry run
    """
    # print("\n" + "=" * 80)
    # print("📊 PROCESSING SUMMARY")
    # print("=" * 80)
    
    # print(f"Total files processed: {results['total_files']}")
    # print(f"Successful: {results['successful_files']} ✅")
    
    # Show failed count with appropriate emoji
    if results['failed_files'] == 0:
        # print(f"Failed: {results['failed_files']} ✅")
        pass
    else:
        # print(f"Failed: {results['failed_files']} ❌")
        pass
    
    success_rate = (results['successful_files'] / results['total_files'] * 100) if results['total_files'] > 0 else 0
    # print(f"Success rate: {success_rate:.1f}%")
    
    if results['errors']:
        # print(f"\n⚠️  Errors encountered:")
        # for error in results['errors'][:10]:  # Show first 10 errors
        #     print(f"  - {error}")
        # if len(results['errors']) > 10:
        #     print(f"  ... and {len(results['errors']) - 10} more errors")
        pass
    
    if dry_run:
        # print(f"\n🔍 This was a dry run - no changes were made")
        pass
    else:
        # print(f"\n✅ All changes have been applied")
        pass
    
    # Overall result
    overall_success = results['failed_files'] == 0
    # print(f"\n🎯 Overall Result: {'✅ SUCCESS' if overall_success else '❌ FAILED'}")


def main():
    parser = argparse.ArgumentParser(
        description="L6 CPP DI Preprocessor - Orchestrate complete DI preprocessing workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python springbootplusplus_web_core/L6_cpp_di_preprocessor.py --include src platform                    # Process all files in src and platform
  python springbootplusplus_web_core/L6_cpp_di_preprocessor.py --include src --exclude platform/arduino  # Process with exclude
  python springbootplusplus_web_core/L6_cpp_di_preprocessor.py --include src platform --dry-run          # Dry run to see what would happen
  python springbootplusplus_web_core/L6_cpp_di_preprocessor.py --dry-run                                 # Dry run on all files in current directory
        """
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
        help="Show what would be changed without making changes"
    )
    
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Show detailed summary of results"
    )
    
    args = parser.parse_args()
    
    # Show configuration
    # print("🔧 L6 CPP DI Preprocessor Configuration")
    # print("=" * 50)
    # print(f"Include paths: {args.include if args.include else ['current directory']}")
    # print(f"Exclude paths: {args.exclude if args.exclude else ['none']}")
    # print(f"Dry run: {'Yes' if args.dry_run else 'No'}")
    # print()
    
    # Find all C++ files
    cpp_files = find_cpp_files(args.include, args.exclude)
    
    if not cpp_files:
        sys.exit(0)
    
    # Process all files
    results = process_all_files(cpp_files, args.include, args.exclude, args.dry_run)
    
    # Display summary
    display_summary(results, args.dry_run)
    
    # Show detailed results if requested
    if args.summary:
        # print(f"\n📋 DETAILED RESULTS")
        # print("=" * 50)
        # for file_path, file_result in results['file_results'].items():
        #     status = "✅ Success" if file_result['success'] else "❌ Failed"
        #     print(f"{file_path}: {status}")
        pass
    
    # Exit with appropriate code
    if results['failed_files'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
