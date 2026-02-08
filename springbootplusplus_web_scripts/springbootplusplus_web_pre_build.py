# Print message immediately when script is loaded
# print("Hello from library number 2")

# Import PlatformIO environment first (if available)
env = None
try:
    Import("env")
except NameError:
    # Not running in PlatformIO environment (e.g., running from CMake)
    # print("Note: Not running in PlatformIO environment - some features may be limited")
    # Create a mock env object for CMake builds
    class MockEnv:
        def get(self, key, default=None):
            return default
    env = MockEnv()

import sys
import os
from pathlib import Path


def get_library_dir():
    """
    Find the springbootplusplus_web_scripts directory by searching up the directory tree.
    
    Returns:
        Path: Path to the springbootplusplus_web_scripts directory
        
    Raises:
        ImportError: If the directory cannot be found
    """
    cwd = Path(os.getcwd())
    current = cwd
    for _ in range(10):  # Search up to 10 levels
        potential = current / "springbootplusplus_web_scripts"
        if potential.exists() and potential.is_dir():
            # print(f"✓ Found library path by searching up directory tree: {potential}")
            return potential
        parent = current.parent
        if parent == current:  # Reached filesystem root
            break
        current = parent
    raise ImportError("Could not find springbootplusplus_web_scripts directory")


def get_project_dir():
    """
    Get the project directory from PlatformIO environment or CMake environment.
    
    Returns:
        str: Path to the project directory, or None if not found
    """
    # Try PlatformIO environment first
    project_dir = None
    if env:
        project_dir = env.get("PROJECT_DIR", None)
    
    # If not found, try CMake environment variable
    if not project_dir:
        project_dir = os.environ.get("CMAKE_PROJECT_DIR", None)
    
    if project_dir:
        # print(f"\nClient project directory: {project_dir}")
        pass
    else:
        # print("Warning: Could not determine PROJECT_DIR from environment")
        pass
    return project_dir


