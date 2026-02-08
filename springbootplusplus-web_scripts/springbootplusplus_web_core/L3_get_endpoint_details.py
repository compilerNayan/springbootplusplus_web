#!/usr/bin/env python3
"""
Script to extract endpoint details from HTTP mapping annotations inside C++ controller classes.
Finds @GetMapping, @PostMapping, @PutMapping, @DeleteMapping, and @PatchMapping annotations above functions 
inside the class, extracts function details, and combines with base URL to form complete endpoint URLs.
"""

import re
import argparse
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any


def find_class_and_interface(file_path: str) -> Optional[Dict[str, str]]:
    """
    Find class name and interface name from class declaration.
    Handles both 'class Xyz : public Interface' and 'class Xyz final : public Interface'.
    
    Args:
        file_path: Path to the C++ file
        
    Returns:
        Dictionary with 'class_name' and 'interface_name', or None if not found
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
    
    # Pattern to match class declarations with inheritance
    # Matches: class Xyz : public Interface or class Xyz final : public Interface
    class_pattern = r'class\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:final\s*)?:\s*public\s+([A-Za-z_][A-Za-z0-9_]*)'
    
    for line_num, line in enumerate(lines, 1):
        stripped_line = line.strip()
        
        # Skip commented lines
        if stripped_line.startswith('//') or stripped_line.startswith('/*') or stripped_line.startswith('*'):
            continue
        
        # Check for class declaration with inheritance
        match = re.search(class_pattern, stripped_line)
        if match:
            class_name = match.group(1)
            interface_name = match.group(2)
            return {
                'class_name': class_name,
                'interface_name': interface_name,
                'line_number': line_num
            }
    
    return None


def find_class_boundaries(file_path: str) -> Optional[Tuple[int, int]]:
    """
    Find the start and end line numbers of the class definition.
    
    Args:
        file_path: Path to the C++ file
        
    Returns:
        Tuple of (start_line, end_line) or None if not found
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
    except Exception as e:
        # print(f"Error reading file '{file_path}': {e}")
        return None
    
    class_start = None
    brace_count = 0
    
    # Pattern to match class declaration
    class_pattern = r'class\s+[A-Za-z_][A-Za-z0-9_]*\s*(?:.*?[:{]|[:{])'
    
    for line_num, line in enumerate(lines, 1):
        stripped_line = line.strip()
        
        # Allow annotations (/* @... */) to be present before the class, but skip other comments
        if stripped_line.startswith('/*') and not re.search(r'/\*\s*@\w+', stripped_line):
            continue
        if stripped_line.startswith('//'):
            continue
        
        # Check if this is the class declaration line
        if class_start is None:
            if re.search(class_pattern, stripped_line):
                class_start = line_num
                # Count opening brace on the same line
                brace_count += stripped_line.count('{')
                if brace_count > 0:
                    continue
        
        # If we're inside the class, count braces
        if class_start is not None:
            brace_count += stripped_line.count('{')
            brace_count -= stripped_line.count('}')
            
            # If braces are balanced and we've closed the class, we're done
            if brace_count == 0:
                return (class_start, line_num)
    
    return None


def parse_function_signature(line: str) -> Optional[Dict[str, str]]:
    """
    Parse a function signature to extract return type, function name, and first argument type.
    
    Args:
        line: Function signature line (e.g., "MyReturnDto myEndpoint(MyInputDto dto)")
        
    Returns:
        Dictionary with 'return_type', 'function_name', 'first_arg_type', or None if parsing fails
    """
    # Pattern to match function signature
    # Matches: ReturnType functionName(Type1 arg1, Type2 arg2, ...)
    # Handles optional override, const, etc.
    function_pattern = r'([A-Za-z_][A-Za-z0-9_<>*&:,\s]*?)\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(([^)]*)\)'
    
    match = re.search(function_pattern, line.strip())
    if not match:
        return None
    
    return_type = match.group(1).strip()
    function_name = match.group(2).strip()
    args_str = match.group(3).strip()
    
    # Extract first argument type
    first_arg_type = None
    if args_str:
        # Split by comma, but be careful with template types
        # Simple approach: take everything before the first comma or space after the type
        first_arg_match = re.match(r'([A-Za-z_][A-Za-z0-9_<>*&:,\s]*?)(?:\s+[A-Za-z_][A-Za-z0-9_]*)?(?:\s*,|\s*$)', args_str)
        if first_arg_match:
            first_arg_type = first_arg_match.group(1).strip()
        else:
            # If no match, try to extract the first word as type
            parts = args_str.split()
            if parts:
                first_arg_type = parts[0]
    
    return {
        'return_type': return_type,
        'function_name': function_name,
        'first_arg_type': first_arg_type or ""
    }


