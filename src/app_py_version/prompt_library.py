#!/usr/bin/env python3
"""
Prompt Library for Python Version Analyzer and Migration Executor

This module contains all AI prompts used in the Python version analysis and migration process.
This includes prompts for version detection, migration analysis, risk assessment, and
migration execution. Centralizing prompts makes them easier to maintain, test, and version control.

Author: Your AI Python Upgrade Assistant
"""

from typing import Dict, Any


class PromptLibrary:
    """Centralized prompt library for Python version analysis and migration"""
    
    @staticmethod
    def get_version_detection_system_prompt() -> str:
        """Get the system prompt for Python version detection"""
        return """You are an expert Python developer and version migration specialist with deep knowledge of both Python 2.x and 3.x ecosystems. 
        Analyze the provided code samples and dependencies to determine:
        1. The most likely current Python version being used (including Python 2.7 if detected)
        2. The minimum Python version required
        3. Recommended Python version for this codebase
        4. Key evidence supporting your analysis
        
        Look for these indicators:
        - Python 2.x: print statements, xrange(), raw_input(), unicode(), .iterkeys(), import urllib2, etc.
        - Python 3.x: print(), range(), input(), f-strings, type hints, match-case, etc.
        - Version-specific features and their minimum requirements
        
        IMPORTANT: Respond with ONLY valid JSON, no additional text or explanation outside the JSON structure.
        
        Respond in JSON format with:
        {
            "current_version": "X.Y",
            "minimum_version": "X.Y", 
            "recommended_version": "X.Y",
            "confidence": 0.0-1.0,
            "evidence": ["reason1", "reason2", ...],
            "analysis": "detailed explanation",
            "is_python2": true/false
        }"""
    
    @staticmethod
    def get_version_detection_user_prompt(dependencies: Dict[str, Any], code_samples: list) -> str:
        """Get the user prompt for Python version detection"""
        import json
        return f"""
        Please analyze this Python codebase:
        
        DEPENDENCIES:
        {json.dumps(dependencies, indent=2)}
        
        CODE SAMPLES:
        {json.dumps(code_samples, indent=2)}
        
        Provide your analysis in the requested JSON format.
        """
    
    @staticmethod
    def get_migration_analysis_system_prompt(
        migration_type: str, 
        current_version: str, 
        target_version: str,
        is_python2_migration: bool = False
    ) -> str:
        """Get the system prompt for migration issue analysis"""
        
        python2_focus_areas = """PYTHON 2.x TO 3.x MIGRATION - Focus on these critical areas:
        1. Print statements -> print() function
        2. String/Unicode handling changes
        3. Integer division behavior (/ vs //)
        4. Iterator changes (.keys(), .values(), .items())
        5. Import statement changes (urllib2, ConfigParser, etc.)
        6. Exception handling syntax changes
        7. Input/raw_input changes
        8. xrange() -> range() changes"""
        
        python3_focus_areas = """PYTHON 3.x UPGRADE - Focus on these areas:
        1. Deprecated features that will be removed
        2. Syntax changes required
        3. Import changes needed
        4. Behavior changes that could break functionality
        5. Performance implications
        6. New language features compatibility"""
        
        focus_areas = python2_focus_areas if is_python2_migration else python3_focus_areas
        issue_type = 'python2_syntax' if is_python2_migration else 'deprecated_feature'
        
        return f"""You are an expert Python migration specialist with deep expertise in {migration_type} migrations. 
        Analyze the provided code files for potential issues when migrating from Python {current_version} to Python {target_version}.

        {focus_areas}
        
        For each issue found, provide:
        - File path and approximate line number
        - Issue type and severity (critical/major/minor/info)
        - Clear description of the problem
        - Code snippet showing the issue
        - Suggested fix with proper Python {target_version} syntax
        - Educational explanation of why this change is needed
        
        IMPORTANT: Respond with ONLY valid JSON array, no additional text or explanation outside the JSON structure.
        
        Respond in JSON format as an array of issues:
        [
            {{
                "file_path": "path/to/file.py",
                "line_number": 42,
                "issue_type": "{issue_type}",
                "severity": "critical/major/minor/info",
                "description": "Brief description",
                "code_snippet": "problematic code",
                "suggested_fix": "recommended Python {target_version} solution",
                "explanation": "educational explanation",
                "ai_confidence": 0.95
            }}
        ]
        
        If no issues are found, respond with an empty array: []"""
    
    @staticmethod
    def get_migration_analysis_user_prompt(
        file_contents: Dict[str, str], 
        current_version: str, 
        target_version: str
    ) -> str:
        """Get the user prompt for migration issue analysis"""
        import json
        return f"""
        Analyze these Python files for migration issues:
        
        {json.dumps(file_contents, indent=2)}
        
        Current Version: {current_version}
        Target Version: {target_version}
        """
    
    @staticmethod
    def get_code_review_system_prompt(focus_area: str = "general") -> str:
        """Get system prompt for general code review tasks"""
        return f"""You are an expert Python code reviewer with extensive experience in code quality, 
        best practices, and {focus_area} analysis. 
        
        Analyze the provided code and provide constructive feedback focusing on:
        - Code quality and maintainability
        - Performance considerations
        - Security implications
        - Best practices adherence
        - Potential bugs or issues
        
        Provide specific, actionable recommendations with code examples where appropriate.
        """
    
    @staticmethod
    def get_dependency_analysis_system_prompt() -> str:
        """Get system prompt for dependency compatibility analysis"""
        return """You are an expert Python package and dependency specialist with deep knowledge of:
        - Python package ecosystems and compatibility matrices
        - Version conflicts and resolution strategies
        - Migration impact on third-party dependencies
        - Security vulnerabilities in package versions
        
        Analyze the provided dependencies for:
        1. Compatibility with target Python version
        2. Known security vulnerabilities
        3. Deprecated packages with modern alternatives
        4. Version conflicts and resolution suggestions
        5. Migration-specific dependency changes needed
        
        Provide detailed analysis with specific version recommendations and migration steps.
        """
    
    @staticmethod
    def get_risk_assessment_system_prompt() -> str:
        """Get system prompt for migration risk assessment"""
        return """You are an expert project management and technical risk assessment specialist 
        with extensive experience in Python migration projects.
        
        Analyze the migration complexity and provide:
        1. Overall risk level (low/medium/high/very_high)
        2. Effort estimation (hours/days/weeks)
        3. Key risk factors and mitigation strategies
        4. Recommended migration approach and timeline
        5. Testing strategy recommendations
        6. Rollback plan considerations
        
        Base your assessment on:
        - Number and severity of code issues
        - Dependency complexity
        - Project size and complexity
        - Team experience level
        - Business criticality
        """

    @staticmethod
    def get_pyupgrade_system_prompt(target_version: str = "3.11") -> str:
        """Get system prompt for PyUpgrade tool analysis"""
        return f"""You are an expert Python modernization specialist with deep knowledge of Python syntax evolution.
        Analyze the provided Python code and identify opportunities to modernize it to Python {target_version} standards.
        
        Focus on these modernization areas:
        1. String formatting: .format() → f-strings (Python 3.6+)
        2. Type annotations: improve and modernize type hints
        3. Dictionary operations: use modern patterns (Python 3.9+ dict union |)
        4. Union types: Union[A, B] → A | B (Python 3.10+)
        5. Generator expressions and comprehensions optimization
        6. Remove unnecessary compatibility code
        7. Use modern standard library features
        
        For each modernization opportunity, provide:
        - Line number
        - Current code pattern
        - Modernized version
        - Python version requirement
        - Description of improvement
        - Confidence level (0.0-1.0)
        
        IMPORTANT: Respond with ONLY valid JSON, no additional text.
        
        Respond in JSON format:
        {{
            "suggestions": [
                {{
                    "line_number": 42,
                    "old_code": "old pattern",
                    "new_code": "modernized pattern", 
                    "upgrade_type": "f_strings|type_hints|dict_union|etc",
                    "python_version": "3.6",
                    "description": "explanation of modernization",
                    "confidence": 0.95
                }}
            ],
            "summary": "overview of modernizations"
        }}"""

    @staticmethod
    def get_pyupgrade_user_prompt(code: str, target_version: str) -> str:
        """Get user prompt for PyUpgrade tool analysis"""
        return f"""
        Analyze this Python code for modernization opportunities to Python {target_version}:
        
        ```python
        {code}
        ```
        
        Target Version: Python {target_version}
        
        Identify all possible modernizations while maintaining functionality.
        """

    @staticmethod
    def get_python2to3_system_prompt() -> str:
        """Get system prompt for Python 2 to 3 migration analysis"""
        return """You are an expert Python migration specialist with extensive experience in Python 2 to 3 migrations.
        Analyze the provided Python 2 code and identify all issues that need to be fixed for Python 3 compatibility.
        
        Focus on these critical migration areas:
        1. Print statements → print() function calls
        2. String/Unicode handling changes
        3. Integer division behavior (/ vs //)
        4. Iterator method changes (.keys(), .values(), .items())
        5. Import statement updates (urllib2, ConfigParser, etc.)
        6. Exception handling syntax changes (except E, e: → except E as e:)
        7. Input function changes (raw_input → input)
        8. Range function changes (xrange → range)
        9. Dictionary method changes (.iteritems() → .items())
        10. String types and encoding issues
        
        For each issue found, provide:
        - Line number
        - Current Python 2 code
        - Python 3 equivalent
        - Issue type and severity
        - Description of the change needed
        - Confidence level (0.0-1.0)
        
        IMPORTANT: Respond with ONLY valid JSON array, no additional text.
        
        Respond in JSON format:
        {{
            "issues": [
                {{
                    "line_number": 42,
                    "old_code": "python 2 code",
                    "new_code": "python 3 equivalent",
                    "issue_type": "print_statement|string_handling|etc",
                    "severity": "critical|major|minor",
                    "description": "explanation of the change",
                    "confidence": 0.95
                }}
            ],
            "summary": "migration overview"
        }}"""

    @staticmethod
    def get_python2to3_user_prompt(code: str) -> str:
        """Get user prompt for Python 2 to 3 migration analysis"""
        return f"""
        Analyze this Python 2 code for migration to Python 3:
        
        ```python
        {code}
        ```
        
        Identify all Python 2 to 3 compatibility issues that need to be fixed.
        Focus on critical issues that would cause runtime errors in Python 3.
        """

    @staticmethod
    def get_modernize_system_prompt() -> str:
        """Get system prompt for Python 2/3 compatibility modernization"""
        return """You are an expert Python compatibility specialist with deep knowledge of Python 2/3 dual compatibility.
        Analyze the provided Python code and modernize it to work on both Python 2.7+ and Python 3.x.
        
        Focus on these compatibility strategies:
        1. Add appropriate __future__ imports (print_function, division, unicode_literals, absolute_import)
        2. Use six library for cross-version compatibility
        3. Handle string/unicode differences safely
        4. Ensure import compatibility
        5. Use compatible coding patterns
        6. Avoid version-specific features
        
        Compatibility approaches:
        - __future__ imports for language features
        - six library for runtime differences
        - Conditional imports where necessary
        - Compatible string/unicode handling
        
        For each modernization, provide:
        - Line number
        - Current code
        - Compatible version
        - Compatibility mechanism used
        - Description of the change
        - Confidence level (0.0-1.0)
        
        IMPORTANT: Respond with ONLY valid JSON array, no additional text.
        
        Respond in JSON format:
        {{
            "issues": [
                {{
                    "line_number": 42,
                    "old_code": "current code",
                    "new_code": "compatible version",
                    "issue_type": "print_compatibility|string_handling|etc",
                    "compatibility_type": "future_import|six_library|conditional",
                    "description": "explanation of compatibility fix",
                    "confidence": 0.95
                }}
            ],
            "summary": "compatibility overview"
        }}"""

    @staticmethod
    def get_modernize_user_prompt(code: str) -> str:
        """Get user prompt for Python 2/3 compatibility modernization"""
        return f"""
        Modernize this Python code for Python 2.7+ and 3.x compatibility:
        
        ```python
        {code}
        ```
        
        Make the code work on both Python 2.7+ and Python 3.x using appropriate compatibility patterns.
        Prefer __future__ imports and six library usage where applicable.
        """

    @staticmethod
    def get_migration_executor_initial_prompt(analysis_result) -> str:
        """Get the initial LLM prompt for migration executor based on analysis results."""
        
        prompt = f"""You are an expert Python migration assistant. Based on the following analysis results, you need to systematically apply migration tools to upgrade the Python project.

ANALYSIS RESULTS:
- Current Python Version: {analysis_result.current_version.detected_version}
- Target Python Version: {analysis_result.target_version}
- Total Files: {analysis_result.total_files_analyzed}
- Migration Issues Found: {len(analysis_result.migration_issues)}

MIGRATION ISSUES DETECTED:
"""
        
        for i, issue in enumerate(analysis_result.migration_issues, 1):
            severity = getattr(issue, 'severity', 'unknown')
            description = getattr(issue, 'description', 'No description')
            file_path = getattr(issue, 'file_path', 'Unknown file')
            line_number = getattr(issue, 'line_number', 'Unknown line')
            
            prompt += f"{i}. {description}\n"
            prompt += f"   File: {file_path}, Line: {line_number}, Severity: {severity}\n"
        
        prompt += """
AVAILABLE TOOLS:
1. PyUpgradeTool: Modernizes Python code to newer syntax (f-strings, type hints, etc.)
2. Python2To3Tool: Migrates Python 2 code to Python 3
3. ModernizeTool: Creates Python 2/3 compatible code with __future__ imports

INSTRUCTIONS:
1. Analyze the migration issues systematically
2. Choose the most appropriate tool(s) for each issue
3. Apply tools in the correct order (typically: Python2To3Tool first, then PyUpgradeTool, then ModernizeTool if needed)
4. Focus on compilation errors first, then style improvements
5. Be precise and methodical - every change should have a clear purpose
6. After each tool application, the code should be closer to successful compilation

Start by identifying which tool would best address the most critical issues first.
"""
        return prompt

    @staticmethod
    def get_migration_executor_agent_prompt_for_file(py_file, code: str, errors: list, iteration: int) -> str:
        """Create a specific prompt for the agent to work on a file."""
        
        # Find errors related to this file
        file_errors = [
            error for error in errors 
            if error.get("file", "").endswith(py_file.name)
        ]
        
        prompt = f"""You are a Python migration expert. Fix the Python code in file '{py_file.name}' to resolve compilation errors.

CURRENT CODE:
```python
{code}
```

SPECIFIC ERRORS FOR THIS FILE:
"""
        
        if file_errors:
            for i, error in enumerate(file_errors, 1):
                prompt += f"{i}. {error.get('error', 'Unknown error')}\n"
                if 'line' in error:
                    prompt += f"   Line: {error['line']}\n"
        else:
            prompt += "No specific errors found for this file, but it may need general migration fixes.\n"
        
        prompt += f"""
AVAILABLE TOOLS:
- pyupgrade: Modernize Python code syntax (f-strings, type hints, etc.)
- python2to3: Convert Python 2 code to Python 3 syntax
- modernize: Add compatibility imports and patterns

INSTRUCTIONS:
1. Analyze the code and errors carefully
2. Use the appropriate tools to fix the issues
3. Focus on making the code compile successfully
4. Return the final fixed code

Fix the code using the available tools and provide the corrected version.
"""
        
        return prompt


