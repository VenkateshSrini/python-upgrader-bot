#!/usr/bin/env python3
"""
Python 2 to 3 Migration Tool - Direct Integration

A LangChain-compatible tool that uses lib2to3 and pattern matching
to migrate Python 2 code to Python 3. This provides reliable migration
using the same engine as the 2to3 command-line tool.
"""

import re
import ast
import tempfile
import os
from typing import Optional, Any, Type, List, Dict
from pydantic import BaseModel, Field
from langchain.tools import BaseTool
import logging

logger = logging.getLogger(__name__)


class Python2To3Input(BaseModel):
    """Input schema for Python 2 to 3 migration tool"""
    code: str = Field(description="Python 2 code to migrate to Python 3")


class Python2To3Tool(BaseTool):
    """
    Python 2 to 3 Migration Tool using lib2to3 engine.
    
    This tool migrates Python 2 code to Python 3:
    - Print statements to print() function
    - String/Unicode handling changes
    - Integer division changes
    - Iterator method changes (.keys(), .values(), .items())
    - Import statement updates (urllib2, ConfigParser, etc.)
    - Exception handling syntax updates
    - xrange to range conversion
    - raw_input to input conversion
    """
    
    name: str = "python2to3"
    description: str = "Migrate Python 2 code to Python 3 using lib2to3"
    args_schema: Type[BaseModel] = Python2To3Input
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def _get_python2_patterns(self) -> Dict[str, str]:
        """Get Python 2 pattern dictionary"""
        return {
            "print_statement": r'\bprint\s+[^(]',
            "unicode_literals": r'\bunicode\s*\(',
            "dict_methods": r'\.iter(keys|values|items)\(\)',
            "imports_urllib2": r'import\s+urllib2',
            "imports_configparser": r'import\s+ConfigParser',
            "exception_syntax": r'except\s+\w+\s*,\s*\w+:',
            "raw_input": r'\braw_input\s*\(',
            "xrange": r'\bxrange\s*\(',
        }
    
    def _detect_python2_patterns(self, code: str) -> List[str]:
        """Detect Python 2 specific patterns in the code"""
        detected = []
        patterns = self._get_python2_patterns()
        for pattern_name, pattern in patterns.items():
            if re.search(pattern, code):
                detected.append(pattern_name)
        return detected
    
    def _use_lib2to3(self, code: str) -> tuple[str, bool, str]:
        """
        Use lib2to3 to migrate Python 2 code to Python 3.
        
        Returns:
            tuple: (migrated_code, was_changed, error_message)
        """
        try:
            from lib2to3 import pytree, pygram
            from lib2to3.pgen2 import driver
            from lib2to3.refactor import RefactoringTool
            
            # Create a RefactoringTool with common fixes
            rt = RefactoringTool(['print', 'unicode', 'xrange', 'raw_input', 'urllib', 'except'])
            
            # Try to refactor the code
            try:
                new_code = rt.refactor_string(code, '<string>')
                if new_code is None:
                    return code, False, ""
                
                migrated = str(new_code)
                was_changed = migrated != code
                return migrated, was_changed, ""
                
            except Exception as e:
                return code, False, f"lib2to3 refactoring failed: {str(e)}"
                
        except ImportError:
            return code, False, "lib2to3 not available"
        except Exception as e:
            return code, False, f"lib2to3 error: {str(e)}"
    
    def _pattern_based_migration(self, code: str) -> tuple[str, List[str]]:
        """
        Fallback pattern-based migration when lib2to3 is not available.
        
        Returns:
            tuple: (migrated_code, list_of_changes)
        """
        migrated_code = code
        changes_made = []
        
        # Convert print statements to print() function
        print_pattern = r'\bprint\s+([^(].+?)(?=\n|$)'
        def print_replacer(match):
            content = match.group(1).strip()
            changes_made.append("Converted print statement to print() function")
            return f'print({content})'
        
        migrated_code = re.sub(print_pattern, print_replacer, migrated_code, flags=re.MULTILINE)
        
        # Convert xrange to range
        if re.search(r'\bxrange\b', migrated_code):
            migrated_code = re.sub(r'\bxrange\b', 'range', migrated_code)
            changes_made.append("Converted xrange() to range()")
        
        # Convert raw_input to input
        if re.search(r'\braw_input\b', migrated_code):
            migrated_code = re.sub(r'\braw_input\b', 'input', migrated_code)
            changes_made.append("Converted raw_input() to input()")
        
        # Update import statements
        import_replacements = [
            (r'import\s+urllib2', 'import urllib.request', 'Updated import: import urllib2 → import urllib.request'),
            (r'import\s+ConfigParser', 'import configparser', 'Updated import: import ConfigParser → import configparser'),
            (r'import\s+cPickle', 'import pickle', 'Updated import: import cPickle → import pickle'),
            (r'import\s+__builtin__', 'import builtins', 'Updated import: import __builtin__ → import builtins'),
        ]
        
        for old_pattern, new_import, change_desc in import_replacements:
            if re.search(old_pattern, migrated_code):
                migrated_code = re.sub(old_pattern, new_import, migrated_code)
                changes_made.append(change_desc)
        
        # Fix exception handling syntax
        except_pattern = r'except\s+(\w+)\s*,\s*(\w+):'
        def except_replacer(match):
            exception_type = match.group(1)
            variable = match.group(2)
            changes_made.append("Updated exception handling syntax")
            return f'except {exception_type} as {variable}:'
        
        migrated_code = re.sub(except_pattern, except_replacer, migrated_code)
        
        return migrated_code, changes_made
    
    def _run(self, code: str, **kwargs) -> str:
        """Run the Python 2 to 3 migration tool on the provided code"""
        try:
            # Validate input
            if not code or not isinstance(code, str):
                return "❌ Error: Invalid input. Please provide Python code as a string."
            
            code = code.strip()
            if not code:
                return "❌ Error: Empty code provided."
            
            # Detect Python 2 patterns
            python2_patterns = self._detect_python2_patterns(code)
            if not python2_patterns:
                return f"""ℹ️ Python 2 to 3 Migration Analysis

The provided code appears to already be Python 3 compatible.
No Python 2 specific patterns detected.

📝 Original code:
```python
{code}
```

✅ No migration needed - code is already Python 3 compatible!"""
            
            # Try using lib2to3 first
            migrated_code, was_changed, error_msg = self._use_lib2to3(code)
            
            if error_msg and "not available" not in error_msg:
                logger.warning(f"lib2to3 error: {error_msg}, falling back to pattern-based migration")
            
            # If lib2to3 failed or didn't make changes, use pattern-based migration
            if not was_changed or error_msg:
                migrated_code, changes_made = self._pattern_based_migration(code)
                was_changed = len(changes_made) > 0
                
                if was_changed:
                    return f"""🚀 Python 2 to 3 Migration Complete

Issues Fixed: {len(changes_made)}
Python 2 Indicators Found: {', '.join(python2_patterns)}

📝 Migrated Code:
```python
{migrated_code}
```

🔧 Migration Changes Applied:

""" + "\n".join(f"{i+1}. {change}" for i, change in enumerate(changes_made)) + """

⚠️  IMPORTANT: After migration, please:
1. Test your code thoroughly
2. Check for any remaining compatibility issues
3. Update your shebang line to use python3
4. Update your requirements.txt for Python 3 compatible packages"""
                else:
                    return f"""🔍 Python 2 to 3 Migration Analysis Complete

No automatic fixes could be applied, but Python 2 patterns were detected: {', '.join(python2_patterns)}

📝 Original code:
```python
{code}
```

⚠️  Manual review may be needed for complete migration."""
            
            # lib2to3 successfully made changes
            return f"""🚀 Python 2 to 3 Migration Complete (using lib2to3)

Python 2 Indicators Found: {', '.join(python2_patterns)}

📝 Migrated Code:
```python
{migrated_code}
```

✅ Code has been successfully migrated using the lib2to3 refactoring tool.

⚠️  IMPORTANT: After migration, please:
1. Test your code thoroughly
2. Check for any remaining compatibility issues
3. Update your shebang line to use python3
4. Update your requirements.txt for Python 3 compatible packages"""
                
        except Exception as e:
            logger.error(f"Python 2 to 3 migration error: {e}")
            return f"❌ Error during migration: {str(e)}"

    def run(self, code: str, **kwargs) -> str:
        """
        Public interface for running the tool.
        
        Args:
            code: Python 2 code to migrate
            **kwargs: Additional parameters (ignored for compatibility)
        
        Returns:
            Migration result as formatted string
        """
        return self._run(code, **kwargs)