def parse_function_signature_advanced(line: str) -> Optional[Dict[str, Any]]:
    """
    Parse a function signature with Spring Boot-like annotations to extract return type, 
    function name, and all parameters with their annotations.
    
    Supports annotations like:
    - /* @RequestBody */ SomeInputDto inputDto
    - /* @PathVariable("xyz") */ StdString someXyz
    - /* @PathVariable("abc") */ const int abc
    
    Args:
        line: Function signature line (e.g., "Void SomeFun(/* @RequestBody */ SomeInputDto inputDto, /* @PathVariable("xyz") */ StdString someXyz)")
        
    Returns:
        Dictionary with 'return_type', 'function_name', and 'parameters' (list of parameter dicts),
        or None if parsing fails.
        Each parameter dict contains:
        - 'type': "RequestBody" or "PathVariable"
        - 'subType': Path variable name (e.g., "xyz") or empty string for RequestBody
        - 'class_name': Parameter type (e.g., "SomeInputDto", "StdString", "const int")
        - 'param_name': Parameter name (e.g., "inputDto", "someXyz")
    """
    # Pattern to match function signature
    # Matches: ReturnType functionName(...)
    # We need to find the opening parenthesis and then match everything until the matching closing parenthesis
    # This handles cases where there are parentheses inside annotations like @PathVariable("xyz")
    
    stripped_line = line.strip()
    
    # Find the function name pattern first
    function_name_pattern = r'([A-Za-z_][A-Za-z0-9_<>*&:,\s]*?)\s+([A-Za-z_][A-Za-z0-9_]*)\s*\('
    name_match = re.search(function_name_pattern, stripped_line)
    if not name_match:
        return None
    
    return_type = name_match.group(1).strip()
    function_name = name_match.group(2).strip()
    
    # Find the position of the opening parenthesis
    open_paren_pos = name_match.end() - 1  # Position of the '('
    
    # Now find the matching closing parenthesis, accounting for nested parentheses in annotations
    paren_depth = 0
    in_string = False
    string_char = None
    i = open_paren_pos
    
    while i < len(stripped_line):
        char = stripped_line[i]
        
        # Track string boundaries (for strings in annotations like "xyz")
        if char in ['"', "'"] and (i == 0 or stripped_line[i-1] != '\\'):
            if not in_string:
                in_string = True
                string_char = char
            elif char == string_char:
                in_string = False
                string_char = None
        
        # Track parentheses depth (only when not in string)
        if not in_string:
            if char == '(':
                paren_depth += 1
            elif char == ')':
                paren_depth -= 1
                if paren_depth == 0:
                    # Found matching closing parenthesis
                    args_str = stripped_line[open_paren_pos + 1:i].strip()
                    break
        i += 1
    else:
        # No matching closing parenthesis found
        return None
    
    parameters = []
    
    if args_str:
        # Split arguments by comma, but be careful with nested structures and annotations
        # We'll parse character by character to handle nested structures
        current_param = ""
        angle_bracket_depth = 0  # For template types like std::vector<int>
        paren_depth = 0  # For nested parentheses
        in_annotation = False  # Track if we're inside /* ... */ annotation
        
        i = 0
        while i < len(args_str):
            char = args_str[i]
            
            # Check for annotation boundaries (2-character sequences)
            if i < len(args_str) - 1:
                two_chars = args_str[i:i+2]
                
                # Check for start of annotation /* 
                if two_chars == '/*' and not in_annotation:
                    in_annotation = True
                    current_param += two_chars
                    i += 2
                    continue
                # Check for end of annotation */
                elif two_chars == '*/' and in_annotation:
                    in_annotation = False
                    current_param += two_chars
                    i += 2
                    continue
            
            # Track angle bracket depth (for template types like std::vector<int>)
            if char == '<':
                angle_bracket_depth += 1
                current_param += char
            elif char == '>':
                angle_bracket_depth -= 1
                current_param += char
            # Track parentheses depth (for nested function calls or complex expressions)
            elif char == '(':
                paren_depth += 1
                current_param += char
            elif char == ')':
                paren_depth -= 1
                current_param += char
            elif char == ',' and angle_bracket_depth == 0 and paren_depth == 0 and not in_annotation:
                # Found a parameter separator (comma outside of templates, parentheses, and annotations)
                param_str = current_param.strip()
                if param_str:
                    # Parse this parameter
                    param_info = _parse_single_parameter(param_str)
                    if param_info:
                        parameters.append(param_info)
                current_param = ""
            else:
                current_param += char
            
            i += 1
        
        # Don't forget the last parameter
        if current_param.strip():
            param_str = current_param.strip()
            param_info = _parse_single_parameter(param_str)
            if param_info:
                parameters.append(param_info)
    
    return {
        'return_type': return_type,
        'function_name': function_name,
        'parameters': parameters
    }


