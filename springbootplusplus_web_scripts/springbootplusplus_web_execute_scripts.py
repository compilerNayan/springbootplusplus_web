"""
Script to execute client file processing.
This script imports get_client_files and processes the client project files.
"""

import os
import sys
import subprocess
from pathlib import Path

try:
    from cppcore_core.cppcore_get_client_files import get_client_files
    HAS_CPPCORE = True
except ImportError:
    # print("Warning: Could not import cppcore_core.cppcore_get_client_files")
    # print("         Some features may be unavailable.")
    HAS_CPPCORE = False
    # Create a dummy function to avoid errors
    def get_client_files(*args, **kwargs):
        return []

def execute_scripts(project_dir, library_dir, all_libs=None, library_scripts_dir=None):
    """
    Execute the scripts to process client files.
    
    Args:
        project_dir: Path to the client project root (where platformio.ini is)
        library_dir: Path to the library directory
        all_libs: Dictionary with library directories (from get_all_library_dirs)
        library_scripts_dir: Path to the springbootplusplus_web_scripts directory (optional, will be derived from library_dir if not provided)
    """
    # Process client files if cppcore is available
    if HAS_CPPCORE:
        # print(f"\nproject_dir: {project_dir}")
        # print(f"library_dir: {library_dir}")

        if project_dir:
            client_files = get_client_files(project_dir, file_extensions=['.h', '.cpp'])
            # print(f"\nFound {len(client_files)} files in client project:")
            # print("=" * 60)
            # for file in client_files:
            #     print(file)
            # print("=" * 60)
            pass

        if library_dir:
            library_files = get_client_files(library_dir, skip_exclusions=True)
            # print(f"\nFound {len(library_files)} files in library:")
            # print("=" * 60)
            # for file in library_files:
            #     print(file)
            # print("=" * 60)
            pass
    else:
        # print("Skipping file processing - cppcore_core not available")
        pass
    
    # Call L7_cpp_spring_boot_preprocessor.py with all library directories
    # This should run regardless of HAS_CPPCORE
    if all_libs and all_libs.get('root_dirs'):
        # print("\n" + "=" * 80)
        # print("🚀 Running L7 CPP Spring Boot Preprocessor with all library directories...")
        # print("=" * 80)
        
        # Get the path to L7 script (in springbootplusplus_web_core directory)
        # Determine the scripts directory
        if library_scripts_dir:
            scripts_dir = Path(library_scripts_dir)
        else:
            # Fallback: construct from library_dir
            scripts_dir = Path(library_dir) / "springbootplusplus_web_scripts"
        
        l7_script_path = scripts_dir / "springbootplusplus_web_core" / "L7_cpp_spring_boot_preprocessor.py"
        
        if not l7_script_path.exists():
            # print(f"⚠️  Warning: L7 script not found at {l7_script_path}")
            return
        
        # Build include paths: project src directory + all library directories
        include_paths = []
        
        # Add project src directory if it exists
        if project_dir:
            project_src = Path(project_dir) / "src"
            if project_src.exists():
                include_paths.append(str(project_src))
        
        # Add all library root directories (filter out arduinojson-src)
        for lib_root in all_libs['root_dirs']:
            lib_path = Path(lib_root)
            lib_name = lib_path.name.lower()
            
            # Filter out arduinojson-src and ArduinoJson directories
            if "arduinojson" in lib_name or "arduinojson-src" in lib_name:
                continue
            
            # Add the library root and its src directory if it exists
            include_paths.append(str(lib_path))
            lib_src = lib_path / "src"
            if lib_src.exists():
                include_paths.append(str(lib_src))
        
        # Build the command
        cmd = ["python", str(l7_script_path)]
        
        if include_paths:
            cmd.extend(["--include"] + include_paths)
        
        # Add dispatcher file - look in the library directory (springbootplusplus_web) instead of client project
        dispatcher_file = Path(library_dir) / "src" / "HttpRequestDispatcher.h"
        if dispatcher_file.exists():
            cmd.extend(["--dispatcher-file", str(dispatcher_file)])
            # print(f"Using dispatcher file: {dispatcher_file}")
        else:
            # print(f"⚠️  Warning: HttpRequestDispatcher.h not found at {dispatcher_file}")
            pass
        
        # print(f"\nRunning: {' '.join(cmd)}")
        # print(f"Include paths: {include_paths}")
        
        # Run the command
        try:
            result = subprocess.run(cmd, cwd=project_dir if project_dir else os.getcwd(), 
                                  capture_output=False, text=True)
            
            if result.returncode == 0:
                # print("\n✅ L7 CPP Spring Boot Preprocessor completed successfully")
                pass
            else:
                # print(f"\n⚠️  L7 CPP Spring Boot Preprocessor exited with code {result.returncode}")
                pass
        except Exception as e:
            # print(f"\n❌ Error running L7 CPP Spring Boot Preprocessor: {e}")
            pass
    else:
        # print("\n⚠️  No library directories found, skipping L7 preprocessing")
        pass
