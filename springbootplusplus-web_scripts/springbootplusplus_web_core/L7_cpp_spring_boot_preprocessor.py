#!/usr/bin/env python3
"""
L7 CPP Spring Boot Preprocessor Script

This script orchestrates the complete Spring Boot preprocessing workflow by:
1. First calling L6_generate_code_for_all_sources.py to generate endpoint mappings
2. Then calling L6_cpp_di_preprocessor.py to process dependency injection

This is the highest-level script that automates the entire preprocessing pipeline.
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path
from typing import Dict, Any

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def run_l6_generate_code(include_paths: list, exclude_paths: list, dispatcher_file: str, dry_run: bool = False) -> Dict[str, Any]:
    """
    Run L6_generate_code_for_all_sources.py.
    
    Args:
        include_paths: List of include paths to search in
        exclude_paths: List of exclude paths to avoid
        dispatcher_file: Path to EventDispatcher.h file
        dry_run: Whether to run in dry-run mode
        
    Returns:
        Dictionary with results
    """
    try:
        # Build the command - use script in same directory
        script_path = os.path.join(SCRIPT_DIR, "L6_generate_code_for_all_sources.py")
        cmd = ["python", script_path]
        
        # Add include paths if provided
        if include_paths:
            cmd.extend(["--include"] + include_paths)
        
        # Add exclude paths if provided
        if exclude_paths:
            cmd.extend(["--exclude"] + exclude_paths)
        
        # Add dispatcher file if provided
        if dispatcher_file:
            cmd.extend(["--dispatcher-file", dispatcher_file])
        
        # Add dry-run flag if specified
        if dry_run:
            cmd.append("--dry-run")
        
        # Run the command
        result = subprocess.run(cmd, capture_output=False, text=True, cwd=".")
        
        # Parse results
        results = {
            'success': result.returncode == 0,
            'return_code': result.returncode,
            'errors': []
        }
        
        if result.returncode != 0:
            results['success'] = False
            results['errors'].append(f"L6_generate_code_for_all_sources.py exited with code {result.returncode}")
        
        return results
        
    except Exception as e:
        error_result = {
            'success': False,
            'return_code': -1,
            'errors': [f"Exception: {e}"]
        }
        # print(f"❌ Exception running L6_generate_code_for_all_sources.py: {e}")
        return error_result


def run_l6_di_preprocessor(include_paths: list, exclude_paths: list, dry_run: bool = False) -> Dict[str, Any]:
    """
    Run L6_cpp_di_preprocessor.py.
    
    Args:
        include_paths: List of include paths to search in
        exclude_paths: List of exclude paths to avoid
        dry_run: Whether to run in dry-run mode
        
    Returns:
        Dictionary with results
    """
    try:
        # Build the command - use script in same directory
        script_path = os.path.join(SCRIPT_DIR, "L6_cpp_di_preprocessor.py")
        cmd = ["python", script_path]
        
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
        result = subprocess.run(cmd, capture_output=False, text=True, cwd=".")
        
        # Parse results
        results = {
            'success': result.returncode == 0,
            'return_code': result.returncode,
            'errors': []
        }
        
        if result.returncode != 0:
            results['success'] = False
            results['errors'].append(f"L6_cpp_di_preprocessor.py exited with code {result.returncode}")
        
        return results
        
    except Exception as e:
        error_result = {
            'success': False,
            'return_code': -1,
            'errors': [f"Exception: {e}"]
        }
        # print(f"❌ Exception running L6_cpp_di_preprocessor.py: {e}")
        return error_result


def display_summary(step1_result: Dict[str, Any], step2_result: Dict[str, Any], dry_run: bool = False):
    """
    Display a summary of the processing results.
    
    Args:
        step1_result: Results from L6_generate_code_for_all_sources.py
        step2_result: Results from L6_cpp_di_preprocessor.py
        dry_run: Whether this was a dry run
    """
    # print("📊 L7 PREPROCESSING SUMMARY")
    # print("=" * 80)
    
    # Step 1 results
    step1_status = "✅ SUCCESS" if step1_result['success'] else "❌ FAILED"
    # print(f"\nStep 1 - Endpoint Mapping Generation: {step1_status}")
    if step1_result['errors']:
        # for error in step1_result['errors']:
        #     print(f"  ⚠️  {error}")
        pass
    
    # Step 2 results
    step2_status = "✅ SUCCESS" if step2_result['success'] else "❌ FAILED"
    # print(f"\nStep 2 - Dependency Injection Processing: {step2_status}")
    if step2_result['errors']:
        # for error in step2_result['errors']:
        #     print(f"  ⚠️  {error}")
        pass
    
    if dry_run:
        # print(f"\n🔍 This was a dry run - no changes were made")
        pass
    else:
        overall_success = step1_result['success'] and step2_result['success']
        if overall_success:
            # print(f"\n✅ All preprocessing steps completed successfully")
            pass
        else:
            # print(f"\n⚠️  Some preprocessing steps failed")
            pass
    
    # Overall result
    overall_success = step1_result['success'] and step2_result['success']
    # print(f"\n🎯 Overall Result: {'✅ SUCCESS' if overall_success else '❌ FAILED'}")


def main():
    parser = argparse.ArgumentParser(
        description="L7 CPP Spring Boot Preprocessor - Orchestrate complete preprocessing workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python springbootplusplus_web_core/L7_cpp_spring_boot_preprocessor.py --include src platform                    # Process all files in src and platform
  python springbootplusplus_web_core/L7_cpp_spring_boot_preprocessor.py --include src --exclude platform/arduino  # Process with exclude
  python springbootplusplus_web_core/L7_cpp_spring_boot_preprocessor.py --include src platform --dry-run          # Dry run to see what would happen
  python springbootplusplus_web_core/L7_cpp_spring_boot_preprocessor.py --dry-run                                 # Dry run on all files in current directory
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
        "--dispatcher-file",
        default="src/01-framework/06-event/04-dispatcher/01-EventDispatcher.h",
        help="Path to EventDispatcher.h file (default: src/01-framework/06-event/04-dispatcher/01-EventDispatcher.h)"
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
    # print("🔧 L7 CPP Spring Boot Preprocessor Configuration")
    # print("=" * 50)
    # print(f"Include paths: {args.include if args.include else ['current directory']}")
    # print(f"Exclude paths: {args.exclude if args.exclude else ['none']}")
    # print(f"Dispatcher file: {args.dispatcher_file}")
    # print(f"Dry run: {'Yes' if args.dry_run else 'No'}")
    # print("\n" + "=" * 80)
    # print("🚀 Starting complete preprocessing workflow...")
    # print("=" * 80 + "\n")
    
    # Step 1: Generate endpoint mappings
    step1_result = run_l6_generate_code(
        include_paths=args.include,
        exclude_paths=args.exclude,
        dispatcher_file=args.dispatcher_file,
        dry_run=args.dry_run
    )
    
    # If step 1 failed and not in dry-run, we might want to continue or stop
    # For now, we'll continue to step 2 even if step 1 had issues
    # (since DI processing might still be useful)
    
    # Step 2: Process dependency injection
    step2_result = run_l6_di_preprocessor(
        include_paths=args.include,
        exclude_paths=args.exclude,
        dry_run=args.dry_run
    )
    
    # Display summary
    # print("\n" + "=" * 80)
    display_summary(step1_result, step2_result, args.dry_run)
    
    # Exit with appropriate code
    overall_success = step1_result['success'] and step2_result['success']
    if overall_success:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()

