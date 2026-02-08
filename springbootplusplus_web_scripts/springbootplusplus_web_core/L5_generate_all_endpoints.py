#!/usr/bin/env python3
"""
Script to generate all endpoint mappings by processing multiple controller files.
For each file with RestController macro:
1. Gets base URL
2. Gets endpoint details
3. Organizes endpoints by HTTP method
4. Generates function pointer code for each endpoint
5. Wraps everything in GenerateMappings() function
"""

import argparse
import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add springbootplusplus_web_core directory to path for imports (current directory)
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

try:
    import L1_check_rest_controller
    import L2_get_base_url
    import L3_get_endpoint_details
    import L4_generate_function_pointer
except ImportError as e:
    # print(f"Error: Could not import required modules: {e}")
    # print("Make sure L1_check_rest_controller.py, L2_get_base_url.py, L3_get_endpoint_details.py, and L4_generate_function_pointer.py are in the springbootplusplus_web_core directory.")
    sys.exit(1)


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


def process_file(file_path: str) -> Optional[List[Dict[str, Any]]]:
    """
    Process a single file to extract endpoint information.
    
    Args:
        file_path: Path to the C++ file
        
    Returns:
        List of endpoint dictionaries if RestController found, None otherwise
    """
    # Step 1: Check if RestController macro is present
    if not L1_check_rest_controller.check_rest_controller_macro_exists(file_path):
        return None
    
    # Step 2: Get base URL
    base_url = L2_get_base_url.get_base_url(file_path)
    
    # Step 3: Get endpoint details
    endpoint_details = L3_get_endpoint_details.get_endpoint_details(file_path, base_url)
    
    if not endpoint_details['success'] or not endpoint_details['endpoints']:
        return []
    
    # Return the endpoints with file path for reference
    endpoints = endpoint_details['endpoints']
    for endpoint in endpoints:
        endpoint['file_path'] = file_path
        endpoint['base_url'] = base_url
    
    return endpoints


