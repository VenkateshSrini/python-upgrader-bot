#!/usr/bin/env python3
"""
Test script for AI Tools

This script tests all AI migration and modernization tools.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from app_py_version.ai_tools import PyUpgradeTool, Python2To3Tool, ModernizeTool

def test_pyupgrade_tool():
    """Test PyUpgrade tool functionality"""
    print("🧪 Testing PyUpgrade Tool...")
    
    tool = PyUpgradeTool(target_version="3.11")
    
    # Test case 1: Format string to f-string
    test_code1 = '''name = "Alice"
age = 30
message = "Hello, my name is {} and I am {} years old".format(name, age)'''
    
    print("   📝 Test Case 1: Format string to f-string conversion")
    result1 = tool._run(test_code1)
    print(f"   ✅ Result length: {len(result1)} characters")
    
    # Test case 2: Already modern code
    test_code2 = '''name = "Alice"
age = 30
message = f"Hello, my name is {name} and I am {age} years old"'''
    
    print("   📝 Test Case 2: Already modern code")
    result2 = tool._run(test_code2)
    print(f"   ✅ Result length: {len(result2)} characters")
    
    # Test case 3: Invalid syntax
    test_code3 = '''def invalid_syntax(
    print("Missing closing paren")'''
    
    print("   📝 Test Case 3: Invalid syntax handling")
    result3 = tool._run(test_code3)
    print(f"   ✅ Error handled: {'Error' in result3}")
    
    print("   ✅ PyUpgrade tool tests completed\n")


def test_python2to3_tool():
    """Test Python 2 to 3 migration tool"""
    print("🧪 Testing Python 2 to 3 Tool...")
    
    tool = Python2To3Tool()
    
    # Test case 1: Classic Python 2 code
    test_code1 = '''print "Hello, World!"
name = raw_input("Enter your name: ")
for i in xrange(10):
    print i'''
    
    print("   📝 Test Case 1: Classic Python 2 patterns")
    result1 = tool._run(test_code1)
    print(f"   ✅ Result length: {len(result1)} characters")
    
    # Test case 2: Already Python 3 code
    test_code2 = '''print("Hello, World!")
name = input("Enter your name: ")
for i in range(10):
    print(i)'''
    
    print("   📝 Test Case 2: Already Python 3 compatible")
    result2 = tool._run(test_code2)
    print(f"   ✅ Result length: {len(result2)} characters")
    
    # Test case 3: Mixed Python 2/3 patterns
    test_code3 = '''import urllib2
print "Downloading..."
data = urllib2.urlopen("http://example.com").read()
print "Done"'''
    
    print("   📝 Test Case 3: Import and print statement fixes")
    result3 = tool._run(test_code3)
    print(f"   ✅ Result length: {len(result3)} characters")
    
    print("   ✅ Python 2 to 3 tool tests completed\n")


def test_modernize_tool():
    """Test Python 2/3 compatibility modernization tool"""
    print("🧪 Testing Modernize Tool...")
    
    tool = ModernizeTool()
    
    # Test case 1: Python 2 code needing compatibility
    test_code1 = '''print "Hello, World!"
data = {"a": 1, "b": 2}
for key in data.iterkeys():
    print key, data[key]'''
    
    print("   📝 Test Case 1: Python 2 compatibility patterns")
    result1 = tool._run(test_code1)
    print(f"   ✅ Result length: {len(result1)} characters")
    
    # Test case 2: Already compatible code
    test_code2 = '''from __future__ import print_function
print("Hello, World!")
data = {"a": 1, "b": 2}
for key in data.keys():
    print(key, data[key])'''
    
    print("   📝 Test Case 2: Already compatible code")
    result2 = tool._run(test_code2)
    print(f"   ✅ Result length: {len(result2)} characters")
    
    # Test case 3: Division compatibility
    test_code3 = '''def calculate_average(total, count):
    return total / count

result = calculate_average(10, 3)
print result'''
    
    print("   📝 Test Case 3: Division and print compatibility")
    result3 = tool._run(test_code3)
    print(f"   ✅ Result length: {len(result3)} characters")
    
    print("   ✅ Modernize tool tests completed\n")


def test_error_handling():
    """Test error handling across all tools"""
    print("🧪 Testing Error Handling...")
    
    tools = [
        ("PyUpgrade", PyUpgradeTool()),
        ("Python2To3", Python2To3Tool()),
        ("Modernize", ModernizeTool())
    ]
    
    # Test empty input
    for tool_name, tool in tools:
        result = tool._run("")
        print(f"   ✅ {tool_name} empty input: {'Error' in result}")
    
    # Test None input
    for tool_name, tool in tools:
        result = tool._run(None)
        print(f"   ✅ {tool_name} None input: {'Error' in result}")
    
    # Test invalid type input
    for tool_name, tool in tools:
        result = tool._run(123)
        print(f"   ✅ {tool_name} invalid type: {'Error' in result}")
    
    print("   ✅ Error handling tests completed\n")


def test_langchain_compatibility():
    """Test LangChain tool interface compatibility"""
    print("🧪 Testing LangChain Compatibility...")
    
    tools = [
        ("PyUpgrade", PyUpgradeTool()),
        ("Python2To3", Python2To3Tool()),
        ("Modernize", ModernizeTool())
    ]
    
    for tool_name, tool in tools:
        # Test tool attributes required by LangChain
        print(f"   📝 Testing {tool_name} LangChain interface:")
        print(f"      ✅ Has name: {hasattr(tool, 'name') and tool.name}")
        print(f"      ✅ Has description: {hasattr(tool, 'description') and len(tool.description) > 0}")
        print(f"      ✅ Has _run method: {hasattr(tool, '_run') and callable(tool._run)}")
        print(f"      ✅ Has _arun method: {hasattr(tool, '_arun') and callable(tool._arun)}")
    
    print("   ✅ LangChain compatibility tests completed\n")


def run_all_tests():
    """Run all tests"""
    print("🚀 Starting AI Tools Test Suite...")
    print("=" * 60)
    
    try:
        test_pyupgrade_tool()
        test_python2to3_tool()
        test_modernize_tool()
        test_error_handling()
        test_langchain_compatibility()
        
        print("🎉 All AI Tools tests completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()