"""
AI-Powered Python Version Analyzer Package

This package provides intelligent Python version analysis and migration planning
using Large Language Models (LLMs) to identify potential issues and provide
actionable recommendations.

Key Features:
- 🔍 Intelligent version detection from multiple sources
- 🤖 AI-powered migration issue analysis  
- ⚖️ Risk assessment and effort estimation
- 💡 Actionable recommendations
- 📊 Comprehensive reporting

Usage:
    from app_py_version import PythonVersionAnalyzer
    
    analyzer = PythonVersionAnalyzer(target_version="3.11")
    result = analyzer.analyze_project("/path/to/project")
    analyzer.save_analysis(result)

CLI Usage:
    python cli.py analyze . --target-version 3.11 --detailed
"""

__version__ = "1.0.0"
__author__ = "AI Python Upgrade Assistant"
__email__ = "ai-assistant@python-upgrade.dev"

from .version_analyzer import (
    PythonVersionAnalyzer,
    PythonVersionInfo,
    MigrationIssue,
    AnalysisResult
)
from .prompt_library import (
    PromptLibrary,
    PromptTemplates
)
from .ai_tools import (
    PyUpgradeTool,
    Python2To3Tool,
    ModernizeTool
)

__all__ = [
    'PythonVersionAnalyzer',
    'PythonVersionInfo', 
    'MigrationIssue',
    'AnalysisResult',
    'PromptLibrary',
    'PromptTemplates',
    'PyUpgradeTool',
    'Python2To3Tool',
    'ModernizeTool'
]