def process_all_files(file_paths: List[str]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Process all files and organize endpoints by HTTP method.
    
    Args:
        file_paths: List of C++ file paths to process
        
    Returns:
        Dictionary mapping HTTP methods to lists of endpoints
    """
    # Maps to store endpoints by HTTP method
    endpoint_maps = {
        'GET': [],
        'POST': [],
        'PUT': [],
        'DELETE': [],
        'PATCH': []
    }
    
    processed_files = 0
    skipped_files = 0
    
    for file_path in file_paths:
        endpoints = process_file(file_path)
        
        if endpoints is None:
            skipped_files += 1
            continue
        
        if not endpoints:
            skipped_files += 1
            continue
        
        processed_files += 1
        
        # Organize endpoints by HTTP method
        for endpoint in endpoints:
            http_method = endpoint['http_method']
            if http_method in endpoint_maps:
                endpoint_maps[http_method].append(endpoint)
            else:
                # print(f"Warning: Unknown HTTP method '{http_method}' for endpoint in {file_path}")
                pass
    
    # print(f"\nProcessed {processed_files} file(s) with RestController")
    # print(f"Skipped {skipped_files} file(s) without RestController")
    
    return endpoint_maps


def generate_code_for_endpoint(endpoint: Dict[str, Any]) -> str:
    """
    Generate function pointer code for a single endpoint.
    Uses the advanced function signature parsing to handle RequestBody and PathVariable parameters.
    
    Args:
        endpoint: Endpoint dictionary with all details (from find_mapping_endpoints or get_endpoint_details)
        
    Returns:
        Generated code string
    """
    # Format the endpoint to the advanced structure
    formatted_endpoint = L3_get_endpoint_details.format_endpoint_with_advanced_signature(endpoint)
    
    # Generate code using the advanced function
    return L4_generate_function_pointer.generate_function_pointer_advanced(formatted_endpoint)


def generate_code_for_file(file_path: str) -> Optional[str]:
    """
    Generate endpoint mapping code for a single file.
    This is a convenience function that processes a single file and returns the generated code.
    
    Args:
        file_path: Path to the C++ file to process
        
    Returns:
        Generated code string for the file's endpoints, or None/empty string if no endpoints found
    """
    # Process the file to get endpoints
    endpoints = process_file(file_path)
    
    if endpoints is None or not endpoints:
        return None
    
    # Organize endpoints by HTTP method
    endpoint_maps = {
        'GET': [],
        'POST': [],
        'PUT': [],
        'DELETE': [],
        'PATCH': []
    }
    
    for endpoint in endpoints:
        http_method = endpoint['http_method']
        if http_method in endpoint_maps:
            endpoint_maps[http_method].append(endpoint)
    
    # Generate code for all endpoints
    code_lines = []
    
    # Generate code for each HTTP method
    for http_method in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
        method_endpoints = endpoint_maps.get(http_method, [])
        
        if not method_endpoints:
            continue
        
        # Add comment for this HTTP method
        code_lines.append(f"    // {http_method} endpoints")
        
        # Generate code for each endpoint
        for endpoint in method_endpoints:
            endpoint_code = generate_code_for_endpoint(endpoint)
            # Indent each line of the endpoint code
            indented_lines = ['    ' + line for line in endpoint_code.split('\n')]
            code_lines.extend(indented_lines)
            code_lines.append("")  # Add blank line between endpoints
        
        code_lines.append("")  # Add blank line between HTTP method sections
    
    if not code_lines:
        return None
    
    return '\n'.join(code_lines)


def generate_all_mappings_code(endpoint_maps: Dict[str, List[Dict[str, Any]]]) -> str:
    """
    Generate the complete GenerateMappings() function with all endpoint code.
    
    Args:
        endpoint_maps: Dictionary mapping HTTP methods to lists of endpoints
        
    Returns:
        Complete GenerateMappings() function code as string
    """
    code_lines = []
    code_lines.append("void GenerateMappings() {")
    code_lines.append("")
    
    # Generate code for each HTTP method
    for http_method in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
        endpoints = endpoint_maps.get(http_method, [])
        
        if not endpoints:
            continue
        
        # Add comment for this HTTP method
        code_lines.append(f"    // {http_method} endpoints")
        
        # Generate code for each endpoint
        for endpoint in endpoints:
            endpoint_code = generate_code_for_endpoint(endpoint)
            # Indent each line of the endpoint code
            indented_lines = ['    ' + line for line in endpoint_code.split('\n')]
            code_lines.extend(indented_lines)
            code_lines.append("")  # Add blank line between endpoints
        
        code_lines.append("")  # Add blank line between HTTP method sections
    
    code_lines.append("}")
    
    return '\n'.join(code_lines)


def main():
    """Main function to handle command line arguments and execute the endpoint generation."""
    parser = argparse.ArgumentParser(
        description="Generate all endpoint mappings by processing multiple controller files"
    )
    parser.add_argument(
        "files",
        nargs="+",
        help="C++ source files to process (.cpp, .h, .hpp, etc.)"
    )
    parser.add_argument(
        "--output",
        help="Output file to save the generated code (optional). If not provided, prints to stdout."
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
        return None
    
    # print(f"Processing {len(valid_files)} file(s)...")
    
    # Process all files and organize endpoints by HTTP method
    endpoint_maps = process_all_files(valid_files)
    
    # Count total endpoints
    total_endpoints = sum(len(endpoints) for endpoints in endpoint_maps.values())
    
    if total_endpoints == 0:
        # print("\nNo endpoints found in any files.")
        return None
    
    # print(f"\nFound {total_endpoints} endpoint(s) total:")
    # for http_method in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
    #     count = len(endpoint_maps.get(http_method, []))
    #     if count > 0:
    #         print(f"  {http_method}: {count}")
    
    # Generate the complete GenerateMappings() function
    # print("\nGenerating code...")
    generated_code = generate_all_mappings_code(endpoint_maps)
    
    # Output the generated code
    if args.output:
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(generated_code)
                f.write('\n')
            # print(f"\nGenerated code saved to: {args.output}")
        except Exception as e:
            # print(f"Error writing to file '{args.output}': {e}")
            # print("\nGenerated code:")
            # print("=" * 70)
            # print(generated_code)
            pass
    else:
        # print("\n" + "=" * 70)
        # print("Generated GenerateMappings() function:")
        # print("=" * 70)
        # print(generated_code)
        pass
    
    return generated_code


# Export functions for other scripts to import
__all__ = [
    'validate_cpp_file',
    'process_file',
    'process_all_files',
    'generate_code_for_endpoint',
    'generate_code_for_file',
    'generate_all_mappings_code',
    'main'
]


if __name__ == "__main__":
    # When run as script, execute main and store result
    result = main()
