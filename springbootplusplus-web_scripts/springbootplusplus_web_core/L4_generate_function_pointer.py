#!/usr/bin/env python3
"""
Script to generate function pointer code for HTTP mapping endpoints.
Takes endpoint details as command-line parameters and generates the appropriate
function pointer template based on the HTTP method (GET, POST, PUT, DELETE, PATCH).
"""

import argparse
from typing import Dict, Optional, List, Any, Tuple


def get_mapping_variable_name(http_method: str) -> str:
    """
    Get the mapping variable name based on HTTP method.
    
    Args:
        http_method: HTTP method (GET, POST, PUT, DELETE, PATCH)
        
    Returns:
        Mapping variable name (e.g., "getMappings", "postMappings", etc.)
    """
    method_lower = http_method.lower()
    return f"{method_lower}Mappings"


def parse_response_entity_type(return_type: str) -> Tuple[bool, Optional[str]]:
    """
    Parse return type to check if it's ResponseEntity<T> and extract the entity type.
    
    Args:
        return_type: Return type string (e.g., "ResponseEntity<StdString>", "ResponseEntity<Int>", "int")
        
    Returns:
        Tuple of (is_response_entity, entity_type)
        - is_response_entity: True if return type is ResponseEntity<T>, False otherwise
        - entity_type: The entity type T if it's ResponseEntity<T>, None otherwise
    """
    cleaned = return_type.strip()
    
    # Check if it starts with "ResponseEntity<" (case-insensitive)
    if not cleaned.lower().startswith("responseentity<"):
        return (False, None)
    
    # Find the opening and closing angle brackets
    start_idx = cleaned.find('<')
    if start_idx == -1:
        return (False, None)
    
    # Find matching closing bracket
    bracket_count = 0
    end_idx = -1
    for i in range(start_idx, len(cleaned)):
        if cleaned[i] == '<':
            bracket_count += 1
        elif cleaned[i] == '>':
            bracket_count -= 1
            if bracket_count == 0:
                end_idx = i
                break
    
    if end_idx == -1:
        return (False, None)
    
    # Extract the entity type (everything between < and >)
    entity_type = cleaned[start_idx + 1:end_idx].strip()
    
    # Remove any C++ keywords from the entity type
    keywords_to_remove = ['public', 'private', 'protected', 'virtual', 'static', 'const', 'override']
    words = entity_type.split()
    actual_type_words = [w for w in words if w.lower() not in keywords_to_remove]
    entity_type = ' '.join(actual_type_words).strip()
    
    return (True, entity_type)


def generate_function_pointer(
    url: str,
    http_method: str,
    function_name: str,
    return_type: str,
    first_arg_type: str,
    interface_name: str
) -> str:
    """
    Generate function pointer code for an HTTP mapping endpoint.
    
    Args:
        url: Endpoint URL as string (e.g., "/myUrl/mysomeget")
        http_method: HTTP method (GET, POST, PUT, DELETE, PATCH)
        function_name: Function name (e.g., "myFun")
        return_type: Return type (e.g., "int", "MyReturnDto")
        first_arg_type: First argument type (e.g., "TestDto", "MyInputDto")
        interface_name: Interface name (e.g., "ITestController")
        
    Returns:
        Generated function pointer code as string
    """
    # Get the mapping variable name based on HTTP method
    mapping_var = get_mapping_variable_name(http_method)
    
    # Clean return type: remove common C++ keywords (Public, Private, Protected, Virtual, etc.)
    # and extract just the actual type
    cleaned_return_type = return_type.strip()
    # Remove common keywords that might appear before the actual type
    keywords_to_remove = ['public', 'private', 'protected', 'virtual', 'static', 'const', 'override']
    words = cleaned_return_type.split()
    # Filter out keywords and keep only the actual type
    actual_type_words = [w for w in words if w.lower() not in keywords_to_remove]
    cleaned_return_type = ' '.join(actual_type_words).strip()
    
    # Check if return type is void or Void (case-insensitive)
    is_void = cleaned_return_type.lower() == "void"
    
    # Check if return type is ResponseEntity<T>
    is_response_entity, entity_type = parse_response_entity_type(cleaned_return_type)
    
    # Generate the function pointer code
    # Return type is now IHttpResponsePtr instead of StdString
    code = f"{mapping_var}[\"{url}\"] = [](CStdString arg) -> IHttpResponsePtr {{\n"
    code += "//                 AUTOWIRED\n"
    code += f"    {interface_name}Ptr controller = Implementation<{interface_name}>::type::GetInstance();\n"
    
    if is_void:
        # For void return types, call controller method and return CreateOkResponse() (no body)
        if first_arg_type and first_arg_type.lower() not in ["", "none", "(none)"]:
            code += f"    controller->{function_name}(nayan::serializer::SerializationUtility::Deserialize<{first_arg_type}>(arg));\n"
        else:
            code += f"    controller->{function_name}();\n"
        code += "    return ResponseEntityConverter::CreateOkResponse();\n"
    elif is_response_entity:
        # For ResponseEntity<T> return types, store return value and use ToHttpResponse<EntityType>(returnValue)
        # Handle case where there's no argument (first_arg_type is empty or "none")
        if first_arg_type and first_arg_type.lower() not in ["", "none", "(none)"]:
            code += f"    {cleaned_return_type} returnValue = controller->{function_name}(nayan::serializer::SerializationUtility::Deserialize<{first_arg_type}>(arg));\n"
        else:
            code += f"    {cleaned_return_type} returnValue = controller->{function_name}();\n"
        code += f"    return ResponseEntityConverter::ToHttpResponse<{entity_type}>(returnValue);\n"
    else:
        # For non-void, non-ResponseEntity return types, store return value and use CreateOkResponse<T>(returnValue)
        # Handle case where there's no argument (first_arg_type is empty or "none")
        if first_arg_type and first_arg_type.lower() not in ["", "none", "(none)"]:
            code += f"    {cleaned_return_type} returnValue = controller->{function_name}(nayan::serializer::SerializationUtility::Deserialize<{first_arg_type}>(arg));\n"
        else:
            code += f"    {cleaned_return_type} returnValue = controller->{function_name}();\n"
        
        code += f"    return ResponseEntityConverter::CreateOkResponse<{cleaned_return_type}>(returnValue);\n"
    
    code += "};"
    
    return code


