#!/usr/bin/env python3
"""
Script to process @Autowired annotations in C++ files.

This script:
1. Gets the class name from the file
2. Finds @Autowired annotations (/* @Autowired */ or /*@Autowired*/) that are not processed
3. Parses @Autowired statements to extract variable type, object name, and base type
4. Replaces the variable declaration with GetInstance() call
5. Marks the @Autowired annotation as processed (/*--@Autowired--*/)
"""

import re
import argparse
import sys
from pathlib import Path

# Import our utility scripts
try:
    from find_class_names import get_class_names_from_file
except ImportError:
    # print("Error: Could not import find_class_names.py")
    sys.exit(1)


def find_autowired_macros(file_path):
    """
    Find all @Autowired annotations in the file that are not processed.
    
    Returns:
        list: List of tuples (line_number, line_content, match_info)
    """
    autowired_macros = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        # Pattern for @Autowired annotation (search for /* @Autowired */ or /*@Autowired*/)
        autowired_annotation_pattern = re.compile(r'/\*\s*@Autowired\s*\*/')
        autowired_processed_pattern = re.compile(r'/\*--\s*@Autowired\s*--\*/')
            
        for line_num, line in enumerate(lines, 1):
            stripped_line = line.strip()
            
            # Skip empty lines
            if not stripped_line:
                continue
            
            # Skip already processed annotations
            if autowired_processed_pattern.search(stripped_line):
                continue
                
            # Skip other comments that aren't @Autowired annotations
            # But allow /* @Autowired */ annotations to be processed
            if stripped_line.startswith('/*') and not autowired_annotation_pattern.search(stripped_line):
                continue
            # Skip single-line comments
            if stripped_line.startswith('//'):
                continue
                
            # Find @Autowired annotation
            autowired_match = autowired_annotation_pattern.search(stripped_line)
            if autowired_match:
                # Look at the next line for the variable declaration
                if line_num < len(lines):
                    next_line = lines[line_num].strip()
                    # Parse the next line for variable declaration
                    var_match = parse_variable_declaration(next_line)
                    if var_match:
                        autowired_macros.append({
                            'type': 'variable',
                            'line_number': line_num,
                            'line_content': line.rstrip(),
                            'next_line_number': line_num + 1,
                            'next_line_content': lines[line_num].rstrip(),
                            'variable_type': var_match['variable_type'],
                            'object_name': var_match['object_name'],
                            'variable_base_type': var_match['variable_base_type']
                        })
            
            # Check for legacy AUTOWIRED macro (for backward compatibility)
            if re.match(r'^\s*AUTOWIRED\s*$', stripped_line):
                if line_num < len(lines):
                    next_line = lines[line_num].strip()
                    var_match = parse_variable_declaration(next_line)
                    if var_match:
                        autowired_macros.append({
                            'type': 'variable',
                            'line_number': line_num,
                            'line_content': line.rstrip(),
                            'next_line_number': line_num + 1,
                            'next_line_content': lines[line_num].rstrip(),
                            'variable_type': var_match['variable_type'],
                            'object_name': var_match['object_name'],
                            'variable_base_type': var_match['variable_base_type']
                        })
                        
    except Exception as e:
        # print(f"Error reading file {file_path}: {e}")
        return []
        
    return autowired_macros


