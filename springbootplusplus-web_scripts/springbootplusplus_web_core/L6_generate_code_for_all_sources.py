#!/usr/bin/env python3
"""
L6 Generate Code for All Sources Script

This script:
1. Finds all C++ source files (using logic from L6_cpp_di_preprocessor.py)
2. Generates endpoint code for each file using L5_generate_code_for_file.py
3. Marks REST-related annotations as processed (/* @RestController */, /* @RequestMapping("...") */, etc.) in processed files
4. Stores valid results in a map
5. Adds #include statements to EventDispatcher.h
6. Updates InitializeMappings() function with all generated code
"""

import argparse
import sys
import os
import re
from pathlib import Path
from typing import Dict, List, Optional

# Add springbootplusplus_web_core directory to path for imports (current directory)
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

try:
    import L5_generate_all_endpoints as L5_generate_code_for_file
    import L3_get_endpoint_details
    import L1_find_class_header
except ImportError as e:
    # print(f"Error: Could not import required modules: {e}")
    # print("Make sure L5_generate_all_endpoints.py, L3_get_endpoint_details.py, and L1_find_class_header.py are in the springbootplusplus_web_core directory.")
    sys.exit(1)


def find_cpp_files(include_paths: List[str], exclude_paths: List[str]) -> List[str]:
    """
    Find all C++ source files in the specified include/exclude paths.
    Uses the same logic as L6_cpp_di_preprocessor.py
    
    Args:
        include_paths: List of include paths to search in
        exclude_paths: List of exclude paths to avoid
        
    Returns:
        List of C++ file paths (absolute paths)
    """
    cpp_files = []
    
    # If no include paths specified, search current directory
    if not include_paths:
        include_paths = ["."]
    
    for include_path in include_paths:
        include_path_obj = Path(include_path).resolve()
        if not include_path_obj.exists():
            # print(f"⚠️  Warning: Include path '{include_path}' does not exist")
            continue
            
        # Find all C++ source files (.h, .hpp, .cpp, .cc, .cxx)
        for ext in ["*.h", "*.hpp", "*.cpp", "*.cc", "*.cxx"]:
            for file_path in include_path_obj.rglob(ext):
                file_path_str = str(file_path.resolve())
                # Check if file should be excluded
                should_exclude = False
                for exclude_path in exclude_paths:
                    exclude_path_obj = Path(exclude_path).resolve()
                    try:
                        if file_path.resolve().is_relative_to(exclude_path_obj):
                            should_exclude = True
                            break
                    except ValueError:
                        # Path is not relative to exclude_path, continue checking
                        pass
                
                if not should_exclude:
                    cpp_files.append(file_path_str)
    
    return sorted(cpp_files)