def _parse_single_parameter(param_str: str) -> Optional[Dict[str, str]]:
    """
    Parse a single parameter string with annotation.
    
    Args:
        param_str: Parameter string (e.g., "/* @RequestBody */ SomeInputDto inputDto" or "/* @RequestBody */ HelloRequestDto /* request */")
        
    Returns:
        Dictionary with 'type', 'subType', 'class_name', 'param_name', or None if parsing fails
    """
    # Pattern to match annotation: /* @RequestBody */ or /* @PathVariable("xyz") */
    annotation_pattern = re.compile(r'/\*\s*@(RequestBody|PathVariable)\s*(?:\(\s*["\']([^"\']+)["\']\s*\))?\s*\*/')
    
    # Find annotation
    annotation_match = annotation_pattern.search(param_str)
    
    param_type = None
    sub_type = ""
    
    if annotation_match:
        param_type = annotation_match.group(1)  # "RequestBody" or "PathVariable"
        if annotation_match.group(2):
            sub_type = annotation_match.group(2)  # Path variable name (e.g., "xyz")
        
        # Remove annotation from param_str
        param_str = annotation_pattern.sub('', param_str).strip()
    
    # If no annotation found, treat as RequestBody (backward compatibility)
    if not param_type:
        param_type = "RequestBody"
    
    # Remove inline comments (e.g., "/* request */" or "// request")
    # Pattern to match C-style comments /* ... */ and C++ style comments // ...
    comment_pattern = re.compile(r'/\*.*?\*/|//.*?$', re.MULTILINE)
    param_str = comment_pattern.sub('', param_str).strip()
    
    # Clean up trailing commas
    param_str = param_str.rstrip(',').strip()
    
    if not param_str:
        return None
    
    # Pattern to match parameter: TypeName paramName
    # Handles:
    # - Simple types: "int x"
    # - Const types: "const int x"
    # - Template types: "std::vector<int> x" or "Vector<SomeType> x"
    # - Complex types: "SomeInputDto x"
    # - Types with comments but no param name: "HelloRequestDto /* request */" -> just extract type
    # The parameter name is the last identifier (word that's not part of a template/type)
    
    # Find the last identifier that's not part of angle brackets
    # We'll work backwards from the end
    angle_bracket_depth = 0
    last_space_pos = -1
    
    # Find the position of the last space that's outside of angle brackets
    for i in range(len(param_str) - 1, -1, -1):
        char = param_str[i]
        if char == '>':
            angle_bracket_depth += 1
        elif char == '<':
            angle_bracket_depth -= 1
        elif char == ' ' and angle_bracket_depth == 0:
            last_space_pos = i
            break
    
    if last_space_pos == -1:
        # No space found - might be just a type name without parameter name
        # This can happen with commented parameters like "HelloRequestDto /* request */"
        # In this case, use the type name as both class_name and generate a dummy param_name
        class_name = param_str.strip()
        if not class_name:
            return None
        # Generate a parameter name from the type (remove namespace, take last part)
        param_name_parts = class_name.split('::')
        last_part = param_name_parts[-1].strip()
        # Remove template parameters if any
        if '<' in last_part:
            last_part = last_part[:last_part.index('<')].strip()
        # Convert to camelCase for parameter name (e.g., "HelloRequestDto" -> "helloRequestDto")
        if last_part:
            param_name = last_part[0].lower() + last_part[1:] if len(last_part) > 1 else last_part.lower()
        else:
            param_name = "param"
    else:
        # Split at the last space
        class_name = param_str[:last_space_pos].strip()
        param_name = param_str[last_space_pos + 1:].strip()
    
    # Clean up
    class_name = class_name.rstrip(',').strip()
    param_name = param_name.rstrip(',').strip()
    
    if not class_name:
        return None
    
    # If param_name is empty, generate one from class_name
    if not param_name:
        param_name_parts = class_name.split('::')
        last_part = param_name_parts[-1].strip()
        if '<' in last_part:
            last_part = last_part[:last_part.index('<')].strip()
        if last_part:
            param_name = last_part[0].lower() + last_part[1:] if len(last_part) > 1 else last_part.lower()
        else:
            param_name = "param"
    
    return {
        'type': param_type,
        'subType': sub_type,
        'class_name': class_name,
        'param_name': param_name
    }


