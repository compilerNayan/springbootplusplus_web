#!/usr/bin/env python3
"""
Script to add instance code to C++ classes based on their scope.
Injects appropriate GetInstance() methods and friend declarations before the class closing brace.
"""

import re
import argparse
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import L2_get_file_scope
import find_class_names
import find_interface_names
import L1_get_validator_name


def find_class_closing_brace(file_path: str) -> Optional[Tuple[int, str]]:
    """
    Find the line containing the class closing brace '};'.
    Uses brace counting to find the correct closing brace even when there are nested braces.
    
    Args:
        file_path: Path to the C++ file
    
    Returns:
        Tuple of (line_number, line_content) or None if not found
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
    except FileNotFoundError:
        # print(f"Error: File '{file_path}' not found")
        return None
    except Exception as e:
        # print(f"Error reading file '{file_path}': {e}")
        return None
    
    # Pattern to match class declaration
    class_pattern = r'class\s+[A-Za-z_][A-Za-z0-9_]*\s*(?:.*?[:{]|[:{])'
    
    class_start = None
    brace_count = 0
    
    for line_num, line in enumerate(lines, 1):
        stripped_line = line.strip()
        
        # Skip commented lines
        if stripped_line.startswith('//') or stripped_line.startswith('/*') or stripped_line.startswith('*'):
            continue
        
        # Check if this is the class declaration line
        if class_start is None:
            if re.search(class_pattern, stripped_line):
                class_start = line_num
                # Count opening brace on the same line
                brace_count += stripped_line.count('{')
                brace_count -= stripped_line.count('}')
                if brace_count > 0:
                    continue
        
        # If we're inside the class, count braces
        if class_start is not None:
            # Check if this line is the class closing brace BEFORE counting
            # The class closes when we have a `};` and brace_count is 0 (all nested structures are closed)
            # We need to check BEFORE processing because after processing, brace_count becomes -1
            if stripped_line == '};' and brace_count == 0:
                return (line_num, line)
            
            brace_count += stripped_line.count('{')
            brace_count -= stripped_line.count('}')
            
            # Also check after processing (in case the line has both opening and closing braces)
            if brace_count == 0 and stripped_line == '};':
                return (line_num, line)
    
    return None


def generate_instance_code(scope: str, class_name: str, interface_name: str, validator_name: Optional[str] = None) -> str:
    """
    Generate the appropriate instance code based on scope.
    
    Args:
        scope: The file scope (SINGLETON, PROTOTYPE, SINGLETON_VALIDATOR, PROTOTYPE_VALIDATOR)
        class_name: Name of the class
        interface_name: Name of the interface
        validator_name: Name of the validator (if applicable)
        
    Returns:
        Generated code string to inject
    """
    # Generate pointer type names based on the naming convention
    interface_ptr_type = f"{interface_name}Ptr"
    class_ptr_type = f"{class_name}Ptr"
    
    if scope == "SINGLETON":
        return f"""        public: static {interface_ptr_type} GetInstance() {{
            static {interface_ptr_type} instance(new {class_name}());
            return instance;
        }}"""
    
    elif scope == "SINGLETON_VALIDATOR":
        if not validator_name:
            raise ValueError("Validator name required for SINGLETON_VALIDATOR scope")
        return f"""        public: friend class {validator_name}<{class_name}>;
        public:  static {interface_ptr_type} GetInstance() {{
            static {interface_ptr_type} instance(new {validator_name}<{class_name}>());
            return instance;
        }}"""
    
    elif scope == "PROTOTYPE":
        return f"""        public: static {interface_ptr_type} GetInstance() {{
            {interface_ptr_type} instance(new {class_name}());
            return instance;
        }}"""
    
    elif scope == "PROTOTYPE_VALIDATOR":
        if not validator_name:
            raise ValueError("Validator name required for PROTOTYPE_VALIDATOR scope")
        return f"""        public: friend class {validator_name}<{class_name}>;
        public: static {interface_ptr_type} GetInstance() {{
            {interface_ptr_type} instance(new {validator_name}<{class_name}>());
            return instance;
        }}"""
    
    else:
        raise ValueError(f"Unknown scope: {scope}")


def inject_instance_code(file_path: str, dry_run: bool = False) -> Dict[str, any]:
    """
    Inject instance code into a C++ file based on its scope and class information.
    
    Args:
        file_path: Path to the C++ file
        dry_run: If True, only show what would be injected without modifying the file
        
    Returns:
        Dictionary with results and any errors
    """
    results = {
        'success': False,
        'injected_code': '',
        'errors': [],
        'info': {}
    }
    
    try:
        # Step 1: Get the file scope
        scope = L2_get_file_scope.get_file_scope(file_path)
        results['info']['scope'] = scope
        # print(f"File scope: {scope}")
        
        # Step 2: Get class names
        class_names = find_class_names.find_class_names(file_path)
        if not class_names:
            results['errors'].append("No classes found in the file")
            return results
        
        class_name = class_names[0]  # Take the first class
        results['info']['class_name'] = class_name
        # print(f"Class name: {class_name}")
        
        # Step 3: Get interface names
        interface_names = find_interface_names.find_interface_names(file_path)
        if not interface_names:
            results['errors'].append("No interfaces found in the file")
            return results
        
        interface_name = interface_names[0]  # Take the first interface
        results['info']['interface_name'] = interface_name
        # print(f"Interface name: {interface_name}")
        
        # Step 4: Get validator name (if applicable)
        validator_name = None
        if scope.endswith('_VALIDATOR'):
            validator_name = L1_get_validator_name.get_validator_name(file_path)
            if not validator_name:
                results['errors'].append(f"Validator required for scope {scope} but none found")
                return results
            results['info']['validator_name'] = validator_name
            # print(f"Validator name: {validator_name}")
        
        # Step 5: Find the class closing brace
        closing_brace = find_class_closing_brace(file_path)
        if not closing_brace:
            results['errors'].append("Could not find class closing brace '};'")
            return results
        
        line_num, line_content = closing_brace
        results['info']['closing_brace_line'] = line_num
        # print(f"Class closing brace found at line {line_num}")
        
        # Step 6: Generate the instance code
        try:
            instance_code = generate_instance_code(scope, class_name, interface_name, validator_name)
            results['injected_code'] = instance_code
            # print(f"Generated instance code for scope {scope}")
        except ValueError as e:
            results['errors'].append(f"Error generating instance code: {e}")
            return results
        
        # Step 7: Inject the code (or show what would be injected)
        if dry_run:
            # print(f"\nWould inject the following code before line {line_num} (before '}};'):")
            # print("=" * 50)
            # print(instance_code)
            # print("=" * 50)
            results['success'] = True
        else:
            # Actually inject the code
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    lines = file.readlines()
                
                # Insert the instance code before the closing brace
                # Add proper indentation to match the class structure
                indentation = len(line_content) - len(line_content.lstrip())
                indented_code = '\n'.join(f"{' ' * indentation}{line}" for line in instance_code.split('\n'))
                
                # Insert the code before the closing brace line
                lines.insert(line_num - 1, f"{indented_code}\n")
                
                # Write back to file
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.writelines(lines)
                
                # print(f"Successfully injected instance code before line {line_num}")
                results['success'] = True
                
            except Exception as e:
                results['errors'].append(f"Failed to inject code: {e}")
                return results
        
    except Exception as e:
        results['errors'].append(f"Error processing file: {e}")
    
    return results


def inject_instance_code_in_files(file_paths: List[str], dry_run: bool = False) -> Dict[str, Dict[str, any]]:
    """
    Inject instance code into multiple C++ files.
    
    Args:
        file_paths: List of file paths to process
        dry_run: If True, only show what would be injected without modifying files
        
    Returns:
        Dictionary mapping file paths to results
    """
    all_results = {}
    
    for file_path in file_paths:
        # print(f"\nProcessing: {file_path}")
        results = inject_instance_code(file_path, dry_run)
        all_results[file_path] = results
        
        # Display results for this file
        if results['success']:
            if dry_run:
                # print("  Status: Would inject instance code successfully")
                pass
            else:
                # print("  Status: Instance code injected successfully")
                pass
        else:
            # print("  Status: Failed to inject instance code")
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
    """Main function to handle command line arguments and execute the injection process."""
    parser = argparse.ArgumentParser(
        description="Add instance code to C++ classes based on their scope"
    )
    parser.add_argument(
        "files", 
        nargs="+", 
        help="C++ source files to process (.cpp, .h, .hpp, etc.)"
    )
    parser.add_argument(
        "--dry-run", 
        action="store_true",
        help="Show what would be injected without modifying files"
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
    results = inject_instance_code_in_files(valid_files, args.dry_run)
    
    # Show summary if requested
    if args.summary:
        # print(f"\n=== Summary ===")
        # print(f"Files processed: {len(valid_files)}")
        # print(f"Files with successful injection: {len([r for r in results.values() if r['success']])}")
        # 
        # total_errors = sum(len(r['errors']) for r in results.values())
        # print(f"Total errors: {total_errors}")
        pass
    
    return results


# Export functions for other scripts to import
__all__ = [
    'find_class_closing_brace',
    'generate_instance_code',
    'inject_instance_code',
    'inject_instance_code_in_files',
    'main'
]


if __name__ == "__main__":
    # When run as script, execute main and store result
    result = main()