def find_autowired_constructor(file_path, class_name):
    """
    Find @Autowired constructor for the given class.
    
    Args:
        file_path (str): Path to the C++ file
        class_name (str): Name of the class to search for
        
    Returns:
        dict: Constructor info or None if not found
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        # Pattern for @Autowired annotation (search for /* @Autowired */ or /*@Autowired*/)
        autowired_annotation_pattern = re.compile(r'/\*\s*@Autowired\s*\*/')
        autowired_processed_pattern = re.compile(r'/\*--\s*@Autowired\s*--\*/')
            
        for line_num, line in enumerate(lines, 1):
            stripped_line = line.strip()
            
            # Skip empty lines
            if not stripped_line:
                continue
            
            # Skip already processed annotations
            if autowired_processed_pattern.search(stripped_line):
                continue
                
            # Skip other comments that aren't @Autowired annotations
            # But allow /* @Autowired */ annotations to be processed
            if stripped_line.startswith('/*') and not autowired_annotation_pattern.search(stripped_line):
                continue
            # Skip single-line comments
            if stripped_line.startswith('//'):
                continue
                
            # Find @Autowired annotation
            autowired_match = autowired_annotation_pattern.search(stripped_line)
            if autowired_match:
                # Look for constructor in the next few lines
                constructor_info = find_constructor_after_autowired(lines, line_num, class_name)
                if constructor_info:
                    # Return the @Autowired annotation line number, not the constructor line number
                    return {
                        'type': 'constructor',
                        'line_number': line_num,  # This is the @Autowired annotation line
                        'line_content': line.rstrip(),
                        'constructor_info': constructor_info
                    }
            
            # Check for legacy AUTOWIRED macro (for backward compatibility)
            if re.match(r'^\s*AUTOWIRED\s*$', stripped_line):
                constructor_info = find_constructor_after_autowired(lines, line_num, class_name)
                if constructor_info:
                    return {
                        'type': 'constructor',
                        'line_number': line_num,
                        'line_content': line.rstrip(),
                        'constructor_info': constructor_info
                    }
                    
    except Exception as e:
        # print(f"Error reading file {file_path}: {e}")
        return None
        
    return None


def find_constructor_after_autowired(lines, autowired_line, class_name):
    """
    Find constructor after @Autowired annotation.
    
    Args:
        lines (list): All lines in the file
        autowired_line (int): Line number of @Autowired annotation
        class_name (str): Expected class name for constructor
        
    Returns:
        dict: Constructor information or None
    """
    # Look in the next 10 lines for constructor start (more restrictive)
    start_line = autowired_line
    end_line = min(autowired_line + 10, len(lines))
    
    # Updated pattern to handle C++ keywords like 'explicit', 'virtual', 'inline', etc.
    constructor_start_pattern = rf'^\s*(?:[A-Za-z_][A-Za-z0-9_]*\s+)*{re.escape(class_name)}\s*\('
    
    for line_num in range(start_line, end_line):
        if line_num >= len(lines):
            break
            
        line = lines[line_num].strip()
        if not line:
            continue
            
        # Check if this is the start of the constructor
        if re.match(constructor_start_pattern, line):
            # Found constructor start, now collect all lines until it's complete
            constructor_lines = []
            current_line_num = line_num
            paren_count = 0
            constructor_complete = False
            
            while current_line_num < len(lines) and not constructor_complete:
                current_line = lines[current_line_num]
                constructor_lines.append(current_line)
                
                # Count parentheses to find when constructor ends
                for char in current_line:
                    if char == '(':
                        paren_count += 1
                    elif char == ')':
                        paren_count -= 1
                        if paren_count == 0:
                            # Found closing parenthesis, check if constructor is complete
                            if '{' in current_line or ':' in current_line:
                                constructor_complete = True
                            break
                
                current_line_num += 1
                
                # Safety check - don't go too far
                if current_line_num > line_num + 15:
                    break
            
            if constructor_complete:
                # Join all lines and parse
                full_constructor = ''.join(constructor_lines).strip()
                params = extract_constructor_parameters(full_constructor, class_name)
                
                # Only return if we found valid parameters (this is a constructor AUTOWIRED)
                if params:
                    return {
                        'line_number': line_num + 1,  # Convert to 1-based
                        'line_content': full_constructor,
                        'parameters': params,
                        'start_line': line_num + 1,
                        'end_line': current_line_num
                    }
    
    return None


def extract_constructor_parameters(full_constructor, class_name):
    """
    Extract parameters from a full constructor string (can be multiline).
    
    Args:
        full_constructor (str): Full constructor string
        class_name (str): Class name
        
    Returns:
        list: List of parameter info dictionaries
    """
    # Find the parameters section between parentheses
    pattern = rf'{re.escape(class_name)}\s*\(([^)]*)\)'
    match = re.search(pattern, full_constructor)
    
    if not match:
        return []
    
    params_str = match.group(1).strip()
    if not params_str:
        return []
    
    # Parse parameters (handle multiline)
    params = parse_constructor_parameters(params_str)
    return params


def parse_constructor_parameters(params_str):
    """
    Parse constructor parameters string.
    
    Args:
        params_str (str): Parameters string like "XyzPtr obj1, AbcPtr obj2" or with default values
        
    Returns:
        list: List of parameter info dictionaries
    """
    params = []
    
    # Split by comma and handle multiline
    param_parts = [p.strip() for p in params_str.split(',')]
    
    for part in param_parts:
        if not part:
            continue
            
        # Pattern to match: TypePtr varName [= default_value]
        # Handle both with and without default values
        param_match = re.match(r'^\s*([A-Za-z_][A-Za-z0-9_]*Ptr)\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:=.*)?$', part)
        if param_match:
            param_type = param_match.group(1)  # e.g., "XyzPtr"
            param_name = param_match.group(2)  # e.g., "obj1"
            base_type = param_type[:-3]  # Remove "Ptr"
            
            params.append({
                'type': param_type,
                'name': param_name,
                'base_type': base_type
            })
    
    return params


def parse_variable_declaration(line):
    """
    Parse a variable declaration line to extract type, name, and base type.
    
    Expected format: ClassNamePtr obj;
    
    Returns:
        dict: Parsed information or None if parsing fails
    """
    # Pattern to match: [Multiple Modifiers] ClassNamePtr obj;
    # Must end with Ptr and have a variable name
    # Modifiers can be Private, Public, Protected, Static, etc.
    pattern = r'^\s*(?:[A-Za-z_][A-Za-z0-9_]*\s+)*([A-Za-z_][A-Za-z0-9_]*Ptr)\s+([A-Za-z_][A-Za-z0-9_]*)\s*;\s*$'
    
    match = re.match(pattern, line)
    if not match:
        return None
        
    variable_type = match.group(1)  # e.g., "ClassNamePtr"
    object_name = match.group(2)    # e.g., "obj"
    
    # Extract base type by removing "Ptr" suffix
    if variable_type.endswith('Ptr'):
        variable_base_type = variable_type[:-3]  # Remove "Ptr"
    else:
        return None  # Must end with Ptr
        
    return {
        'variable_type': variable_type,
        'object_name': object_name,
        'variable_base_type': variable_base_type
    }


def process_autowired_macros(file_path, dry_run=False):
    """
    Process all AUTOWIRED macros in the file.
    
    Args:
        file_path (str): Path to the C++ file
        dry_run (bool): If True, show what would be changed without making changes
        
    Returns:
        dict: Processing results
    """
    # print(f"Processing: {file_path}")
    
    # Get class name (optional - only needed for constructor @Autowired)
    class_name = None
    try:
        class_names = get_class_names_from_file(file_path)
        if class_names:
            class_name = class_names[0]  # Use the first class name
            # print(f"  Class name: {class_name}")
        else:
            # print("  ℹ️  No class names found in file (this is OK for simple @Autowired variables)")
            pass
    except Exception as e:
        # print(f"  ℹ️  Could not get class name: {e} (this is OK for simple @Autowired variables)")
        pass
    
    # Find @Autowired variable annotations (these don't need class names)
    autowired_macros = find_autowired_macros(file_path)
    
    # Find @Autowired constructor (this needs class name)
    autowired_constructor = None
    if class_name:
        autowired_constructor = find_autowired_constructor(file_path, class_name)
    else:
        # print("  ℹ️  Skipping constructor @Autowired check (no class name available)")
        pass
    
    total_autowired = len(autowired_macros) + (1 if autowired_constructor else 0)
    
    if total_autowired == 0:
        # print("  ℹ️  No @Autowired annotations found")
        return {'success': True, 'autowired_count': 0, 'message': 'No @Autowired annotations found'}
    
    # print(f"  Found {len(autowired_macros)} @Autowired variable annotation(s)")
    if autowired_constructor:
        # print(f"  Found 1 @Autowired constructor annotation")
        pass
    
    # Log whether we're processing with or without class name
    if class_name:
        # print(f"  ℹ️  Processing with class name: {class_name}")
        pass
    else:
        # print(f"  ℹ️  Processing simple AUTOWIRED variables (no class name required)")
        pass
    
    if dry_run:
        # print("  🔍 DRY RUN - No changes will be made")
        pass
    
    # Process AUTOWIRED variable macros
    processed_count = 0
    errors = []
    all_changes = []
    
    for macro_info in autowired_macros:
        try:
            # print(f"  Processing AUTOWIRED variable at line {macro_info['line_number']}:")
            # print(f"    Variable type: {macro_info['variable_type']}")
            # print(f"    Object name: {macro_info['object_name']}")
            # print(f"    Base type: {macro_info['variable_base_type']}")
            
            # Generate replacement code
            replacement_code = (macro_info['variable_type'] + " " + macro_info['object_name'] + 
                              " = Implementation<" + macro_info['variable_base_type'] + ">::type::GetInstance();")
            
            # Store the replacement code for later use
            macro_info['replacement_code'] = replacement_code
            
            # print(f"    Would replace: {macro_info['next_line_content']}")
            # print(f"    With: {replacement_code}")
            # print(f"    Would comment: {macro_info['line_content']}")
            
            if not dry_run:
                # Collect changes for later application
                all_changes.append(macro_info)
                processed_count += 1
                # print(f"    ✅ Would process successfully")
            else:
                processed_count += 1
                # print(f"    ✅ Would process successfully")
                
        except Exception as e:
            error_msg = f"Error processing AUTOWIRED variable at line {macro_info['line_number']}: {e}"
            errors.append(error_msg)
            # print(f"    ❌ {error_msg}")
    
    # Process AUTOWIRED constructor
    if autowired_constructor:
        try:
            constructor_info = autowired_constructor['constructor_info']
            # print(f"  Processing AUTOWIRED constructor at line {autowired_constructor['line_number']}:")
            # print(f"    Constructor: {constructor_info['line_content']}")
            
            if constructor_info['parameters']:
                # print("    Parameters to expand:")
                # for param in constructor_info['parameters']:
                #     print("      " + param['type'] + " " + param['name'] + " -> Implementation<" + param['base_type'] + ">::type::GetInstance()")
                
                # Store constructor info for line-by-line processing
                autowired_constructor['constructor_info'] = constructor_info
                
                # print(f"    Would replace: {constructor_info['line_content']}")
                # print(f"    With: [Line-by-line replacement preserving structure]")
                # print(f"    Would comment: {autowired_constructor['line_content']}")
                
                if not dry_run:
                    all_changes.append(autowired_constructor)
                    processed_count += 1
                    # print(f"    ✅ Would process successfully")
                else:
                    processed_count += 1
                    # print(f"    ✅ Would process successfully")
            else:
                # print(f"    No parameters to expand")
                pass
                
        except Exception as e:
            error_msg = f"Error processing AUTOWIRED constructor at line {autowired_constructor['line_number']}: {e}"
            errors.append(error_msg)
            # print(f"    ❌ {error_msg}")
    
    # Apply all changes at once if not in dry run
    if not dry_run and all_changes:
        # print(f"  🔧 Applying all {len(all_changes)} changes...")
        success = apply_all_autowired_changes(file_path, all_changes)
        if not success:
            errors.append("Failed to apply changes to file")
            # print(f"  ❌ Failed to apply changes to file")
        else:
            # print(f"  ✅ Successfully applied all changes to file")
            pass
    
    # Summary
    if processed_count > 0:
        # print(f"  📊 Summary: {processed_count} @Autowired annotation(s) processed")
        pass
    if errors:
        # print(f"  ⚠️  Errors: {len(errors)}")
        # for error in errors:
        #     print(f"    - {error}")
        pass
    
    # Success if we processed at least one macro or if there were no macros to process
    success = len(errors) == 0 and (processed_count > 0 or total_autowired == 0)
    
    return {
        'success': success,
        'autowired_count': len(autowired_macros),
        'processed_count': processed_count,
        'errors': errors
    }


def apply_autowired_changes(file_path, macro_info, replacement_code):
    """
    Apply the AUTOWIRED changes to the file.
    
    Args:
        file_path (str): Path to the file
        macro_info (dict): Information about the AUTOWIRED macro
        replacement_code (str): The replacement code for the variable declaration
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        # Comment out the AUTOWIRED macro
        autowired_line = macro_info['line_number'] - 1  # Convert to 0-based index
        lines[autowired_line] = f"// {lines[autowired_line].rstrip()}\n"
        
        # Replace the variable declaration
        var_line = macro_info['next_line_number'] - 1  # Convert to 0-based index
        lines[var_line] = f"{replacement_code}\n"
        
        # Write back to file
        with open(file_path, 'w', encoding='utf-8') as file:
            file.writelines(lines)
            
        return True
        
    except Exception as e:
        # print(f"    Error applying changes: {e}")
        return False