def generate_function_pointer_advanced(formatted_endpoint: Dict[str, Any]) -> str:
    """
    Generate function pointer code for an HTTP mapping endpoint using advanced parameter parsing.
    
    This function generates code that handles:
    - RequestBody parameters (deserialized from payload)
    - PathVariable parameters (extracted from variables map using ConvertToType)
    - Void and non-void return types
    
    Args:
        formatted_endpoint: Dictionary with the structure from format_endpoint_with_advanced_signature():
            {
                'controller_interface_name': str,  # e.g., "IMyController"
                'complete_url': str,               # e.g., "/myUrlTee/somePost2ee"
                'endpoint_type': str,              # "POST", "PUT", "GET", "DELETE", "PATCH"
                'return_type': str,                # e.g., "Void", "MyReturnDto", "int"
                'function_name': str,              # e.g., "SomeFun", "CreateUser"
                'parameters': List[Dict]           # List of parameter dictionaries
            }
    
    Returns:
        Generated function pointer code as string
    """
    # Extract endpoint information
    controller_interface = formatted_endpoint.get('controller_interface_name', '')
    complete_url = formatted_endpoint.get('complete_url', '')
    endpoint_type = formatted_endpoint.get('endpoint_type', '').upper()  # Ensure uppercase
    return_type = formatted_endpoint.get('return_type', '')
    function_name = formatted_endpoint.get('function_name', '')
    parameters = formatted_endpoint.get('parameters', [])
    
    # Get the mapping variable name based on HTTP method
    mapping_var = get_mapping_variable_name(endpoint_type)
    
    # Clean return type: remove common C++ keywords
    cleaned_return_type = return_type.strip()
    keywords_to_remove = ['public', 'private', 'protected', 'virtual', 'static', 'const', 'override']
    words = cleaned_return_type.split()
    actual_type_words = [w for w in words if w.lower() not in keywords_to_remove]
    cleaned_return_type = ' '.join(actual_type_words).strip()
    
    # Check if return type is void or Void (case-insensitive)
    is_void = cleaned_return_type.lower() == "void"
    
    # Check if return type is ResponseEntity<T>
    is_response_entity, entity_type = parse_response_entity_type(cleaned_return_type)
    
    # Check which parameters are used
    has_request_body = False
    has_path_variable = False
    
    for param in parameters:
        param_type = param.get('type', '')
        if param_type == 'RequestBody':
            has_request_body = True
        elif param_type == 'PathVariable':
            has_path_variable = True
        else:
            # Fallback: treat as RequestBody
            has_request_body = True
    
    # Generate lambda signature with commented unused parameters
    # Return type is now IHttpResponsePtr instead of StdString
    if has_request_body and has_path_variable:
        # Both are used
        lambda_signature = "[](CStdString payload, Map<StdString, StdString> variables) -> IHttpResponsePtr"
    elif has_request_body and not has_path_variable:
        # Only payload is used
        lambda_signature = "[](CStdString payload, Map<StdString, StdString> /*variables*/) -> IHttpResponsePtr"
    elif not has_request_body and has_path_variable:
        # Only variables is used
        lambda_signature = "[](CStdString /*payload*/, Map<StdString, StdString> variables) -> IHttpResponsePtr"
    else:
        # Neither is used (no parameters)
        lambda_signature = "[](CStdString /*payload*/, Map<StdString, StdString> /*variables*/) -> IHttpResponsePtr"
    
    # Generate the function pointer code
    code = f"{mapping_var}[\"{complete_url}\"] = {lambda_signature} {{\n"
    code += "//                 AUTOWIRED\n"
    code += f"    {controller_interface}Ptr controller = Implementation<{controller_interface}>::type::GetInstance();\n"
    
    # Build function call arguments
    function_args = []
    
    for param in parameters:
        param_type = param.get('type', '')
        param_class_name = param.get('class_name', '')
        param_sub_type = param.get('subType', '')  # Path variable name for PathVariable
        
        if param_type == 'RequestBody':
            # Deserialize from payload
            function_args.append(f"nayan::serializer::SerializationUtility::Deserialize<{param_class_name}>(payload)")
        elif param_type == 'PathVariable':
            # Extract from variables map and convert to type
            # Strip 'const' and other qualifiers for ConvertToType template parameter
            # ConvertToType needs the base type, not const-qualified
            type_for_conversion = param_class_name.strip()
            # Remove 'const' keyword if present
            if type_for_conversion.startswith('const '):
                type_for_conversion = type_for_conversion[6:].strip()
            # Use ConvertToType to convert the string value to the appropriate type
            # Qualify with class name since it's a member function template
            function_args.append(f"HttpRequestDispatcher::ConvertToType<{type_for_conversion}>(variables[\"{param_sub_type}\"])")
        else:
            # Fallback: treat as RequestBody
            function_args.append(f"nayan::serializer::SerializationUtility::Deserialize<{param_class_name}>(payload)")
    
    # Generate function call
    if is_void:
        # For void return types, call controller method and return CreateOkResponse() (no body)
        if function_args:
            args_str = ", ".join(function_args)
            code += f"    controller->{function_name}({args_str});\n"
        else:
            code += f"    controller->{function_name}();\n"
        code += "    return ResponseEntityConverter::CreateOkResponse();\n"
    elif is_response_entity:
        # For ResponseEntity<T> return types, store return value and use ToHttpResponse<EntityType>(returnValue)
        if function_args:
            args_str = ", ".join(function_args)
            code += f"    {cleaned_return_type} returnValue = controller->{function_name}({args_str});\n"
        else:
            code += f"    {cleaned_return_type} returnValue = controller->{function_name}();\n"
        code += f"    return ResponseEntityConverter::ToHttpResponse<{entity_type}>(returnValue);\n"
    else:
        # For non-void, non-ResponseEntity return types, store return value and use CreateOkResponse<T>(returnValue)
        if function_args:
            args_str = ", ".join(function_args)
            code += f"    {cleaned_return_type} returnValue = controller->{function_name}({args_str});\n"
        else:
            code += f"    {cleaned_return_type} returnValue = controller->{function_name}();\n"
        code += f"    return ResponseEntityConverter::CreateOkResponse<{cleaned_return_type}>(returnValue);\n"
    
    code += "};"
    
    return code