def find_mapping_endpoints(file_path: str, base_url: str, class_name: str, interface_name: str) -> List[Dict[str, Any]]:
    """
    Find all HTTP mapping endpoints (GetMapping, PostMapping, PutMapping, DeleteMapping, PatchMapping) 
    inside the class and extract their details.
    
    Args:
        file_path: Path to the C++ file
        base_url: Base URL to concatenate with mapping paths
        class_name: Name of the class
        interface_name: Name of the interface
        
    Returns:
        List of dictionaries with endpoint details
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
    except Exception as e:
        return []
    
    # Find class boundaries
    boundaries = find_class_boundaries(file_path)
    if not boundaries:
        return []
    
    class_start, class_end = boundaries
    
    endpoints = []
    
    # Pattern to match any HTTP mapping annotation (search for /* @GetMapping("/path") */ or /*@GetMapping("/path")*/)
    # Also check for already processed /*--@GetMapping("/path")--*/ pattern
    # Note: [^"\']* allows empty strings (zero or more characters), not [^"\']+ (one or more)
    mapping_annotation_pattern = re.compile(r'/\*\s*@(GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping)\s*\(\s*["\']([^"\']*)["\']\s*\)\s*\*/')
    mapping_processed_pattern = re.compile(r'/\*--\s*@(GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping)\s*\(\s*["\'][^"\']*["\']\s*\)\s*--\*/')
    
    # Pattern to match legacy HTTP mapping macros (for backward compatibility)
    mapping_macro_pattern = re.compile(r'(GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping)\s*\(\s*["\']([^"\']*)["\']\s*\)')
    
    # Pattern to match function signature
    function_pattern = r'([A-Za-z_][A-Za-z0-9_<>*&:,\s]*?)\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(([^)]*)\)'
    
    # Scan inside the class (between class_start and class_end)
    i = class_start
    while i < class_end:
        line = lines[i - 1].strip()  # Convert to 0-indexed
        
        # Skip already processed annotations
        if mapping_processed_pattern.search(line):
            i += 1
            continue
        
        # Skip other comments that aren't HTTP mapping annotations
        # But allow /* @GetMapping("...") */ annotations to be processed
        if line.startswith('/*') and not mapping_annotation_pattern.search(line):
            i += 1
            continue
        # Skip single-line comments
        if line.startswith('//'):
            i += 1
            continue
        
        # Check for HTTP mapping annotation first (/* @GetMapping("/path") */)
        mapping_match = mapping_annotation_pattern.search(line)
        if mapping_match:
            http_method_annotation = mapping_match.group(1)  # e.g., "GetMapping", "PostMapping", etc.
            mapping_path = mapping_match.group(2)
        else:
            # Fallback: check for legacy mapping macro (for backward compatibility)
            mapping_match = mapping_macro_pattern.search(line)
            if mapping_match:
                http_method_annotation = mapping_match.group(1)
                mapping_path = mapping_match.group(2)
            else:
                i += 1
                continue
        
        # Extract HTTP method from annotation/macro name (GetMapping -> GET, PostMapping -> POST, etc.)
        http_method = http_method_annotation.replace('Mapping', '').upper()
        
        # Construct full endpoint URL
        # Ensure proper URL concatenation: base_url + mapping_path
        # Handle empty mapping_path (maps to base_url only)
        base_url_clean = base_url.rstrip('/')
        if not mapping_path:  # Empty string
            endpoint_url = base_url_clean
        else:
            # mapping_path is not empty
            if not mapping_path.startswith('/'):
                mapping_path = '/' + mapping_path
            endpoint_url = base_url_clean + mapping_path
        
        # Look ahead for function signature (within next few lines)
        # Function signatures can span multiple lines, so we need to collect lines until we find a complete signature
        function_found = False
        function_details = None
        
        # Collect lines for multi-line function signature
        function_lines = []
        function_start_line = None
        paren_depth = 0
        found_opening_paren = False
        
        for j in range(i + 1, min(i + 20, class_end + 1)):  # Increased range to handle multi-line signatures
            if j > len(lines):
                break
            
            next_line = lines[j - 1]  # Don't strip yet - we need to preserve structure
            
            # Skip already processed annotations
            if mapping_processed_pattern.search(next_line):
                continue
            
            # Skip other comments that aren't HTTP mapping annotations
            # But allow /* @GetMapping("...") */ annotations to be processed
            if next_line.strip().startswith('/*') and not mapping_annotation_pattern.search(next_line):
                # Check if it's a closing comment that might be part of parameter annotation
                if '*/' in next_line:
                    # Might be part of parameter annotation, include it
                    pass
                else:
                    continue
            # Skip single-line comments
            if next_line.strip().startswith('//'):
                continue
            
            # Check if this line might be part of a function signature
            # Look for return type pattern or opening parenthesis
            stripped_next = next_line.strip()
            
            # If we haven't started collecting, look for return type pattern
            if not function_lines:
                # Pattern to match return type and function name: ReturnType functionName(
                function_start_pattern = r'([A-Za-z_][A-Za-z0-9_<>*&:,\s]*?)\s+([A-Za-z_][A-Za-z0-9_]*)\s*\('
                if re.search(function_start_pattern, stripped_next):
                    function_start_line = j
                    function_lines.append(next_line.rstrip('\n'))
                    found_opening_paren = True
                    paren_depth = stripped_next.count('(') - stripped_next.count(')')
                    # If parentheses are balanced on this line, we have a single-line function
                    if paren_depth == 0:
                        # Single-line function signature
                        function_signature = ' '.join(function_lines)
                        func_details = parse_function_signature_advanced(function_signature)
                        if func_details:
                            function_found = True
                            function_details = func_details
                            break
                    continue
            
            # If we're collecting function lines, add this line
            if function_lines:
                function_lines.append(next_line.rstrip('\n'))
                # Update parenthesis depth
                paren_depth += stripped_next.count('(') - stripped_next.count(')')
                
                # If parentheses are balanced, we've found the complete function signature
                if paren_depth == 0:
                    # Join all lines to form complete function signature
                    function_signature = ' '.join(function_lines)
                    func_details = parse_function_signature_advanced(function_signature)
                    if func_details:
                        function_end_line = j
                        function_found = True
                        function_details = func_details
                        break
                    else:
                        # Failed to parse, reset and continue
                        function_lines = []
                        function_start_line = None
                        paren_depth = 0
                        found_opening_paren = False
                continue
            
            # If we haven't found a function start and this line doesn't look like one, skip it
            # But allow a few empty lines between annotation and function
            if not stripped_next:
                continue
            
            # If we've gone too far without finding a function, stop looking
            if j > i + 10 and not function_lines:
                break
        
        if function_found and function_details:
                # Handle both old format (first_arg_type) and new format (parameters)
                first_arg_type = ""
                if 'first_arg_type' in function_details:
                    # Old format
                    first_arg_type = function_details['first_arg_type']
                elif 'parameters' in function_details and function_details['parameters']:
                    # New format - get first RequestBody parameter, or first parameter if no RequestBody
                    for param in function_details['parameters']:
                        if param.get('type') == 'RequestBody':
                            first_arg_type = param.get('class_name', '')
                            break
                    if not first_arg_type and function_details['parameters']:
                        # No RequestBody found, use first parameter
                        first_arg_type = function_details['parameters'][0].get('class_name', '')
                
                endpoint_info = {
                    'endpoint_url': endpoint_url,
                    'http_method': http_method,
                    'mapping_annotation': http_method_annotation,
                    'mapping_path': mapping_path,
                    'function_name': function_details['function_name'],
                    'return_type': function_details['return_type'],
                    'first_arg_type': first_arg_type,
                    'parameters': function_details.get('parameters', []),  # Include full parameters list
                    'class_name': class_name,
                    'interface_name': interface_name,
                    'mapping_line': i,
                    'function_line': function_start_line if function_start_line else None
                }
                endpoints.append(endpoint_info)
        
        i += 1
    
    return endpoints


def get_endpoint_details(file_path: str, base_url: str) -> Dict[str, Any]:
    """
    Get all endpoint details from a C++ controller file.
    
    Args:
        file_path: Path to the C++ file
        base_url: Base URL to concatenate with GetMapping paths
        
    Returns:
        Dictionary with class info and endpoint details
    """
    # Step 1: Get class name and interface name
    class_info = find_class_and_interface(file_path)
    if not class_info:
        return {
            'success': False,
            'error': 'Could not find class and interface declaration',
            'endpoints': []
        }
    
    class_name = class_info['class_name']
    interface_name = class_info['interface_name']
    
    # Step 2: Find all HTTP mapping endpoints inside the class
    endpoints = find_mapping_endpoints(file_path, base_url, class_name, interface_name)
    
    return {
        'success': True,
        'class_name': class_name,
        'interface_name': interface_name,
        'base_url': base_url,
        'endpoints': endpoints
    }


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


def display_endpoint_details(result: Dict[str, Any]) -> None:
    """
    Display endpoint details in a formatted way.
    
    Args:
        result: Dictionary with endpoint details
    """
    if not result['success']:
        # print(f"Error: {result.get('error', 'Unknown error')}")
        return
    
    # print(f"\n{'='*70}")
    # print(f"Class: {result['class_name']}")
    # print(f"Interface: {result['interface_name']}")
    # print(f"Base URL: {result['base_url']}")
    # print(f"{'='*70}")
    
    if not result['endpoints']:
        # print("\nNo HTTP mapping endpoints found inside the class.")
        return
    
    # print(f"\nFound {len(result['endpoints'])} endpoint(s):\n")
    
    # for idx, endpoint in enumerate(result['endpoints'], 1):
    #     print(f"Endpoint {idx}:")
    #     print(f"  HTTP Method: {endpoint['http_method']}")
    #     print(f"  URL: {endpoint['endpoint_url']}")
    #     print(f"  Mapping Annotation: {endpoint.get('mapping_annotation', endpoint.get('mapping_macro', 'N/A'))}")
    #     print(f"  Mapping Path: {endpoint['mapping_path']}")
    #     print(f"  Function Name: {endpoint['function_name']}")
    #     print(f"  Return Type: {endpoint['return_type']}")
    #     print(f"  First Argument Type: {endpoint['first_arg_type'] if endpoint['first_arg_type'] else '(none)'}")
    #     print(f"  Class Name: {endpoint['class_name']}")
    #     print(f"  Interface Name: {endpoint['interface_name']}")
    #     if endpoint.get('mapping_line'):
    #         print(f"  Mapping at line: {endpoint['mapping_line']}")
    #     if endpoint.get('function_line'):
    #         print(f"  Function at line: {endpoint['function_line']}")
    #     print()


def main():
    """Main function to handle command line arguments and execute the endpoint extraction."""
    parser = argparse.ArgumentParser(
        description="Extract endpoint details from HTTP mapping macros (GetMapping, PostMapping, PutMapping, DeleteMapping, PatchMapping) inside C++ controller classes"
    )
    parser.add_argument(
        "file",
        help="C++ source file to analyze (.cpp, .h, .hpp, etc.)"
    )
    parser.add_argument(
        "--base-url",
        required=True,
        help="Base URL to concatenate with mapping paths (e.g., '/myUrl')"
    )
    
    args = parser.parse_args()
    
    # Validate file
    if not validate_cpp_file(args.file):
        # print(f"Error: '{args.file}' is not a valid C++ file")
        return None
    
    # Get endpoint details
    result = get_endpoint_details(args.file, args.base_url)
    
    # Display results
    display_endpoint_details(result)
    
    return result


def format_endpoint_with_advanced_signature(endpoint: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format endpoint information with advanced function signature parsing.
    Transforms endpoint dictionary to include controller interface, complete URL, 
    endpoint type, and full parameter details.
    
    Args:
        endpoint: Endpoint dictionary from find_mapping_endpoints() or get_endpoint_details()
        
    Returns:
        Dictionary with the following structure:
        {
            'controller_interface_name': str,  # e.g., "IMyController"
            'complete_url': str,               # e.g., "/myUrlTee/somePost2ee"
            'endpoint_type': str,              # "POST", "PUT", "GET", "DELETE", "PATCH"
            'return_type': str,                # e.g., "Void", "MyReturnDto", "int"
            'function_name': str,              # e.g., "SomeFun", "CreateUser"
            'parameters': List[Dict]           # List of parameter dictionaries (maintains order)
        }
    """
    # Extract or use existing parameters list
    parameters = endpoint.get('parameters', [])
    
    # If parameters list is empty but we have function details, try to parse from function signature
    if not parameters and 'function_signature' in endpoint:
        # This would require the full function signature string
        # For now, we'll rely on the parameters already being parsed
        pass
    
    return {
        'controller_interface_name': endpoint.get('interface_name', ''),
        'complete_url': endpoint.get('endpoint_url', ''),
        'endpoint_type': endpoint.get('http_method', ''),  # Already in uppercase (GET, POST, etc.)
        'return_type': endpoint.get('return_type', ''),
        'function_name': endpoint.get('function_name', ''),
        'parameters': parameters
    }


