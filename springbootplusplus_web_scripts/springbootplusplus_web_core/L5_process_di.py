#!/usr/bin/env python3
"""
L5 Process DI (Dependency Injection) Script

This script orchestrates the processing of C++ files for dependency injection by:
1. Running L4_process_component.py to process COMPONENT macros
2. Running L4_process_autowired.py to process AUTOWIRED macros

Both scripts are called with the same include and exclude parameters.
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))





def run_script(script_name, files, include_paths, exclude_paths, dry_run=False):
    """
    Run a Python script with the specified files and include/exclude parameters.
    
    Args:
        script_name (str): Name of the script to run
        files (list): List of specific files to process
        include_paths (list): List of include paths
        exclude_paths (list): List of exclude paths
        dry_run (bool): Whether to run in dry-run mode
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if not files:
            # print(f"⚠️  No files specified for {script_name}")
            return False
        
        # print(f"📁 Processing {len(files)} file(s) with {script_name}")
        
        # Build the command based on script requirements
        if script_name == "L4_process_component.py":
            # L4_process_component.py expects: files [--include paths] [--exclude paths] [--dry-run]
            script_path = os.path.join(SCRIPT_DIR, script_name)
            cmd = ["python", script_path]
            
            # Add the specific files to process FIRST (positional arguments)
            cmd.extend(files)
            
            # Add include paths if provided
            if include_paths:
                cmd.extend(["--include"] + include_paths)
            
            # Add exclude paths if provided
            if exclude_paths:
                cmd.extend(["--exclude"] + exclude_paths)
            
            # Add dry-run flag if specified
            if dry_run:
                cmd.append("--dry-run")
            
        elif script_name == "L4_process_autowired.py":
            # L4_process_autowired.py expects: files [--dry-run]
            script_path = os.path.join(SCRIPT_DIR, script_name)
            cmd = ["python", script_path]
            
            # Add the specific files to process FIRST (positional arguments)
            cmd.extend(files)
            
            # Add dry-run flag if specified
            if dry_run:
                cmd.append("--dry-run")
            
        else:
            # print(f"❌ Unknown script: {script_name}")
            return False
        
        # print(f"Running: {' '.join(cmd)}")
        
        # Run the script
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=".")
        
        # Print output
        if result.stdout:
            # print(result.stdout)
            pass
        if result.stderr:
            # print(f"Errors from {script_name}:", result.stderr, file=sys.stderr)
            pass
        
        if result.returncode == 0:
            # print(f"✅ {script_name} completed successfully")
            return True
        else:
            # print(f"❌ {script_name} failed with return code {result.returncode}")
            return False
            
    except Exception as e:
        # print(f"❌ Error running {script_name}: {e}")
        return False


def process_di(files, include_paths, exclude_paths, dry_run=False):
    """
    Process dependency injection by running both component and autowired scripts.
    
    Args:
        files (list): List of specific files to process
        include_paths (list): List of include paths
        exclude_paths (list): List of exclude paths
        dry_run (bool): Whether to run in dry-run mode
        
    Returns:
        dict: Results summary
    """
    # print("🚀 Starting Dependency Injection Processing")
    # print("=" * 60)
    # print(f"📁 Target files: {', '.join(files)}")
    # print()
    
    results = {
        'component_success': False,
        'autowired_success': False,
        'errors': []
    }
    
    # Step 1: Process COMPONENT macros
    # print("\n📋 Step 1: Processing COMPONENT macros with L4_process_component.py")
    # print("-" * 60)
    
    component_success = run_script("L4_process_component.py", files, include_paths, exclude_paths, dry_run)
    results['component_success'] = component_success
    
    if not component_success:
        results['errors'].append("L4_process_component.py failed")
    
    # Step 2: Process AUTOWIRED macros
    # print("\n🔧 Step 2: Processing AUTOWIRED macros with L4_process_autowired.py")
    # print("-" * 60)
    
    autowired_success = run_script("L4_process_autowired.py", files, include_paths, exclude_paths, dry_run)
    results['autowired_success'] = autowired_success
    
    if not autowired_success:
        results['errors'].append("L4_process_autowired.py failed")
    
    # Summary
    # print("\n" + "=" * 60)
    # print("📊 PROCESSING SUMMARY")
    # print("=" * 60)
    
    # print(f"COMPONENT Processing: {'✅ Success' if component_success else '❌ Failed'}")
    # print(f"AUTOWIRED Processing: {'✅ Success' if autowired_success else '❌ Failed'}")
    
    if results['errors']:
        # print(f"\n⚠️  Errors encountered:")
        # for error in results['errors']:
        #     print(f"  - {error}")
        pass
    
    overall_success = component_success and autowired_success
    # print(f"\n🎯 Overall Result: {'✅ SUCCESS' if overall_success else '❌ FAILED'}")
    
    if dry_run:
        # print("\n🔍 This was a dry run - no changes were made")
        pass
    else:
        # print("\n✅ All changes have been applied")
        pass
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description="L5 Process DI - Orchestrate COMPONENT and AUTOWIRED processing for specific files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python springbootplusplus_web_core/L5_process_di.py file.h                                    # Process single file
  python springbootplusplus_web_core/L5_process_di.py file1.h file2.h                           # Process multiple files
  python springbootplusplus_web_core/L5_process_di.py file.h --include src platform              # Process with include paths
  python springbootplusplus_web_core/L5_process_di.py file.h --include src --exclude platform/arduino  # Process with include/exclude
  python springbootplusplus_web_core/L5_process_di.py file.h --include src platform --dry-run    # Dry run to see what would happen
  python springbootplusplus_web_core/L5_process_di.py file.h --dry-run                          # Dry run on specific file
        """
    )
    
    parser.add_argument(
        "files",
        nargs="+",
        help="C++ header files to process (required)"
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
    
    args = parser.parse_args()
    
    # Show configuration
    # print("🔧 L5 Process DI Configuration")
    # print("=" * 40)
    # print(f"Target files: {', '.join(args.files)}")
    # print(f"Include paths: {args.include if args.include else ['none']}")
    # print(f"Exclude paths: {args.exclude if args.exclude else ['none']}")
    # print(f"Dry run: {'Yes' if args.dry_run else 'No'}")
    # print()
    
    # Process dependency injection
    results = process_di(args.files, args.include, args.exclude, args.dry_run)
    
    # Exit with appropriate code
    if results['errors']:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
