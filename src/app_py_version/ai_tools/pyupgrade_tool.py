#!/usr/bin/env python3
"""
PyUpgrade Tool - Direct Integration

A LangChain-compatible tool that uses the actual pyupgrade command-line tool
to modernize Python code syntax. This provides reliable, tested modernization
without relying on AI analysis.
"""

import subprocess
import tempfile
import os
import ast
import shutil
from typing import Optional, Any, Type
from pydantic import BaseModel, Field
from langchain.tools import BaseTool
import logging

logger = logging.getLogger(__name__)


class PyUpgradeInput(BaseModel):
    """Input schema for PyUpgrade tool"""
    code: str = Field(description="Python code to modernize")
    target_version: str = Field(
        default="3.11", 
        description="Target Python version (e.g., '3.8', '3.9', '3.11')"
    )


class PyUpgradeTool(BaseTool):
    """
    PyUpgrade Tool for modernizing Python code using the actual pyupgrade command.
    
    This tool uses the real pyupgrade CLI tool to modernize Python code:
    - f-strings instead of .format() or % formatting
    - Union syntax using | operator (Python 3.10+)
    - Modern type hints
    - Updated function signatures
    - Removal of unnecessary __future__ imports
    """
    
    name: str = "pyupgrade"
    description: str = "Modernize Python code to newer syntax patterns using the pyupgrade tool"
    args_schema: Type[BaseModel] = PyUpgradeInput
    target_version: str = Field(default="3.11")
    
    def __init__(self, target_version: str = "3.11", **kwargs):
        super().__init__(**kwargs)
        self.target_version = target_version
    
    def _check_pyupgrade_available(self) -> bool:
        """Check if pyupgrade is available in the system"""
        # Try direct command first
        if shutil.which("pyupgrade"):
            return True
        
        # Try with python -m pyupgrade
        try:
            result = subprocess.run(['python', '-m', 'pyupgrade', '--help'], 
                                  capture_output=True, timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _get_pyupgrade_args(self) -> list:
        """Get pyupgrade command arguments based on target version"""
        # Try direct command first, then fallback to python -m
        if shutil.which("pyupgrade"):
            args = ["pyupgrade"]
        else:
            args = ["python", "-m", "pyupgrade"]
        
        # Map Python versions to pyupgrade arguments
        version_mapping = {
            "3.6": ["--py36-plus"],
            "3.7": ["--py37-plus"],
            "3.8": ["--py38-plus"],
            "3.9": ["--py39-plus"],
            "3.10": ["--py310-plus"],
            "3.11": ["--py311-plus"],
            "3.12": ["--py312-plus"],
        }
        
        # Use the appropriate flag for the target version
        if self.target_version in version_mapping:
            args.extend(version_mapping[self.target_version])
        else:
            # Default to py311-plus for unknown versions
            args.extend(["--py311-plus"])
        
        return args
    
    def _run_pyupgrade_on_code(self, code: str) -> tuple[str, bool, str]:
        """
        Run pyupgrade on the provided code.
        
        Returns:
            tuple: (updated_code, was_changed, error_message)
        """
        try:
            # Create a temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
                temp_file.write(code)
                temp_file_path = temp_file.name
            
            try:
                # Prepare pyupgrade command
                cmd = self._get_pyupgrade_args()
                cmd.append(temp_file_path)
                
                # Run pyupgrade
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                # Read the updated file
                with open(temp_file_path, 'r', encoding='utf-8') as f:
                    updated_code = f.read()
                
                # Check if changes were made
                was_changed = updated_code != code
                
                # Handle pyupgrade's return codes
                if result.returncode == 0:
                    return updated_code, was_changed, ""
                elif result.returncode == 1:
                    # pyupgrade returns 1 when it makes changes
                    return updated_code, True, ""
                else:
                    error_msg = result.stderr or "Unknown pyupgrade error"
                    return code, False, f"pyupgrade error: {error_msg}"
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except subprocess.TimeoutExpired:
            return code, False, "pyupgrade command timed out"
        except Exception as e:
            return code, False, f"Error running pyupgrade: {str(e)}"
    
    def _pattern_based_fallback(self, code: str) -> str:
        """
        Fallback method when pyupgrade is not available.
        Applies basic modernization patterns.
        """
        import re
        
        updated_code = code
        changes_made = []
        
        # Convert simple .format() to f-strings
        format_pattern = r'(["\'])([^"\']*?)\{(\w+)\}([^"\']*?)\1\.format\(\s*(\w+)\s*\)'
        def format_replacer(match):
            quote = match.group(1)
            before = match.group(2)
            var_name = match.group(3)
            after = match.group(4)
            param = match.group(5)
            if var_name == param:
                changes_made.append(f"Converted .format() to f-string")
                return f'f{quote}{before}{{{var_name}}}{after}{quote}'
            return match.group(0)
        
        updated_code = re.sub(format_pattern, format_replacer, updated_code)
        
        # Convert % formatting to f-strings (simple cases)
        percent_pattern = r'(["\'])([^"\']*?)%s([^"\']*?)\1\s*%\s*(\w+)'
        def percent_replacer(match):
            quote = match.group(1)
            before = match.group(2)
            after = match.group(3)
            var_name = match.group(4)
            changes_made.append(f"Converted % formatting to f-string")
            return f'f{quote}{before}{{{var_name}}}{after}{quote}'
        
        updated_code = re.sub(percent_pattern, percent_replacer, updated_code)
        
        if changes_made:
            return f"🔧 Fallback Modernization Applied\n\nChanges made:\n" + "\n".join(f"- {change}" for change in changes_made) + f"\n\n📝 Updated Code:\n```python\n{updated_code}\n```"
        else:
            return f"🔍 Fallback Analysis Complete - No changes needed\n\nThe code appears to be using modern Python patterns.\n\n📝 Original code:\n```python\n{code}\n```"
    
    def _run(self, code: str, **kwargs) -> str:
        """Run the PyUpgrade tool on the provided code"""
        try:
            # Validate input
            if not code or not isinstance(code, str):
                return "❌ Error: Invalid input. Please provide Python code as a string."
            
            code = code.strip()
            if not code:
                return "❌ Error: Empty code provided."
            
            # Validate Python syntax
            try:
                ast.parse(code)
            except SyntaxError as e:
                return f"❌ Error: Invalid Python syntax: {e}"
            
            # Check if pyupgrade is available
            if not self._check_pyupgrade_available():
                logger.warning("pyupgrade not found, using fallback method")
                return self._pattern_based_fallback(code)
            
            # Run pyupgrade
            updated_code, was_changed, error_msg = self._run_pyupgrade_on_code(code)
            
            if error_msg:
                return f"❌ Error: {error_msg}"
            
            if was_changed:
                return f"""� PyUpgrade Modernization Complete

Target Version: Python {self.target_version}

📝 Modernized Code:
```python
{updated_code}
```

✅ Code has been successfully modernized using pyupgrade tool."""
            else:
                return f"""� PyUpgrade Analysis Complete - No changes needed

Target Version: Python {self.target_version}

The code is already using modern Python {self.target_version} syntax patterns.

📝 Original code:
```python
{code}
```"""
                
        except Exception as e:
            logger.error(f"PyUpgrade tool error: {e}")
            return f"❌ Error during code modernization: {str(e)}"

    def run(self, code: str, target_version: str = None, **kwargs) -> str:
        """
        Public interface for running the tool.
        
        Args:
            code: Python code to modernize
            target_version: Target Python version (optional, uses instance default)
            **kwargs: Additional parameters (ignored for compatibility)
        
        Returns:
            Modernization result as formatted string
        """
        if target_version:
            self.target_version = target_version
        
        return self._run(code, **kwargs)