def main():
    """Main function to handle command line arguments and generate function pointer code."""
    parser = argparse.ArgumentParser(
        description="Generate function pointer code for HTTP mapping endpoints"
    )
    parser.add_argument(
        "--url",
        required=True,
        help="Endpoint URL as string (e.g., '/myUrl/mysomeget')"
    )
    parser.add_argument(
        "--http-method",
        required=True,
        choices=["GET", "POST", "PUT", "DELETE", "PATCH"],
        help="HTTP method (GET, POST, PUT, DELETE, PATCH)"
    )
    parser.add_argument(
        "--function-name",
        required=True,
        help="Function name (e.g., 'myFun')"
    )
    parser.add_argument(
        "--return-type",
        required=True,
        help="Return type (e.g., 'int', 'MyReturnDto')"
    )
    parser.add_argument(
        "--first-arg-type",
        default="",
        help="First argument type (e.g., 'TestDto', 'MyInputDto'). Leave empty if no arguments."
    )
    parser.add_argument(
        "--interface-name",
        required=True,
        help="Interface name (e.g., 'ITestController')"
    )
    parser.add_argument(
        "--output",
        help="Output file to save the generated code (optional). If not provided, prints to stdout."
    )
    
    args = parser.parse_args()
    
    # Generate the function pointer code
    generated_code = generate_function_pointer(
        url=args.url,
        http_method=args.http_method,
        function_name=args.function_name,
        return_type=args.return_type,
        first_arg_type=args.first_arg_type,
        interface_name=args.interface_name
    )
    
    # Output the generated code
    if args.output:
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(generated_code)
                f.write('\n')
            # print(f"Generated code saved to: {args.output}")
        except Exception as e:
            # print(f"Error writing to file '{args.output}': {e}")
            # print("\nGenerated code:")
            # print(generated_code)
            pass
    else:
        # print(generated_code)
        pass
    
    return generated_code


# Export functions for other scripts to import
__all__ = [
    'get_mapping_variable_name',
    'generate_function_pointer',
    'generate_function_pointer_advanced',
    'main'
]


if __name__ == "__main__":
    # When run as script, execute main and store result
    result = main()