def comment_rest_macros(file_path: str, dry_run: bool = False) -> bool:
    """
    Mark all REST-related annotations as processed (/* @RestController */, /* @RequestMapping("...") */, etc.) in a C++ file.
    Converts /* @RestController */ to /* @Component */, and other /* @Annotation */ to /*--@Annotation--*/.
    Comments out legacy macros.
    
    Args:
        file_path: Path to the C++ file to modify
        dry_run: If True, only show what would be changed without making changes
        
    Returns:
        True if file was modified successfully or would be modified, False otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        # Patterns for @RestController annotation (search for /* @RestController */ or /*@RestController*/)
        rest_controller_annotation_pattern = re.compile(r'/\*\s*@RestController\s*\*/')
        rest_controller_processed_pattern = re.compile(r'/\*--\s*@RestController\s*--\*/')
        # Pattern to check if @Component already exists (to avoid duplicate)
        component_annotation_pattern = re.compile(r'/\*\s*@Component\s*\*/')
        component_processed_pattern = re.compile(r'/\*--\s*@Component\s*--\*/')
        
        # Patterns for REST mapping annotations (search for /* @Annotation("...") */ or /*@Annotation("...")*/)
        rest_mapping_annotations = {
            'RequestMapping': (re.compile(r'/\*\s*@RequestMapping\s*\(\s*["\']([^"\']+)["\']\s*\)\s*\*/'), re.compile(r'/\*--\s*@RequestMapping\s*\(\s*["\'][^"\']+["\']\s*\)\s*--\*/')),
            'GetMapping': (re.compile(r'/\*\s*@GetMapping\s*\(\s*["\']([^"\']+)["\']\s*\)\s*\*/'), re.compile(r'/\*--\s*@GetMapping\s*\(\s*["\'][^"\']+["\']\s*\)\s*--\*/')),
            'PostMapping': (re.compile(r'/\*\s*@PostMapping\s*\(\s*["\']([^"\']+)["\']\s*\)\s*\*/'), re.compile(r'/\*--\s*@PostMapping\s*\(\s*["\'][^"\']+["\']\s*\)\s*--\*/')),
            'PutMapping': (re.compile(r'/\*\s*@PutMapping\s*\(\s*["\']([^"\']+)["\']\s*\)\s*\*/'), re.compile(r'/\*--\s*@PutMapping\s*\(\s*["\'][^"\']+["\']\s*\)\s*--\*/')),
            'DeleteMapping': (re.compile(r'/\*\s*@DeleteMapping\s*\(\s*["\']([^"\']+)["\']\s*\)\s*\*/'), re.compile(r'/\*--\s*@DeleteMapping\s*\(\s*["\'][^"\']+["\']\s*\)\s*--\*/')),
            'PatchMapping': (re.compile(r'/\*\s*@PatchMapping\s*\(\s*["\']([^"\']+)["\']\s*\)\s*\*/'), re.compile(r'/\*--\s*@PatchMapping\s*\(\s*["\'][^"\']+["\']\s*\)\s*--\*/'))
        }
        
        # Legacy REST-related macros (for backward compatibility, will be commented out)
        rest_macros = [
            'RestController', 'RequestMapping', 'GetMapping', 'PostMapping',
            'PutMapping', 'DeleteMapping', 'PatchMapping'
        ]
        
        modified = False
        modified_lines = []
        
        for i, line in enumerate(lines):
            original_line = line
            stripped_line = line.strip()
            
            # Process @RestController annotation - replace with @Component
            if rest_controller_processed_pattern.search(stripped_line):
                modified_lines.append(line)
                continue
            
            rest_controller_match = rest_controller_annotation_pattern.search(stripped_line)
            if rest_controller_match:
                indent = len(line) - len(line.lstrip())
                indent_str = line[:indent]
                # Replace /* @RestController */ with /* @Component */
                processed_line = f"{indent_str}/* @Component */\n"
                if not dry_run:
                    modified_lines.append(processed_line)
                else:
                    modified_lines.append(line)
                modified = True
                continue
            
            # Process other REST mapping annotations
            annotation_processed = False
            for annotation_name, (annotation_pattern, processed_pattern) in rest_mapping_annotations.items():
                if processed_pattern.search(stripped_line):
                    modified_lines.append(line)
                    annotation_processed = True
                    break
                
                annotation_match = annotation_pattern.search(stripped_line)
                if annotation_match:
                    indent = len(line) - len(line.lstrip())
                    indent_str = line[:indent]
                    # Extract the annotation name and path value
                    annotation_name = annotation_name  # e.g., "GetMapping"
                    path_value = annotation_match.group(1)  # Extract path from group 1
                    processed_line = f"{indent_str}/*--@{annotation_name}(\"{path_value}\")--*/\n"
                    if not dry_run:
                        modified_lines.append(processed_line)
                    else:
                        modified_lines.append(line)
                    modified = True
                    annotation_processed = True
                    break
            
            if annotation_processed:
                continue
            
            # Skip other comments that aren't REST annotations
            # But allow /* @RestController */, /* @RequestMapping("...") */, etc. to be processed
            if stripped_line.startswith('/*') and not (rest_controller_annotation_pattern.search(stripped_line) or any(ann[0].search(stripped_line) for ann in rest_mapping_annotations.values())):
                modified_lines.append(line)
                continue
            # Skip single-line comments
            if stripped_line.startswith('//'):
                modified_lines.append(line)
                continue
            
            # Check if line starts with any legacy REST macro (for backward compatibility)
            line_modified = False
            for macro in rest_macros:
                pattern = re.compile(r'^' + re.escape(macro) + r'(?:\s*\([^)]*\))?\s*$')
                if pattern.match(stripped_line):
                    if not dry_run:
                        modified_lines.append('// ' + line)
                    else:
                        modified_lines.append(line)
                    modified = True
                    line_modified = True
                    break
            
            if not line_modified:
                modified_lines.append(line)
        
        if modified and not dry_run:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.writelines(modified_lines)
            # print(f"✓ Processed REST annotations/macros in: {file_path}")
        elif modified and dry_run:
            # print(f"  Would process REST annotations/macros in: {file_path}")
            pass
        elif not modified:
            pass
        
        return True
        
    except FileNotFoundError:
        # print(f"Error: File '{file_path}' not found")
        return False
    except Exception as e:
        # print(f"Error modifying file '{file_path}': {e}")
        return False


def generate_code_map(cpp_files: List[str], dry_run: bool = False) -> Dict[str, Dict[str, str]]:
    """
    Generate code for all source files and store valid results in a map.
    Also comments out REST-related macros in processed files.
    
    Args:
        cpp_files: List of C++ file paths to process
        dry_run: If True, don't actually comment macros, just show what would be done
        
    Returns:
        Dictionary mapping file paths (absolute) to dictionaries with 'code' and 'interface_name' keys
    """
    # print("🔄 Generating code for files with RestController...")
    
    code_map = {}
    processed_count = 0
    skipped_count = 0
    
    for file_path in cpp_files:
        # Generate code for this file
        generated_code = L5_generate_code_for_file.generate_code_for_file(file_path)
        
        # Only add to map if code is valid (not empty, not None)
        if generated_code and generated_code.strip():
            # Get interface name from the file
            class_info = L3_get_endpoint_details.find_class_and_interface(file_path)
            interface_name = class_info['interface_name'] if class_info else None
            
            code_map[file_path] = {
                'code': generated_code,
                'interface_name': interface_name
            }
            processed_count += 1
            
            # Mark REST-related annotations as processed in this file
            if not dry_run:
                # print(f"  Processing REST annotations in: {file_path}")
                pass
            else:
                # print(f"  Would process REST annotations in: {file_path}")
                pass
            comment_rest_macros(file_path, dry_run=dry_run)
        else:
            skipped_count += 1
    
    # print(f"✅ Processed {processed_count} file(s) with RestController")
    # print(f"⏭️  Skipped {skipped_count} file(s) without RestController")
    
    return code_map


def generate_includes(code_map: Dict[str, Dict[str, str]], project_root: Optional[str] = None, include_paths: List[str] = None, exclude_paths: List[str] = None) -> List[str]:
    """
    Generate #include statements for interface headers of all files in the code map.
    
    Args:
        code_map: Dictionary mapping file paths to dictionaries with 'code' and 'interface_name'
        project_root: Project root directory (if None, will try to find it)
        include_paths: List of include paths to search for interface headers
        exclude_paths: List of exclude paths to avoid when searching
        
    Returns:
        List of #include statements for interface headers
    """
    includes = []
    
    # Find project root if not provided
    if project_root is None:
        # Try to find project root by looking for common markers
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(script_dir))  # Go up from springbootplusplus_web_core/springbootplusplus_web_scripts/ to project root
    
    project_root_path = Path(project_root).resolve()
    
    # Default include/exclude paths if not provided
    if include_paths is None:
        include_paths = ["src"]
    if exclude_paths is None:
        exclude_paths = []
    
    for file_path in sorted(code_map.keys()):
        file_info = code_map[file_path]
        interface_name = file_info.get('interface_name')
        
        if not interface_name:
            # Fallback: use implementation header if interface name not found
            file_path_obj = Path(file_path).resolve()
            include_path = str(file_path_obj).replace('\\', '/')  # Use absolute path
            includes.append(f'#include "{include_path}"')
            continue
        
        # Find interface header file
        interface_header = L1_find_class_header.find_class_header_file(
            class_name=interface_name,
            search_root=project_root,
            include_folders=include_paths,
            exclude_folders=exclude_paths
        )
        
        if interface_header:
            # Use absolute path for the include
            interface_header_obj = Path(interface_header).resolve()
            include_path = str(interface_header_obj).replace('\\', '/')  # Normalize path separators
            includes.append(f'#include "{include_path}"')
        else:
            # Fallback: use implementation header if interface header not found
            file_path_obj = Path(file_path).resolve()
            include_path = str(file_path_obj).replace('\\', '/')  # Use absolute path
            includes.append(f'#include "{include_path}"')
    
    return includes


def add_includes_to_event_dispatcher(file_path: str, includes: List[str]) -> bool:
    """
    Add #include statements to EventDispatcher.h after line 6.
    
    Args:
        file_path: Path to EventDispatcher.h
        includes: List of #include statements to add
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Find line 6 (index 5) which has #include "01-IEventDispatcher.h"
        # We want to add includes after this line
        insert_index = 6  # After line 6 (0-indexed is line 6)
        
        if insert_index >= len(lines):
            # print(f"Error: Cannot find insertion point in {file_path}")
            return False
        
        # Remove all existing controller includes (they will be replaced with correct ones)
        # Look for includes that point to controller files
        import re
        lines_to_remove = []
        for i, line in enumerate(lines):
            if line.strip().startswith('#include'):
                # Check if this is a controller include (contains "controller" in path or matches pattern)
                if 'controller' in line.lower() or re.search(r'/\d+-[A-Za-z0-9_]*Controller\.h', line):
                    lines_to_remove.append(i)
        
        # Remove lines in reverse order to maintain indices
        for i in reversed(lines_to_remove):
            del lines[i]
        
        # Check if includes already exist (after removal)
        existing_includes = set()
        for i, line in enumerate(lines):
            if line.strip().startswith('#include'):
                existing_includes.add(line.strip())
        
        # Filter out includes that already exist
        new_includes = []
        for include in includes:
            if include not in existing_includes:
                new_includes.append(include + '\n')
        
        if not new_includes and not lines_to_remove:
            # print("ℹ️  All includes already exist in EventDispatcher.h")
            return True
        
        # Find the insertion point (after line 6, but account for removed lines)
        # Recalculate insert_index after removals
        insert_index = 6
        for removed_idx in lines_to_remove:
            if removed_idx < insert_index:
                insert_index -= 1
        
        # Insert new includes after line 6
        if new_includes:
            lines[insert_index:insert_index] = new_includes + ['\n']  # Add blank line after includes
        
        # Write back to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        # print(f"✅ Added {len(new_includes)} include(s) to EventDispatcher.h")
        return True
        
    except Exception as e:
        # print(f"Error updating EventDispatcher.h: {e}")
        return False


