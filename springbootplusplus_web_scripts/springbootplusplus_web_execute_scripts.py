"""
Script to execute client file processing.
This script imports get_client_files and processes the client project files.

When ``all_libs`` is set, ``SECURITY_CONFIGURATION_ENTRIES`` is filled with
``{"class_name": ..., "file_path": ...}`` dicts for every scanned C++ file that matches
/* @Configuration */ with an ISecurityConfig subclass (same roots as the RestController
preprocessor; see security_script/L7_resolve_security_configuration.py). Then
``run_l5_security_config_registry_codegen`` updates ``src/auth/SecurityConfigRegistry.h``
after the L7 CPP subprocess (so L6 can mark ``/* @Configuration */`` first while the
collect step still sees active annotations). See security_script/L5_apply_security_config_codegen.py.
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

# Populated by ``execute_scripts`` when ``all_libs`` is set (same scan roots as L6/L7 CPP).
SECURITY_CONFIGURATION_ENTRIES: List[Dict[str, str]] = []


def _find_cpp_files_same_as_l6(include_paths: List[str], exclude_paths: Optional[List[str]] = None) -> List[str]:
    """
    Same discovery rules as springbootplusplus_web_core/L6_generate_code_for_all_sources.find_cpp_files.
    Kept here to avoid importing L6 (heavy imports / sys.exit on missing deps).
    """
    exclude_paths = exclude_paths or []
    cpp_files: List[str] = []
    if not include_paths:
        include_paths = ["."]
    for include_path in include_paths:
        include_path_obj = Path(include_path).resolve()
        if not include_path_obj.exists():
            continue
        for ext in ["*.h", "*.hpp", "*.cpp", "*.cc", "*.cxx"]:
            for file_path in include_path_obj.rglob(ext):
                file_path_str = str(file_path.resolve())
                should_exclude = False
                for exclude_path in exclude_paths:
                    exclude_path_obj = Path(exclude_path).resolve()
                    try:
                        if file_path.resolve().is_relative_to(exclude_path_obj):
                            should_exclude = True
                            break
                    except ValueError:
                        pass
                if not should_exclude:
                    cpp_files.append(file_path_str)
    return sorted(cpp_files)


def collect_security_configuration_entries(
    include_paths: List[str],
    exclude_paths: Optional[List[str]] = None,
) -> List[Dict[str, str]]:
    """
    Walk the same C++ files as the RestController pipeline and collect security configs.

    Returns:
        List of {"class_name": str, "file_path": str} for each matching file.
    """
    sec_dir = Path(__file__).resolve().parent / "security_script"
    if not sec_dir.is_dir():
        return []
    sd = str(sec_dir)
    if sd not in sys.path:
        sys.path.insert(0, sd)
    try:
        from L7_resolve_security_configuration import resolve_security_configuration_file
    except ImportError:
        return []

    entries: List[Dict[str, str]] = []
    for fp in _find_cpp_files_same_as_l6(include_paths, exclude_paths):
        row = resolve_security_configuration_file(fp)
        if row:
            entries.append(row)
    return entries


def security_config_registry_header_path(library_dir: str) -> Path:
    """Absolute path to ``src/auth/SecurityConfigRegistry.h`` under the library root."""
    return Path(library_dir).resolve() / "src" / "auth" / "SecurityConfigRegistry.h"


def security_config_include_string_from_scan_roots(
    absolute_file_path: str,
    include_roots: List[str],
) -> str:
    """
    Return the resolved absolute path (posix) for use inside ``#include "..."``.

    ``include_roots`` is kept for call-site compatibility with the RestController scan
    list; it is not used (includes always use the full filesystem path of the config header).
    """
    del include_roots  # unused; same signature as when relative paths were derived from roots
    return Path(absolute_file_path).resolve().as_posix()


def run_l5_security_config_registry_codegen(
    library_dir: str,
    include_roots: List[str],
    entries: List[Dict[str, str]],
    *,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Run L5 (``apply_security_config_codegen``) on ``SecurityConfigRegistry.h``.

    ``entries`` should match ``SECURITY_CONFIGURATION_ENTRIES``: each item provides
    ``file_path`` (absolute) and ``class_name``. Include lines use the config header's
    resolved absolute path inside ``#include "..."``.
    """
    registry = security_config_registry_header_path(library_dir)
    if not registry.is_file():
        return {
            "success": False,
            "skipped": True,
            "reason": "SecurityConfigRegistry.h not found",
        }

    sec_dir = Path(__file__).resolve().parent / "security_script"
    if not sec_dir.is_dir():
        return {"success": False, "skipped": True, "reason": "security_script directory missing"}
    sd = str(sec_dir)
    if sd not in sys.path:
        sys.path.insert(0, sd)
    try:
        from L5_apply_security_config_codegen import apply_security_config_codegen
    except ImportError as exc:
        return {"success": False, "skipped": True, "reason": str(exc)}

    header_paths = [
        security_config_include_string_from_scan_roots(e["file_path"], include_roots) for e in entries
    ]
    class_names = [e["class_name"] for e in entries]

    return apply_security_config_codegen(
        str(registry),
        header_paths,
        class_names,
        dry_run=dry_run,
    )


try:
    from cpp_core_core.cpp_core_get_client_files import get_client_files
    HAS_cpp_core = True
except ImportError:
    # print("Warning: Could not import cpp_core_core.cpp_core_get_client_files")
    # print("         Some features may be unavailable.")
    HAS_cpp_core = False
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
    global SECURITY_CONFIGURATION_ENTRIES
    SECURITY_CONFIGURATION_ENTRIES = []

    # Process client files if cpp_core is available
    if HAS_cpp_core:
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
        # print("Skipping file processing - cpp_core_core not available")
        pass
    
    # Call L7_cpp_spring_boot_preprocessor.py with all library directories
    # This should run regardless of HAS_cpp_core
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

        # Same file set as L6 RestController / L7 CPP preprocessor: collect @Configuration + ISecurityConfig classes
        SECURITY_CONFIGURATION_ENTRIES = collect_security_configuration_entries(include_paths, exclude_paths=[])

        if not l7_script_path.exists():
            # print(f"⚠️  Warning: L7 script not found at {l7_script_path}")
            run_l5_security_config_registry_codegen(
                library_dir,
                include_paths,
                SECURITY_CONFIGURATION_ENTRIES,
                dry_run=False,
            )
            return

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

            run_l5_security_config_registry_codegen(
                library_dir,
                include_paths,
                SECURITY_CONFIGURATION_ENTRIES,
                dry_run=False,
            )
        except Exception as e:
            # print(f"\n❌ Error running L7 CPP Spring Boot Preprocessor: {e}")
            pass
    else:
        # print("\n⚠️  No library directories found, skipping L7 preprocessing")
        pass