def generate_constructor_replacement(constructor_info):
    """
    Generate replacement constructor with expanded parameters.
    
    Args:
        constructor_info (dict): Constructor information
        
    Returns:
        list: List of replacement lines (preserves exact line structure)
    """
    # Get the original lines from the constructor info
    start_line = constructor_info['start_line'] - 1  # Convert to 0-based
    end_line = constructor_info['end_line']
    
    # We need to read the file to get the original lines
    # This will be handled in the apply function
    
    # For now, return the constructor info for line-by-line processing
    return constructor_info


def generate_line_by_line_replacement(constructor_info, original_lines):
    """
    Generate replacement constructor line by line, preserving exact structure.
    
    Args:
        constructor_info (dict): Constructor information
        original_lines (list): Original file lines
        
    Returns:
        list: List of replacement lines
    """
    start_line = constructor_info['start_line'] - 1  # Convert to 0-based
    end_line = constructor_info['end_line']
    
    # Get the original constructor lines
    constructor_lines = original_lines[start_line:end_line]
    
    # Simple approach: replace each parameter type+name with type+name+default_value
    # and preserve the original line structure
    new_lines = []
    
    for line in constructor_lines:
        new_line = line
        
        # Replace each parameter in this line
        for param in constructor_info['parameters']:
            old_param = f"{param['type']} {param['name']}"
            new_param = f"{param['type']} {param['name']} = Implementation<{param['base_type']}>::type::GetInstance()"
            
            # Only replace if this line contains the parameter
            if old_param in line:
                new_line = new_line.replace(old_param, new_param)
        
        new_lines.append(new_line)
    
    return new_lines


