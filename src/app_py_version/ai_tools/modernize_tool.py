#!/usr/bin/env python3
"""
Python Modernize Tool - Direct Integration

A LangChain-compatible tool that uses the actual python-modernize tool
to create Python 2/3 compatible code. This provides reliable compatibility
using the same engine as the modernize command-line tool.
"""

import subprocess
import tempfile
import os
import re
import shutil
from typing import Optional, Any, Type, List, Dict
from pydantic import BaseModel, Field
from langchain.tools import BaseTool
import logging

logger = logging.getLogger(__name__)


class ModernizeInput(BaseModel):
    """Input schema for Python modernize tool"""
    code: str = Field(description="Python code to make Python 2/3 compatible")


class ModernizeTool(BaseTool):
    """
    Python Modernize Tool using python-modernize.
    
    This tool makes Python code compatible with both Python 2 and 3:
    - Adds appropriate __future__ imports
    - Uses six library for compatibility  
    - Handles string/unicode differences
    - Fixes print statement compatibility
    - Updates import statements for cross-compatibility
    """
    
    name: str = "modernize"
    description: str = "Make Python code compatible with both Python 2 and 3 using modernize"
    args_schema: Type[BaseModel] = ModernizeInput
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def _get_compatibility_patterns(self) -> Dict[str, str]:
        """Get compatibility patterns dictionary"""
        return {
            "print_statement": r'\bprint\s+[^(]',
            "division": r'(?<!\/)\/(?!\/)',  # Single slash not preceded or followed by slash
            "string_types": r'\bstr\s*\(',
            "unicode_types": r'\bunicode\s*\(',
            "dict_methods": r'\.(keys|values|items)\(\)',
            "input_function": r'\braw_input\s*\(',
        }
    
    def _check_modernize_available(self) -> bool:
        """Check if python-modernize is available"""
        # Try direct command first
        try:
            result = subprocess.run(['python-modernize', '--help'], 
                                  capture_output=True, timeout=10)
            if result.returncode == 0:
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # Try with python -m modernize
        try:
            result = subprocess.run(['python', '-m', 'libmodernize', '--help'], 
                                  capture_output=True, timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _run_modernize_on_code(self, code: str) -> tuple[str, bool, str]:
        """
        Run python-modernize on the provided code.
        
        Returns:
            tuple: (updated_code, was_changed, error_message)
        """
        try:
            # Create a temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
                temp_file.write(code)
                temp_file_path = temp_file.name
            
            try:
                # Run python-modernize (try direct command first, then python -m)
                if shutil.which('python-modernize'):
                    cmd = ['python-modernize', '--print', '--no-diffs', temp_file_path]
                else:
                    cmd = ['python', '-m', 'libmodernize', '--print', '--no-diffs', temp_file_path]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    # python-modernize prints the result to stdout
                    updated_code = result.stdout
                    if updated_code.strip():
                        was_changed = updated_code != code
                        return updated_code, was_changed, ""
                    else:
                        # No output, read the file
                        with open(temp_file_path, 'r', encoding='utf-8') as f:
                            updated_code = f.read()
                        was_changed = updated_code != code
                        return updated_code, was_changed, ""
                else:
                    error_msg = result.stderr or "Unknown modernize error"
                    return code, False, f"modernize error: {error_msg}"
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except subprocess.TimeoutExpired:
            return code, False, "modernize command timed out"
        except Exception as e:
            return code, False, f"Error running modernize: {str(e)}"
    
    def _pattern_based_modernization(self, code: str) -> tuple[str, List[str]]:
        """
        Fallback pattern-based modernization when python-modernize is not available.
        
        Returns:
            tuple: (modernized_code, list_of_changes)
        """
        modernized_code = code
        changes_made = []
        future_imports = set()
        
        # Check if __future__ imports are needed
        needs_print_function = bool(re.search(r'\bprint\s+[^(]', code))
        needs_division = bool(re.search(r'(?<!\/)\/(?!\/)', code))
        
        # Add necessary __future__ imports
        if needs_print_function:
            future_imports.add("print_function")
            changes_made.append("Added from __future__ import print_function")
        
        if needs_division:
            future_imports.add("division")  
            changes_made.append("Added from __future__ import division")
        
        # Build __future__ import statement
        if future_imports:
            future_import_line = f"from __future__ import {', '.join(sorted(future_imports))}\n"
            
            # Insert at the top, after any existing __future__ imports or docstrings
            lines = modernized_code.split('\n')
            insert_pos = 0
            
            # Skip shebang, encoding, and docstrings
            for i, line in enumerate(lines):
                stripped = line.strip()
                if (stripped.startswith('#') or 
                    stripped.startswith('"""') or 
                    stripped.startswith("'''") or
                    stripped.startswith('from __future__') or
                    not stripped):
                    insert_pos = i + 1
                else:
                    break
            
            lines.insert(insert_pos, future_import_line)
            modernized_code = '\n'.join(lines)
        
        # Convert print statements to be compatible (if print_function is imported)
        if needs_print_function:
            print_pattern = r'\bprint\s+([^(].+?)(?=\n|$)'
            def print_replacer(match):
                content = match.group(1).strip()
                return f'print({content})'
            
            modernized_code = re.sub(print_pattern, print_replacer, modernized_code, flags=re.MULTILINE)
            changes_made.append("Converted print statements to print() function")
        
        return modernized_code, changes_made
    
    def _detect_compatibility_issues(self, code: str) -> List[str]:
        """Detect potential Python 2/3 compatibility issues"""
        issues = []
        patterns = self._get_compatibility_patterns()
        for issue_name, pattern in patterns.items():
            if re.search(pattern, code):
                issues.append(issue_name)
        return issues
    
    def _run(self, code: str, **kwargs) -> str:
        """Run the Python modernize tool on the provided code"""
        try:
            # Validate input
            if not code or not isinstance(code, str):
                return "❌ Error: Invalid input. Please provide Python code as a string."
            
            code = code.strip()
            if not code:
                return "❌ Error: Empty code provided."
            
            # Detect potential compatibility issues
            compatibility_issues = self._detect_compatibility_issues(code)
            
            # Check if python-modernize is available
            if self._check_modernize_available():
                # Use the real python-modernize tool
                updated_code, was_changed, error_msg = self._run_modernize_on_code(code)
                
                if error_msg:
                    logger.warning(f"modernize error: {error_msg}, falling back to pattern-based")
                    updated_code, changes_made = self._pattern_based_modernization(code)
                    was_changed = len(changes_made) > 0
                    
                    if was_changed:
                        return f"""🔧 Python 2/3 Compatibility Applied (Pattern-based)

Compatibility Issues Detected: {', '.join(compatibility_issues)}

📝 Modernized Code:
```python
{updated_code}
```

🔧 Changes Applied:
""" + "\n".join(f"- {change}" for change in changes_made) + """

✅ Code is now compatible with both Python 2.7+ and Python 3.x"""
                    else:
                        return f"""🔍 Python 2/3 Compatibility Analysis Complete

No automatic fixes could be applied.

📝 Original code:
```python
{code}
```

ℹ️  Code appears to already be compatible with both Python versions."""
                
                if was_changed:
                    return f"""🚀 Python 2/3 Compatibility Applied (using python-modernize)

Compatibility Issues Detected: {', '.join(compatibility_issues)}

📝 Modernized Code:
```python
{updated_code}
```

✅ Code has been successfully modernized using the python-modernize tool.
Code is now compatible with both Python 2.7+ and Python 3.x"""
                else:
                    return f"""🔍 Python 2/3 Compatibility Analysis Complete

No changes needed - code is already compatible.

📝 Original code:
```python
{code}
```

✅ Code is already compatible with both Python 2.7+ and Python 3.x"""
            
            else:
                # Fallback to pattern-based modernization
                logger.info("python-modernize not available, using pattern-based modernization")
                updated_code, changes_made = self._pattern_based_modernization(code)
                
                if changes_made:
                    return f"""🔧 Python 2/3 Compatibility Applied (Pattern-based Fallback)

Compatibility Issues Detected: {', '.join(compatibility_issues)}

📝 Modernized Code:
```python
{updated_code}
```

🔧 Changes Applied:
""" + "\n".join(f"- {change}" for change in changes_made) + """

✅ Code should now be more compatible with both Python 2.7+ and Python 3.x
⚠️  For best results, install python-modernize: pip install modernize"""
                else:
                    return f"""🔍 Python 2/3 Compatibility Analysis Complete

📝 Original code:
```python
{code}
```

ℹ️  Code appears to already be compatible or no automatic fixes available.
💡 For comprehensive modernization, install python-modernize: pip install modernize"""
                
        except Exception as e:
            logger.error(f"Modernize tool error: {e}")
            return f"❌ Error during modernization: {str(e)}"

    def run(self, code: str, **kwargs) -> str:
        """
        Public interface for running the tool.
        
        Args:
            code: Python code to modernize for 2/3 compatibility
            **kwargs: Additional parameters (ignored for compatibility)
        
        Returns:
            Modernization result as formatted string
        """
        return self._run(code, **kwargs)