def get_all_library_dirs(project_dir=None):
    """
    Get all library directories (both scripts directories and root directories).
    
    This function discovers all library directories by:
    1. Checking CMake FetchContent locations (build/_deps/)
    2. Checking PlatformIO library locations (.pio/libdeps/)
    3. Checking current directory and parent directories
    
    Args:
        project_dir: Optional project directory to search from. If None, uses get_project_dir()
    
    Returns:
        Dictionary with:
        - 'scripts_dirs': List of paths to library scripts directories (e.g., serializationlib_scripts)
        - 'root_dirs': List of paths to library root directories (e.g., serializationlib-src)
        - 'by_name': Dictionary mapping library names to their root directories
    """
    if project_dir is None:
        project_dir = get_project_dir()
    
    scripts_dirs = []
    root_dirs = []
    by_name = {}
    
    search_paths = []
    
    # Add current working directory
    search_paths.append(Path(os.getcwd()))
    
    # Add project directory if available
    if project_dir:
        project_path = Path(project_dir)
        search_paths.append(project_path)
        
        # Check CMake FetchContent location: build/_deps/
        build_deps = project_path / "build" / "_deps"
        if build_deps.exists() and build_deps.is_dir():
            # Find all library directories in _deps
            for lib_dir in build_deps.iterdir():
                if lib_dir.is_dir() and lib_dir.name.endswith("-src"):
                    lib_root = lib_dir.resolve()
                    root_dirs.append(lib_root)
                    
                    # Extract library name (e.g., "serializationlib-src" -> "serializationlib")
                    lib_name = lib_dir.name[:-4]  # Remove "-src" suffix
                    by_name[lib_name] = lib_root
                    
                    # Check for scripts directory
                    scripts_dir = lib_root / f"{lib_name}_scripts"
                    if scripts_dir.exists() and scripts_dir.is_dir():
                        scripts_dirs.append(scripts_dir.resolve())
    
    # Add library directory (parent of springbootplusplus_web_scripts)
    library_scripts_dir = get_library_dir()
    library_dir = library_scripts_dir.parent
    search_paths.append(library_dir)
    
    # If we're in a CMake build, check sibling directories in _deps
    if "springbootplusplus_web-src" in str(library_dir) or "_deps" in str(library_dir):
        parent_deps = library_dir.parent
        if parent_deps.exists() and parent_deps.name == "_deps":
            # Find all library directories in _deps
            for lib_dir in parent_deps.iterdir():
                if lib_dir.is_dir() and lib_dir.name.endswith("-src"):
                    lib_root = lib_dir.resolve()
                    if lib_root not in root_dirs:
                        root_dirs.append(lib_root)
                        
                        # Extract library name
                        lib_name = lib_dir.name[:-4]  # Remove "-src" suffix
                        if lib_name not in by_name:
                            by_name[lib_name] = lib_root
                        
                        # Check for scripts directory
                        scripts_dir = lib_root / f"{lib_name}_scripts"
                        if scripts_dir.exists() and scripts_dir.is_dir():
                            scripts_dirs.append(scripts_dir.resolve())
    
    # Search in each path for PlatformIO libraries
    for start_path in search_paths:
        current = start_path.resolve()
        for _ in range(10):  # Search up to 10 levels
            # Check in .pio/libdeps/ (PlatformIO location)
            # Structure: .pio/libdeps/<env>/<library_name>/
            pio_path = current / ".pio" / "libdeps"
            if pio_path.exists() and pio_path.is_dir():
                # Iterate through environment directories (e.g., esp32dev, native, etc.)
                for env_dir in pio_path.iterdir():
                    if env_dir.is_dir():
                        # Now iterate through libraries in this environment
                        for lib_dir in env_dir.iterdir():
                            if lib_dir.is_dir():
                                lib_root = lib_dir.resolve()
                                if lib_root not in root_dirs:
                                    root_dirs.append(lib_root)
                                    
                                    # Try to extract library name from directory name
                                    lib_name = lib_dir.name
                                    # Use library name as key (may have duplicates across envs, but that's okay)
                                    if lib_name not in by_name:
                                        by_name[lib_name] = lib_root
                                    
                                    # Check for scripts directory (various naming patterns)
                                    possible_scripts_names = [
                                        f"{lib_name}_scripts",
                                        f"{lib_name.replace('-', '')}_scripts",
                                        "scripts"
                                    ]
                                    for scripts_name in possible_scripts_names:
                                        scripts_dir = lib_root / scripts_name
                                        if scripts_dir.exists() and scripts_dir.is_dir():
                                            if scripts_dir.resolve() not in scripts_dirs:
                                                scripts_dirs.append(scripts_dir.resolve())
                                            break
            
            parent = current.parent
            if parent == current:  # Reached filesystem root
                break
            current = parent
    
    return {
        'scripts_dirs': scripts_dirs,
        'root_dirs': root_dirs,
        'by_name': by_name
    }