def apply_all_autowired_changes(file_path, all_macros):
    """
    Apply all AUTOWIRED changes to the file at once.
    
    Args:
        file_path (str): Path to the file
        all_macros (list): List of all macro_info dictionaries
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        # Sort macros by line number in descending order to avoid line number shifting
        sorted_macros = sorted(all_macros, key=lambda x: x['line_number'], reverse=True)
        
        for macro_info in sorted_macros:
            # Mark @Autowired annotation as processed or comment out legacy AUTOWIRED macro
            autowired_line = macro_info['line_number'] - 1  # Convert to 0-based index
            original_line = lines[autowired_line]
            stripped_original = original_line.strip()
            
            # Check if it's an annotation or legacy macro
            autowired_annotation_pattern = re.compile(r'/\*\s*@Autowired\s*\*/')
            if autowired_annotation_pattern.search(stripped_original):
                # Mark annotation as processed: /* @Autowired */ → /*--@Autowired--*/
                indent = len(original_line) - len(original_line.lstrip())
                indent_str = original_line[:indent]
                lines[autowired_line] = f"{indent_str}/*--@Autowired--*/\n"
            else:
                # Legacy macro: comment it out
                lines[autowired_line] = f"// {original_line.rstrip()}\n"
            
            if macro_info['type'] == 'variable':
                # Replace the variable declaration
                var_line = macro_info['next_line_number'] - 1  # Convert to 0-based index
                lines[var_line] = f"{macro_info['replacement_code']}\n"
            elif macro_info['type'] == 'constructor':
                # Replace the constructor line by line to preserve exact structure
                start_line = macro_info['constructor_info']['start_line'] - 1  # Convert to 0-based index
                end_line = macro_info['constructor_info']['end_line']  # Already 0-based
                
                # Generate line-by-line replacement
                replacement_lines = generate_line_by_line_replacement(macro_info['constructor_info'], lines)
                
                # Replace the lines one by one
                for i, replacement_line in enumerate(replacement_lines):
                    if start_line + i < len(lines):
                        lines[start_line + i] = replacement_line
        
        # Write back to file
        with open(file_path, 'w', encoding='utf-8') as file:
            file.writelines(lines)
            
        return True
        
    except Exception as e:
        # print(f"    Error applying all changes: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Process @Autowired annotations in C++ files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python process_autowired.py file.h                    # Process file
  python process_autowired.py file.h --dry-run          # Show what would change
  python process_autowired.py *.h                       # Process multiple files
        """
    )
    
    parser.add_argument(
        "files",
        nargs="+",
        help="C++ files to process"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without making changes"
    )
    
    args = parser.parse_args()
    
    # Process each file
    all_results = {}
    
    for file_path in args.files:
        if not Path(file_path).exists():
            # print(f"❌ File not found: {file_path}")
            all_results[file_path] = {'success': False, 'errors': ['File not found']}
            continue
            
        result = process_autowired_macros(file_path, args.dry_run)
        all_results[file_path] = result
        # print()  # Add spacing between files
    
    # Summary
    if len(args.files) > 1:
        # print("=" * 60)
        # print("SUMMARY")
        # print("=" * 60)
        # 
        # total_files = len(args.files)
        # successful_files = sum(1 for r in all_results.values() if r['success'])
        # total_autowired = sum(r.get('autowired_count', 0) for r in all_results.values())
        # total_processed = sum(r.get('processed_count', 0) for r in all_results.values())
        # 
        # print(f"Files processed: {total_files}")
        # print(f"Files successful: {successful_files}")
        # print(f"Total AUTOWIRED macros found: {total_autowired}")
        # print(f"Total AUTOWIRED macros processed: {total_processed}")
        # 
        # if args.dry_run:
        #     print("🔍 This was a dry run - no changes were made")
        # else:
        #     print("✅ Changes applied successfully")
        pass


if __name__ == "__main__":
    main()