class PromptTemplates:
    """Template strings for dynamic prompt generation"""
    
    MIGRATION_FOCUS_AREAS = {
        'python2_to_3': [
            "Print statements -> print() function",
            "String/Unicode handling changes", 
            "Integer division behavior (/ vs //)",
            "Iterator changes (.keys(), .values(), .items())",
            "Import statement changes (urllib2, ConfigParser, etc.)",
            "Exception handling syntax changes",
            "Input/raw_input changes",
            "xrange() -> range() changes"
        ],
        'python3_upgrade': [
            "Deprecated features that will be removed",
            "Syntax changes required",
            "Import changes needed", 
            "Behavior changes that could break functionality",
            "Performance implications",
            "New language features compatibility"
        ]
    }
    
    SEVERITY_LEVELS = {
        'critical': 'Must be fixed before migration - will cause runtime errors',
        'major': 'Should be fixed - may cause unexpected behavior',
        'minor': 'Recommended to fix - improves code quality',
        'info': 'Informational - no immediate action required'
    }
    
    ISSUE_CATEGORIES = {
        'syntax': 'Syntax changes required for target Python version',
        'deprecated': 'Features deprecated in target version',
        'behavior': 'Behavior changes that may affect functionality',
        'performance': 'Performance-related changes or optimizations',
        'security': 'Security-related improvements or fixes',
        'compatibility': 'Compatibility issues with target version'
    }


# Convenience functions for common prompt combinations
def create_version_detection_messages(dependencies: Dict[str, Any], code_samples: list):
    """Create complete message chain for version detection"""
    from langchain.schema import SystemMessage, HumanMessage
    
    return [
        SystemMessage(content=PromptLibrary.get_version_detection_system_prompt()),
        HumanMessage(content=PromptLibrary.get_version_detection_user_prompt(dependencies, code_samples))
    ]


def create_migration_analysis_messages(
    file_contents: Dict[str, str], 
    current_version: str, 
    target_version: str
):
    """Create complete message chain for migration analysis"""
    from langchain.schema import SystemMessage, HumanMessage
    
    is_python2_migration = current_version.startswith('2.')
    migration_type = "Python 2.x to 3.x" if is_python2_migration else f"Python {current_version} to {target_version}"
    
    return [
        SystemMessage(content=PromptLibrary.get_migration_analysis_system_prompt(
            migration_type, current_version, target_version, is_python2_migration
        )),
        HumanMessage(content=PromptLibrary.get_migration_analysis_user_prompt(
            file_contents, current_version, target_version
        ))
    ]