def find_library_scripts(scripts_dir_name):
    """
    Find a library scripts directory by searching from current directory and project directory.
    
    Args:
        scripts_dir_name: Name of the scripts directory to find (e.g., "serializationlib_scripts")
    
    Returns:
        Path: Path to the scripts directory, or None if not found
    """
    # Derive library source directory name from scripts directory name
    # e.g., "serializationlib_scripts" -> "serializationlib-src"
    if scripts_dir_name.endswith("_scripts"):
        lib_name = scripts_dir_name[:-8]  # Remove "_scripts" suffix
        lib_src_name = f"{lib_name}-src"
    else:
        # Fallback: assume scripts_dir_name is the library name
        lib_src_name = f"{scripts_dir_name}-src"
    
    search_paths = []
    
    # Add current working directory
    search_paths.append(Path(os.getcwd()))
    
    # Add project directory if available
    project_dir = get_project_dir()
    if project_dir:
        project_path = Path(project_dir)
        search_paths.append(project_path)
        
        # Check build/_deps/{lib_src_name}/{scripts_dir_name} from project directory
        build_deps = project_path / "build" / "_deps" / lib_src_name / scripts_dir_name
        if build_deps.exists() and build_deps.is_dir():
            # print(f"✓ Found {scripts_dir_name} (CMake from project): {build_deps}")
            return build_deps
    
    # Add library directory (parent of springbootplusplus_web_scripts)
    library_scripts_dir = get_library_dir()
    library_dir = library_scripts_dir.parent
    search_paths.append(library_dir)
    
    # If we're in a CMake build, check sibling directory ({lib_src_name} next to springbootplusplus_web-src)
    if "springbootplusplus_web-src" in str(library_dir) or "_deps" in str(library_dir):
        # We're in a CMake FetchContent location, check sibling
        parent_deps = library_dir.parent
        if parent_deps.exists() and parent_deps.name == "_deps":
            lib_src = parent_deps / lib_src_name / scripts_dir_name
            if lib_src.exists() and lib_src.is_dir():
                # print(f"✓ Found {scripts_dir_name} (CMake sibling): {lib_src}")
                return lib_src
            # Also check if {lib_src_name} exists but scripts might be in root
            lib_root = parent_deps / lib_src_name
            if lib_root.exists():
                lib_scripts = lib_root / scripts_dir_name
                if lib_scripts.exists() and lib_scripts.is_dir():
                    # print(f"✓ Found {scripts_dir_name} (CMake sibling root): {lib_scripts}")
                    return lib_scripts
    
    # Search in each path and their parent directories
    for start_path in search_paths:
        current = start_path.resolve()
        for _ in range(10):  # Search up to 10 levels
            # Check for {scripts_dir_name} in current directory
            potential = current / scripts_dir_name
            if potential.exists() and potential.is_dir():
                # print(f"✓ Found {scripts_dir_name}: {potential}")
                return potential
            
            # Check in build/_deps/{lib_src_name}/ (CMake FetchContent location)
            deps_path = current / "build" / "_deps" / lib_src_name / scripts_dir_name
            if deps_path.exists() and deps_path.is_dir():
                # print(f"✓ Found {scripts_dir_name} (CMake): {deps_path}")
                return deps_path
            
            # Check in .pio/libdeps/ (PlatformIO location)
            # Structure: .pio/libdeps/<env>/<library_name>/
            pio_path = current / ".pio" / "libdeps"
            if pio_path.exists():
                # Iterate through environment directories (e.g., esp32dev, native, etc.)
                for env_dir in pio_path.iterdir():
                    if env_dir.is_dir():
                        # Now iterate through libraries in this environment
                        for lib_dir in env_dir.iterdir():
                            if lib_dir.is_dir():
                                lib_scripts_path = lib_dir / scripts_dir_name
                                if lib_scripts_path.exists() and lib_scripts_path.is_dir():
                                    # print(f"✓ Found {scripts_dir_name} (PlatformIO): {lib_scripts_path}")
                                    return lib_scripts_path
            
            parent = current.parent
            if parent == current:  # Reached filesystem root
                break
            current = parent
    
    # print(f"Warning: Could not find {scripts_dir_name} directory")
    return None


# Get library scripts directory and add it to Python path
library_scripts_dir = get_library_dir()
sys.path.insert(0, str(library_scripts_dir))

# Find and add cpp_core scripts to Python path
cpp_core_scripts_dir = find_library_scripts("cpp_core_scripts")
if cpp_core_scripts_dir:
    sys.path.insert(0, str(cpp_core_scripts_dir))

# Find and add serializationlib_scripts to Python path
serializationlib_scripts_dir = find_library_scripts("serializationlib_scripts")
if serializationlib_scripts_dir:
    sys.path.insert(0, str(serializationlib_scripts_dir))

# Get library root directory (parent of springbootplusplus_web_scripts)
library_dir = library_scripts_dir.parent

# Get project directory
project_dir = get_project_dir()

# Get all library directories (available for use in scripts)
all_libs = get_all_library_dirs(project_dir)
if all_libs['root_dirs']:
    # print(f"\n📚 DDEE Found {len(all_libs['root_dirs'])} library directory(ies):")
    # for lib_name, lib_dir in sorted(all_libs['by_name'].items()):
    #     print(f"   - {lib_name}: {lib_dir}")
    pass
if all_libs['scripts_dirs']:
    # print(f"\n📜 DDMM Found {len(all_libs['scripts_dirs'])} library scripts directory(ies)")
    pass

# Import and execute scripts
from springbootplusplus_web_execute_scripts import execute_scripts
execute_scripts(project_dir, library_dir, all_libs, library_scripts_dir)

