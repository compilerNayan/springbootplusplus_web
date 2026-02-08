#!/usr/bin/env python3
"""
Debug test script for parse_function_signature_advanced()
"""

import sys
import os
import re

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from L3_get_endpoint_details import parse_function_signature_advanced, _parse_single_parameter

# Test a simple case
test = "Void SomeFun(/* @RequestBody */ SomeInputDto inputDto, /* @PathVariable(\"xyz\") */ StdString someXyz) {"

print("Testing parameter splitting:")
print(f"Input: {test}")

# Extract args string manually
function_pattern = r'([A-Za-z_][A-Za-z0-9_<>*&:,\s]*?)\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(([^)]*)\)'
match = re.search(function_pattern, test.strip())
if match:
    args_str = match.group(3).strip()
    print(f"\nArgs string: '{args_str}'")
    
    # Test splitting manually
    current_param = ""
    angle_bracket_depth = 0
    paren_depth = 0
    in_annotation = False
    
    i = 0
    params = []
    while i < len(args_str):
        char = args_str[i]
        
        # Check for annotation boundaries
        if i < len(args_str) - 1:
            two_chars = args_str[i:i+2]
            
            if two_chars == '/*' and not in_annotation:
                in_annotation = True
                current_param += two_chars
                i += 2
                print(f"  [i={i}] Found /*, in_annotation=True, current_param='{current_param}'")
                continue
            elif two_chars == '*/' and in_annotation:
                in_annotation = False
                current_param += two_chars
                i += 2
                print(f"  [i={i}] Found */, in_annotation=False, current_param='{current_param}'")
                continue
        
        if char == '<':
            angle_bracket_depth += 1
            current_param += char
        elif char == '>':
            angle_bracket_depth -= 1
            current_param += char
        elif char == '(':
            paren_depth += 1
            current_param += char
        elif char == ')':
            paren_depth -= 1
            current_param += char
        elif char == ',' and angle_bracket_depth == 0 and paren_depth == 0 and not in_annotation:
            param_str = current_param.strip()
            print(f"  [i={i}] Found comma separator, param='{param_str}'")
            if param_str:
                params.append(param_str)
            current_param = ""
        else:
            current_param += char
        
        i += 1
    
    if current_param.strip():
        param_str = current_param.strip()
        print(f"  [i={i}] Last param='{param_str}'")
        params.append(param_str)
    
    print(f"\nSplit into {len(params)} parameters:")
    for i, p in enumerate(params, 1):
        print(f"  Param {i}: '{p}'")
        result = _parse_single_parameter(p)
        if result:
            print(f"    Parsed: type={result['type']}, subType='{result['subType']}', class_name={result['class_name']}, param_name={result['param_name']}")
        else:
            print(f"    Failed to parse")