def get_endpoint_with_advanced_signature(
    file_path: str, 
    base_url: str
) -> List[Dict[str, Any]]:
    """
    Get all endpoint details with advanced function signature parsing.
    This is a convenience wrapper that combines get_endpoint_details() with 
    format_endpoint_with_advanced_signature().
    
    Args:
        file_path: Path to the C++ controller file
        base_url: Base URL to concatenate with mapping paths
        
    Returns:
        List of formatted endpoint dictionaries with the structure:
        {
            'controller_interface_name': str,
            'complete_url': str,
            'endpoint_type': str,
            'return_type': str,
            'function_name': str,
            'parameters': List[Dict]
        }
    """
    # Get endpoint details (this already uses parse_function_signature_advanced internally)
    endpoint_details = get_endpoint_details(file_path, base_url)
    
    if not endpoint_details['success']:
        return []
    
    # Format each endpoint
    formatted_endpoints = []
    for endpoint in endpoint_details['endpoints']:
        formatted = format_endpoint_with_advanced_signature(endpoint)
        formatted_endpoints.append(formatted)
    
    return formatted_endpoints


# Export functions for other scripts to import
__all__ = [
    'find_class_and_interface',
    'find_class_boundaries',
    'parse_function_signature',
    'parse_function_signature_advanced',
    '_parse_single_parameter',
    'find_mapping_endpoints',
    'get_endpoint_details',
    'format_endpoint_with_advanced_signature',
    'get_endpoint_with_advanced_signature',
    'display_endpoint_details',
    'main'
]


if __name__ == "__main__":
    # When run as script, execute main and store result
    result = main()