def update_initialize_mappings(file_path: str, code_content: str) -> bool:
    """
    Replace the InitializeMappings() function body with the provided code.
    
    Args:
        file_path: Path to EventDispatcher.h
        code_content: Code content to insert into InitializeMappings()
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Pattern to match InitializeMappings() function
        # Matches: Private Void InitializeMappings() { ... }
        # We need to find the matching closing brace by counting braces, not just the first }
        pattern = r'(Private\s+Void\s+InitializeMappings\s*\(\s*\)\s*\{)'
        
        match = re.search(pattern, content, flags=re.MULTILINE)
        if not match:
            # print("⚠️  Warning: Could not find InitializeMappings() function to update")
            return False
        
        # Find the matching closing brace by counting braces
        start_pos = match.end()
        brace_count = 1  # We're already inside the opening brace
        pos = start_pos
        
        while pos < len(content) and brace_count > 0:
            if content[pos] == '{':
                brace_count += 1
            elif content[pos] == '}':
                brace_count -= 1
            pos += 1
        
        if brace_count != 0:
            # print("⚠️  Warning: Could not find matching closing brace for InitializeMappings()")
            return False
        
        # Extract the function header and footer
        function_header = match.group(0)
        function_footer = '}'
        
        # Split code_content into lines and indent each line
        if code_content.strip():
            code_lines = code_content.strip().split('\n')
            indented_lines = ['        ' + line if line.strip() else '' for line in code_lines]
            indented_code = '\n'.join(indented_lines)
            replacement = f"{function_header}\n{indented_code}\n    {function_footer}"
        else:
            replacement = f"{function_header}\n    {function_footer}"
        
        # Replace the function
        new_content = content[:match.start()] + replacement + content[pos:]
        
        if new_content == content:
            # print("⚠️  Warning: Could not find InitializeMappings() function to update")
            return False
        
        # Write back to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        # print("✅ Updated InitializeMappings() function in EventDispatcher.h")
        return True
        
    except Exception as e:
        # print(f"Error updating InitializeMappings(): {e}")
        return False


def main():
    """Main function to handle command line arguments and execute the code generation."""
    parser = argparse.ArgumentParser(
        description="Generate endpoint code for all source files and update EventDispatcher.h",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python springbootplusplus_web_core/L6_generate_code_for_all_sources.py --include src platform                    # Process all files in src and platform
  python springbootplusplus_web_core/L6_generate_code_for_all_sources.py --include src --exclude platform/arduino  # Process with exclude
  python springbootplusplus_web_core/L6_generate_code_for_all_sources.py --include src platform --dry-run          # Dry run to see what would happen
  python springbootplusplus_web_core/L6_generate_code_for_all_sources.py --dry-run                                 # Dry run on all files in current directory
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
    # print("🔧 L6 Generate Code for All Sources Configuration")
    # print("=" * 50)
    # print(f"Include paths: {args.include if args.include else ['current directory']}")
    # print(f"Exclude paths: {args.exclude if args.exclude else ['none']}")
    # print(f"Dispatcher file: {args.dispatcher_file}")
    # print(f"Dry run: {'Yes' if args.dry_run else 'No'}")
    # print()
    
    # Find all C++ files
    # print("🔍 Discovering C++ source files...")
    cpp_files = find_cpp_files(args.include, args.exclude)
    
    if not cpp_files:
        # print("⚠️  No C++ source files found in the specified paths")
        sys.exit(0)
    
    # print(f"📁 Found {len(cpp_files)} C++ source files")
    
    # Generate code map (this will also comment out REST macros)
    code_map = generate_code_map(cpp_files, dry_run=args.dry_run)
    
    if not code_map:
        # print("⚠️  No files with RestController found. Nothing to update.")
        sys.exit(0)
    
    # print(f"\n📊 Generated code for {len(code_map)} file(s)")
    
    if args.dry_run:
        # print("\n🔍 DRY RUN MODE - No changes will be made")
        # print("\nController files found:")
        # for file_path in sorted(code_map.keys()):
        #     interface_name = code_map[file_path].get('interface_name', 'Unknown')
        #     print(f"  {file_path} (interface: {interface_name})")
        # Note: REST macros that would be commented are already shown during generate_code_map
        # print("\nIncludes that would be added (interface headers):")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        includes = generate_includes(code_map, project_root, args.include, args.exclude)
        # Add SerializeUtility.h include for dry run display
        serialize_utility_path = os.path.join(project_root, "src/01-framework/01-core/01-serializer/02-generic/04-SerializeUtility.h")
        serialize_utility_path_obj = Path(serialize_utility_path).resolve()
        if serialize_utility_path_obj.exists():
            include_path = str(serialize_utility_path_obj).replace('\\', '/')
            serialize_utility_include = f'#include "{include_path}"'
            includes.insert(0, serialize_utility_include)
        # for include in includes:
        #     print(f"  {include}")
        # print("\nCode that would be added to InitializeMappings():")
        all_code = '\n\n'.join([info['code'] for info in code_map.values()])
        # print(all_code[:500] + "..." if len(all_code) > 500 else all_code)
        return
    
    # Get project root (parent of script directory)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)  # This gives springbootplusplus_web_scripts
    # Go up one more level to get to springbootplusplus_web
    springbootplusplus_web_root = os.path.dirname(project_root)  # This gives springbootplusplus_web
    
    # Generate includes (for interface headers)
    includes = generate_includes(code_map, project_root, args.include, args.exclude)
    
    # Add SerializeUtility.h include (required for serialize template function)
    serialize_utility_path = os.path.join(project_root, "src/01-framework/01-core/01-serializer/02-generic/04-SerializeUtility.h")
    serialize_utility_path_obj = Path(serialize_utility_path).resolve()
    if serialize_utility_path_obj.exists():
        include_path = str(serialize_utility_path_obj).replace('\\', '/')
        serialize_utility_include = f'#include "{include_path}"'
        # Add it at the beginning of includes list (before controller includes)
        includes.insert(0, serialize_utility_include)
    else:
        # print(f"⚠️  Warning: SerializeUtility.h not found at '{serialize_utility_path}', serialize() function may not be available")
        pass
    
    # Add ResponseEntityToHttpResponse.h include (required for CreateOkResponse utility functions)
    # Try multiple possible paths relative to different root directories
    response_entity_converter_paths = [
        os.path.join(springbootplusplus_web_root, "src/ResponseEntityToHttpResponse.h"),  # springbootplusplus_web/src/ResponseEntityToHttpResponse.h
        os.path.join(project_root, "../springbootplusplus_web/src/ResponseEntityToHttpResponse.h"),  # Fallback relative path
        os.path.join(project_root, "src/ResponseEntityToHttpResponse.h"),  # Alternative location
    ]
    
    response_entity_converter_include = None
    for converter_path in response_entity_converter_paths:
        converter_path_obj = Path(converter_path).resolve()
        if converter_path_obj.exists():
            include_path = str(converter_path_obj).replace('\\', '/')
            response_entity_converter_include = f'#include "{include_path}"'
            break
    
    if response_entity_converter_include:
        # Add it after SerializeUtility but before controller includes
        if includes:
            includes.insert(1, response_entity_converter_include)
        else:
            includes.insert(0, response_entity_converter_include)
    
    # Add includes to EventDispatcher.h
    dispatcher_file = args.dispatcher_file
    if not os.path.exists(dispatcher_file):
        # print(f"Error: EventDispatcher.h file not found at '{dispatcher_file}'")
        sys.exit(1)
    
    if not add_includes_to_event_dispatcher(dispatcher_file, includes):
        # print("Error: Failed to add includes to EventDispatcher.h")
        sys.exit(1)
    
    # Concatenate all code values
    all_code = '\n\n'.join([info['code'] for info in code_map.values()])
    
    # Update InitializeMappings() function
    if not update_initialize_mappings(dispatcher_file, all_code):
        # print("Error: Failed to update InitializeMappings() function")
        sys.exit(1)
    
    # print("\n✅ Successfully updated EventDispatcher.h")
    # print(f"   - Added {len(includes)} include(s)")
    # print(f"   - Updated InitializeMappings() with code from {len(code_map)} controller(s)")
    
    # Show detailed results if requested
    if args.summary:
        # print(f"\n📋 DETAILED RESULTS")
        # print("=" * 50)
        # for file_path in sorted(code_map.keys()):
        #     print(f"  {file_path}: ✅ Generated code")
        pass
    
    # Exit with appropriate code
    sys.exit(0)


# Export functions for other scripts to import
__all__ = [
    'find_cpp_files',
    'comment_rest_macros',
    'generate_code_map',
    'generate_includes',
    'add_includes_to_event_dispatcher',
    'update_initialize_mappings',
    'main'
]


if __name__ == "__main__":
    main()

