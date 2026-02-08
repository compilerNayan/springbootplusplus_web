#!/usr/bin/env python3
"""
Test script for parse_function_signature_advanced()
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from L3_get_endpoint_details import parse_function_signature_advanced

# Test cases
test_cases = [
    # Test 1: Single RequestBody parameter
    "Void SomeFun(/* @RequestBody */ SomeInputDto inputDto) {",
    
    # Test 2: RequestBody + PathVariable
    "Void SomeFun(/* @RequestBody */ SomeInputDto inputDto, /* @PathVariable(\"xyz\") */ StdString someXyz) {",
    
    # Test 3: RequestBody + Multiple PathVariables
    "Void SomeFun(/* @RequestBody */ SomeInputDto inputDto, /* @PathVariable(\"xyz\") */ StdString someXyz, /* @PathVariable(\"abc\") */ const int abc) {",
    
    # Test 4: Only PathVariables
    "Void SomeFun(/* @PathVariable(\"id\") */ int id, /* @PathVariable(\"name\") */ StdString name) {",
    
    # Test 5: Complex types
    "MyReturnDto GetData(/* @PathVariable(\"id\") */ const int id, /* @RequestBody */ ComplexType<InnerType> data) {",
]

print("=" * 80)
print("Testing parse_function_signature_advanced()")
print("=" * 80)
print()

for i, test_case in enumerate(test_cases, 1):
    print(f"Test Case {i}:")
    print(f"  Input: {test_case}")
    print()
    
    result = parse_function_signature_advanced(test_case)
    
    if result:
        print(f"  Return Type: {result['return_type']}")
        print(f"  Function Name: {result['function_name']}")
        print(f"  Parameters ({len(result['parameters'])}):")
        
        for j, param in enumerate(result['parameters'], 1):
            print(f"    Parameter {j}:")
            print(f"      type: {param['type']}")
            print(f"      subType: '{param['subType']}'")
            print(f"      class_name: {param['class_name']}")
            print(f"      param_name: {param['param_name']}")
    else:
        print("  ❌ Failed to parse")
    
    print()
    print("-" * 80)
    print()

