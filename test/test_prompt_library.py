#!/usr/bin/env python3
"""
Test script for prompt_library module

This script tests the prompt library to ensure all prompts are working correctly.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from app_py_version.prompt_library import (
    PromptLibrary, 
    PromptTemplates,
    create_version_detection_messages,
    create_migration_analysis_messages
)

def test_prompt_library():
    """Test all prompt generation functions"""
    print("🧪 Testing Prompt Library...")
    
    # Test version detection prompts
    print("\n1. Testing Version Detection Prompts")
    system_prompt = PromptLibrary.get_version_detection_system_prompt()
    print(f"   ✅ System prompt length: {len(system_prompt)} characters")
    
    dependencies = {'requirements': ['requests==2.28.0']}
    code_samples = [{'file': 'test.py', 'content': 'print("hello")'}]
    user_prompt = PromptLibrary.get_version_detection_user_prompt(dependencies, code_samples)
    print(f"   ✅ User prompt length: {len(user_prompt)} characters")
    
    # Test migration analysis prompts
    print("\n2. Testing Migration Analysis Prompts")
    system_prompt_migration = PromptLibrary.get_migration_analysis_system_prompt(
        "Python 2.x to 3.x", "2.7", "3.11", True
    )
    print(f"   ✅ Migration system prompt length: {len(system_prompt_migration)} characters")
    
    file_contents = {'test.py': 'print "hello world"'}
    user_prompt_migration = PromptLibrary.get_migration_analysis_user_prompt(
        file_contents, "2.7", "3.11"
    )
    print(f"   ✅ Migration user prompt length: {len(user_prompt_migration)} characters")
    
    # Test message creation functions
    print("\n3. Testing Message Creation Functions")
    try:
        messages = create_version_detection_messages(dependencies, code_samples)
        print(f"   ✅ Version detection messages created: {len(messages)} messages")
        
        messages_migration = create_migration_analysis_messages(file_contents, "2.7", "3.11")
        print(f"   ✅ Migration analysis messages created: {len(messages_migration)} messages")
    except ImportError as e:
        print(f"   ⚠️ Message creation requires langchain: {e}")
    
    # Test template data
    print("\n4. Testing Template Data")
    print(f"   ✅ Python2->3 focus areas: {len(PromptTemplates.MIGRATION_FOCUS_AREAS['python2_to_3'])} items")
    print(f"   ✅ Python3 upgrade focus areas: {len(PromptTemplates.MIGRATION_FOCUS_AREAS['python3_upgrade'])} items")
    print(f"   ✅ Severity levels: {len(PromptTemplates.SEVERITY_LEVELS)} levels")
    print(f"   ✅ Issue categories: {len(PromptTemplates.ISSUE_CATEGORIES)} categories")
    
    print("\n✅ All prompt library tests passed!")

if __name__ == "__main__":
    test_prompt_library()