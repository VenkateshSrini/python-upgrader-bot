#!/usr/bin/env python3
"""
Automated Migration Executor

This module takes the LLM analysis output and automatically executes migration tools
in an iterative process until the project compiles successfully or max iterations reached.
"""

import json
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging
import re

from langchain.agents import initialize_agent, AgentExecutor, create_react_agent
from langchain.agents import AgentType
from langchain.schema import HumanMessage, SystemMessage
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain.memory import ConversationBufferMemory
from langchain import hub

from app_py_version.ai_tools import PyUpgradeTool, Python2To3Tool, ModernizeTool
from app_py_version.version_analyzer import AnalysisResult
from app_py_version.prompt_library import PromptLibrary

logger = logging.getLogger(__name__)


class MigrationExecutor:
    """
    Executes migration tools based on LLM analysis using LangChain agents.
    The LLM decides which tools to use and how to use them.
    """
    
    def __init__(self, max_iterations: int = 5, llm_manager=None):
        self.max_iterations = max_iterations
        self.llm_manager = llm_manager
        
        # Initialize LangChain tools (properly registered)
        self.tools = [
            PyUpgradeTool(),
            Python2To3Tool(), 
            ModernizeTool()
        ]
        
        # Initialize memory for conversation
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Agent will be initialized when needed
        self.agent_executor = None
        
        self.migration_issues = []
        self.successful_fixes = []
    
    def _initialize_agent(self):
        """Initialize the LangChain agent with migration tools."""
        if self.agent_executor is not None:
            return
            
        if not self.llm_manager:
            logger.error("LLM Manager not available - cannot initialize agent")
            return
            
        try:
            # Get the LLM instance
            llm = self.llm_manager.get_llm()
            
            # Create agent with tools (use STRUCTURED_CHAT for multi-input tools)
            self.agent_executor = initialize_agent(
                tools=self.tools,
                llm=llm,
                agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
                memory=self.memory,
                verbose=True,
                max_iterations=3,
                handle_parsing_errors=True,
                return_intermediate_steps=True
            )
            
            logger.info(f"✅ LangChain agent initialized with {len(self.tools)} tools")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize LangChain agent: {e}")
            self.agent_executor = None
    
    def execute_migration(self, analysis_result: AnalysisResult, source_dir: Path, 
                         output_dir: Path) -> Dict[str, Any]:
        """
        Execute migration tools based on analysis results.
        
        Args:
            analysis_result: The analysis result from version analyzer
            source_dir: Source project directory
            output_dir: Output directory for migrated code
            
        Returns:
            Dictionary with execution results
        """
        logger.info(f"Starting migration execution for {source_dir}")
        
        # Initialize the LangChain agent
        self._initialize_agent()
        
        # Create working directory
        working_dir = output_dir / "migrated_code"
        if working_dir.exists():
            shutil.rmtree(working_dir)
        shutil.copytree(source_dir, working_dir)
        
        results = {
            "source_dir": str(source_dir),
            "working_dir": str(working_dir),
            "start_time": datetime.now().isoformat(),
            "iterations": [],
            "final_status": "unknown",
            "successful_fixes": [],
            "unresolved_issues": [],
            "compilation_attempts": 0,
            "agent_available": self.agent_executor is not None
        }
        
        # Initial LLM prompt with analysis results
        initial_prompt = self._create_initial_prompt(analysis_result)
        
        # Execute iterative migration process
        for iteration in range(1, self.max_iterations + 1):
            logger.info(f"Starting iteration {iteration}/{self.max_iterations}")
            
            iteration_result = self._execute_iteration_with_agent(
                iteration, working_dir, initial_prompt, analysis_result
            )
            
            results["iterations"].append(iteration_result)
            results["compilation_attempts"] += iteration_result.get("compilation_attempts", 0)
            
            # Check if compilation is successful
            if iteration_result["compilation_status"] == "success":
                results["final_status"] = "success"
                logger.info(f"Migration completed successfully in iteration {iteration}")
                break
                
            # Check if no progress was made
            if iteration_result["fixes_applied"] == 0:
                logger.warning(f"No fixes applied in iteration {iteration}, stopping")
                break
                
        else:
            results["final_status"] = "max_iterations_reached"
            
        results["end_time"] = datetime.now().isoformat()
        results["successful_fixes"] = self.successful_fixes
        results["unresolved_issues"] = self.migration_issues
        
        # Save migration issues if any
        if self.migration_issues:
            self._save_migration_issues(output_dir)
        
        # Copy final migrated files to output directory
        self._finalize_migrated_files(working_dir, output_dir, results["final_status"])
            
        return results
    
    def _create_initial_prompt(self, analysis_result: AnalysisResult) -> str:
        """Create the initial LLM prompt based on analysis results."""
        return PromptLibrary.get_migration_executor_initial_prompt(analysis_result)
    
    def _execute_iteration_with_agent(self, iteration: int, working_dir: Path, 
                                    initial_prompt: str, analysis_result: AnalysisResult) -> Dict[str, Any]:
        """Execute a single iteration using LangChain agent to decide tool usage."""
        
        iteration_result = {
            "iteration": iteration,
            "start_time": datetime.now().isoformat(),
            "compilation_status": "unknown",
            "compilation_attempts": 0,
            "errors_found": [],
            "fixes_applied": 0,
            "agent_steps": [],
            "tools_used": []
        }
        
        try:
            # First, try to compile the current state
            compilation_result = self._attempt_compilation(working_dir)
            iteration_result["compilation_attempts"] += 1
            iteration_result["compilation_status"] = compilation_result["status"]
            
            if compilation_result["status"] == "success":
                logger.info("Project compiled successfully!")
                return iteration_result
            
            # Extract compilation errors
            errors = compilation_result.get("errors", [])
            iteration_result["errors_found"] = errors
            
            if not errors:
                logger.warning("Compilation failed but no specific errors found")
                return iteration_result
            
            # Use LangChain agent to fix the code
            if self.agent_executor:
                fixes_applied = self._execute_with_langchain_agent(
                    working_dir, errors, iteration, iteration_result
                )
            else:
                # Fallback to manual orchestration
                logger.warning("Agent not available, falling back to manual tool execution")
                fixes_applied = self._execute_manual_fallback(
                    working_dir, errors, iteration_result
                )
            
            iteration_result["fixes_applied"] = fixes_applied
            
            # Try compilation again after fixes
            if fixes_applied > 0:
                final_compilation = self._attempt_compilation(working_dir)
                iteration_result["compilation_attempts"] += 1
                iteration_result["compilation_status"] = final_compilation["status"]
                
                # Track successful fixes
                if final_compilation["status"] == "success":
                    self.successful_fixes.extend(iteration_result["tools_used"])
                elif len(final_compilation.get("errors", [])) < len(errors):
                    # Partial improvement
                    self.successful_fixes.extend(iteration_result["tools_used"])
            
        except Exception as e:
            logger.error(f"Error in iteration {iteration}: {e}")
            iteration_result["error"] = str(e)
        
        iteration_result["end_time"] = datetime.now().isoformat()
        return iteration_result
    
    def _execute_with_langchain_agent(self, working_dir: Path, errors: List[Dict], 
                                    iteration: int, iteration_result: Dict) -> int:
        """Execute migration using LangChain agent to decide tool usage."""
        
        fixes_applied = 0
        
        try:
            # Get Python files from working directory
            python_files = list(working_dir.rglob("*.py"))
            
            for py_file in python_files:
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        original_code = f.read()
                    
                    # Create agent prompt for this file
                    agent_prompt = self._create_agent_prompt_for_file(
                        py_file, original_code, errors, iteration
                    )
                    
                    # Let the agent decide which tools to use and how
                    logger.info(f"🤖 Agent analyzing {py_file.name}...")
                    
                    try:
                        result = self.agent_executor.invoke({
                            "input": agent_prompt
                        })
                        
                        # Extract the modified code from agent result
                        if "output" in result:
                            agent_output = result["output"]
                            logger.debug(f"🔍 Raw agent output for {py_file.name}: {agent_output[:500]}...")
                            
                            modified_code = self._extract_code_from_agent_output(agent_output)
                            
                            if modified_code and modified_code != original_code:
                                # Validate the modified code
                                if self._validate_python_code(modified_code):
                                    with open(py_file, 'w', encoding='utf-8') as f:
                                        f.write(modified_code)
                                    fixes_applied += 1
                                    logger.info(f"✅ Agent successfully modified {py_file.name}")
                                    
                                    # Track tools used (from intermediate steps)
                                    if "intermediate_steps" in result:
                                        for step in result["intermediate_steps"]:
                                            if len(step) >= 2:
                                                action, observation = step
                                                tool_name = getattr(action, 'tool', 'unknown')
                                                iteration_result["agent_steps"].append({
                                                    "tool": tool_name,
                                                    "file": py_file.name,
                                                    "action": str(action),
                                                    "observation": str(observation)[:200]  # Truncate for readability
                                                })
                                else:
                                    logger.warning(f"⚠️ Agent produced invalid Python code for {py_file.name}")
                                    logger.debug(f"🔍 Invalid code: {modified_code[:200]}...")
                            else:
                                logger.info(f"ℹ️ No changes made to {py_file.name}")
                                if not modified_code:
                                    logger.debug(f"🔍 No code extracted from: {agent_output[:300]}...")
                                    # Try fallback if agent completed but we couldn't extract code
                                    logger.info(f"🔧 Agent completed but code extraction failed, trying fallback for {py_file.name}")
                                    if self._apply_fallback_tools(py_file, original_code):
                                        fixes_applied += 1
                                        logger.info(f"✅ Fallback tool application succeeded for {py_file.name}")
                                        iteration_result["tools_used"].append({
                                            "tool": "fallback_after_agent",
                                            "file": py_file.name,
                                            "status": "success"
                                        })
                        else:
                            logger.warning(f"⚠️ No output received from agent for {py_file.name}")
                            logger.debug(f"🔍 Full result keys: {result.keys()}")
                            # Try fallback when no output received
                            logger.info(f"🔧 No agent output received, trying fallback for {py_file.name}")
                            if self._apply_fallback_tools(py_file, original_code):
                                fixes_applied += 1
                                logger.info(f"✅ Fallback tool application succeeded for {py_file.name}")
                                iteration_result["tools_used"].append({
                                    "tool": "fallback_no_output",
                                    "file": py_file.name,
                                    "status": "success"
                                })
                            
                    except Exception as e:
                        logger.error(f"❌ Error processing {py_file.name} with agent: {e}")
                        # If agent fails, try manual tool application as fallback
                        logger.info(f"🔧 Attempting manual tool application for {py_file.name}")
                        if self._apply_fallback_tools(py_file, original_code):
                            fixes_applied += 1
                            logger.info(f"✅ Manual tool application succeeded for {py_file.name}")
                            iteration_result["tools_used"].append({
                                "tool": "fallback_tools",
                                "file": py_file.name,
                                "status": "success"
                            })
                
                except Exception as e:
                    logger.error(f"❌ Error reading/processing {py_file.name}: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"❌ Error in overall agent execution: {e}")
        
        return fixes_applied
    
    def _apply_fallback_tools(self, py_file: Path, original_code: str) -> bool:
        """Apply tools manually as fallback when agent fails."""
        try:
            current_code = original_code
            code_modified = False
            
            # Try Python2To3Tool first for Python 2 code
            if any(pattern in current_code for pattern in ['print ', 'raw_input', 'urllib2', 'ConfigParser', 'cPickle', 'except ', ', e:']):
                logger.info(f"🔧 Applying Python2To3Tool to {py_file.name}")
                python2to3_tool = self.tools[1]  # Python2To3Tool
                result = python2to3_tool.run(current_code)
                modified_code = self._extract_code_from_result(result)
                
                if modified_code and modified_code != current_code:
                    if self._validate_python_code(modified_code):
                        current_code = modified_code
                        code_modified = True
                        logger.info(f"✅ Python2To3Tool applied successfully to {py_file.name}")
            
            # Try PyUpgradeTool for general modernization
            logger.info(f"🔧 Applying PyUpgradeTool to {py_file.name}")
            pyupgrade_tool = self.tools[0]  # PyUpgradeTool
            result = pyupgrade_tool.run(current_code)
            modified_code = self._extract_code_from_result(result)
            
            if modified_code and modified_code != current_code:
                if self._validate_python_code(modified_code):
                    current_code = modified_code
                    code_modified = True
                    logger.info(f"✅ PyUpgradeTool applied successfully to {py_file.name}")
            
            # Try ModernizeTool for additional compatibility (always try it)
            logger.info(f"🔧 Applying ModernizeTool to {py_file.name}")
            modernize_tool = self.tools[2]  # ModernizeTool
            result = modernize_tool.run(current_code)
            modified_code = self._extract_code_from_result(result)
            
            if modified_code and modified_code != current_code:
                if self._validate_python_code(modified_code):
                    current_code = modified_code
                    code_modified = True
                    logger.info(f"✅ ModernizeTool applied successfully to {py_file.name}")
            
            # Write the final modified code if any tool made changes
            if code_modified:
                with open(py_file, 'w', encoding='utf-8') as f:
                    f.write(current_code)
                logger.info(f"✅ Final code written to {py_file.name}")
                return True
                    
        except Exception as e:
            logger.error(f"Error in fallback tool application: {e}")
        
        return False
    
    def _create_agent_prompt_for_file(self, py_file: Path, code: str, 
                                    errors: List[Dict], iteration: int) -> str:
        """Create a specific prompt for the agent to work on a file."""
        return PromptLibrary.get_migration_executor_agent_prompt_for_file(py_file, code, errors, iteration)
    
    def _extract_code_from_agent_output(self, agent_output: str) -> Optional[str]:
        """Extract Python code from agent output."""
        
        # Try to extract from JSON-encoded action_input first (most reliable)
        # Handle different JSON structures that LangChain agent might produce
        json_patterns = [
            # Standard action_input pattern
            r'"action_input":\s*"((?:[^"\\]|\\.)*)(?<!\\)"',
            # Alternative patterns for different LangChain formats
            r'"action_input":\s*"([^"]*(?:\\.[^"]*)*)"',
            # Pattern for Final Answer in JSON
            r'"action":\s*"Final Answer"[^}]*"action_input":\s*"((?:[^"\\]|\\.)*)"',
        ]
        
        for pattern in json_patterns:
            match = re.search(pattern, agent_output, re.DOTALL)
            if match:
                json_content = match.group(1)
                # Decode JSON escapes more thoroughly
                try:
                    import json as json_lib
                    # Try to decode as proper JSON string
                    decoded_content = json_lib.loads(f'"{json_content}"')
                except:
                    # Fallback to manual decoding
                    decoded_content = (json_content
                                     .replace('\\n', '\n')
                                     .replace('\\"', '"')
                                     .replace('\\\\', '\\')
                                     .replace('\\t', '\t')
                                     .replace('\\r', '\r'))
                
                # Now look for code blocks within the decoded content
                code_patterns = [
                    r"```python\n(.*?)\n```",
                    r"```\n(.*?)\n```",
                    # Also try without the trailing newline
                    r"```python\n(.*?)```",
                    r"```\n(.*?)```",
                ]
                
                for code_pattern in code_patterns:
                    code_match = re.search(code_pattern, decoded_content, re.DOTALL)
                    if code_match:
                        code = code_match.group(1).strip()
                        if code and self._validate_python_code(code):
                            logger.info(f"✓ Extracted code from JSON action_input using pattern: {pattern[:30]}...")
                            return code
        
        # Look for code blocks in different formats (including Final Answer)
        patterns = [
            # Standard code blocks
            r"```python\n(.*?)\n```",
            r"```\n(.*?)\n```",
            
            # Labeled code blocks
            r"FIXED CODE:\s*```python\n(.*?)\n```",
            r"RESULT:\s*```python\n(.*?)\n```",
            r"CORRECTED VERSION:\s*```python\n(.*?)\n```",
            r"MIGRATED CODE:\s*```python\n(.*?)\n```",
            
            # Final Answer pattern (common in LangChain agent responses)
            r"Final Answer.*?```python\n(.*?)\n```",
            
            # Code within final answer text blocks
            r"Here's the corrected version.*?```python\n(.*?)\n```",
            r"Here's the final code.*?```python\n(.*?)\n```",
            r"Here's the corrected Python 3 code.*?```python\n(.*?)\n```",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, agent_output, re.DOTALL | re.IGNORECASE)
            if match:
                code = match.group(1).strip()
                if code and self._validate_python_code(code):
                    logger.info(f"✓ Extracted code using pattern: {pattern[:50]}...")
                    return code
        
        # Try extracting from tool output in the agent response
        tool_output_patterns = [
            r"Observation:\s*.*?```python\n(.*?)\n```",
        ]
        
        for pattern in tool_output_patterns:
            match = re.search(pattern, agent_output, re.DOTALL | re.IGNORECASE)
            if match:
                code = match.group(1).strip()
                if code and self._validate_python_code(code):
                    logger.info(f"✓ Extracted code from tool observation")
                    return code
        
        # If no clear code block, try to find Python-like content
        lines = agent_output.split('\n')
        code_lines = []
        in_code = False
        start_indicators = ['#!/usr/bin/env python', 'def ', 'class ', 'import ', 'from ']
        
        for line in lines:
            stripped_line = line.strip()
            
            # Start collecting code when we see Python indicators
            if any(indicator in line for indicator in start_indicators):
                in_code = True
                code_lines.append(line)
            elif in_code:
                # Continue collecting if it looks like Python code
                if (stripped_line == '' or 
                    line.startswith('    ') or line.startswith('\t') or  # Indented
                    stripped_line.startswith('#') or  # Comments
                    any(keyword in stripped_line for keyword in ['if ', 'else:', 'elif ', 'for ', 'while ', 'try:', 'except', 'finally:', 'with ', 'return', 'yield', 'pass', 'break', 'continue'])):
                    code_lines.append(line)
                elif stripped_line and not any(char in stripped_line for char in ['*', '-', '✅', '🔧', '⚠️', '#']):
                    # Looks like more Python code
                    code_lines.append(line)
                else:
                    # End of code block
                    break
        
        if code_lines:
            code = '\n'.join(code_lines)
            if self._validate_python_code(code):
                logger.info(f"✓ Extracted code from heuristic parsing")
                return code
        
        logger.warning("⚠️ Could not extract valid Python code from agent output")
        
        # Enhanced debugging - look for any code-like patterns
        if "```python" in agent_output.lower():
            logger.info("🔍 Found ```python marker but extraction failed")
            # Try a very permissive pattern
            permissive_match = re.search(r'```python\s*(.*?)\s*```', agent_output, re.DOTALL | re.IGNORECASE)
            if permissive_match:
                potential_code = permissive_match.group(1).strip()
                logger.info(f"🔍 Permissive extraction found: {potential_code[:100]}...")
                if self._validate_python_code(potential_code):
                    logger.info("✓ Permissive extraction succeeded!")
                    return potential_code
                else:
                    logger.warning("⚠️ Permissive extraction failed validation")
        
        logger.debug(f"🔍 Agent output sample: {agent_output[:500]}...")
        return None
    
    def _validate_python_code(self, code: str) -> bool:
        """Validate that the code is syntactically correct Python."""
        try:
            compile(code, '<string>', 'exec')
            return True
        except SyntaxError:
            return False
        except Exception:
            return False
    
    def _execute_manual_fallback(self, working_dir: Path, errors: List[Dict], 
                                iteration_result: Dict) -> int:
        """Fallback manual tool execution when agent is not available."""
        
        fixes_applied = 0
        
        # Simple rule-based tool selection
        tool_sequence = []
        
        # Check for Python 2 patterns
        if any('print' in str(error) or 'raw_input' in str(error) for error in errors):
            tool_sequence.append(self.tools[1])  # Python2To3Tool
        
        # Always try pyupgrade for modernization
        tool_sequence.append(self.tools[0])  # PyUpgradeTool
        
        # Try modernize for compatibility
        if any('import' in str(error) for error in errors):
            tool_sequence.append(self.tools[2])  # ModernizeTool
        
        # Apply tools in sequence
        for tool in tool_sequence:
            logger.info(f"Applying {tool.name} to project files")
            
            python_files = list(working_dir.rglob("*.py"))
            files_modified = 0
            
            for py_file in python_files:
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        original_code = f.read()
                    
                    # Apply the tool
                    result = tool.run(original_code)
                    
                    # Extract the modified code from the result
                    modified_code = self._extract_code_from_result(result)
                    
                    if modified_code and modified_code != original_code:
                        with open(py_file, 'w', encoding='utf-8') as f:
                            f.write(modified_code)
                        files_modified += 1
                        logger.info(f"Modified {py_file.name} with {tool.name}")
                        
                except Exception as e:
                    logger.error(f"Error applying {tool.name} to {py_file}: {e}")
            
            if files_modified > 0:
                fixes_applied += files_modified
                iteration_result["tools_used"].append({
                    "tool": tool.name,
                    "files_modified": files_modified
                })
        
        return fixes_applied
    
# Legacy method - replaced by _execute_iteration_with_agent
    
    def _attempt_compilation(self, working_dir: Path) -> Dict[str, Any]:
        """Attempt to compile the Python project."""
        
        compilation_result = {
            "status": "unknown",
            "errors": [],
            "output": ""
        }
        
        try:
            # Find Python files to compile
            python_files = list(working_dir.rglob("*.py"))
            if not python_files:
                compilation_result["status"] = "no_python_files"
                return compilation_result
            
            errors = []
            
            # Try to compile each Python file
            for py_file in python_files:
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        code = f.read()
                    
                    # Use ast.parse to check for syntax errors
                    compile(code, str(py_file), 'exec')
                    
                except SyntaxError as e:
                    error_info = {
                        "file": str(py_file.relative_to(working_dir)),
                        "line": e.lineno,
                        "error": str(e),
                        "type": "syntax_error"
                    }
                    errors.append(error_info)
                    
                except Exception as e:
                    error_info = {
                        "file": str(py_file.relative_to(working_dir)),
                        "error": str(e),
                        "type": "compilation_error"
                    }
                    errors.append(error_info)
            
            if errors:
                compilation_result["status"] = "failed"
                compilation_result["errors"] = errors
            else:
                compilation_result["status"] = "success"
                
        except Exception as e:
            compilation_result["status"] = "error"
            compilation_result["errors"] = [{"error": str(e), "type": "system_error"}]
        
        return compilation_result
    
# Old methods removed - now using LangChain agent for tool orchestration
    
    def _extract_code_from_result(self, result: str) -> Optional[str]:
        """Extract the actual code from tool result."""
        
        # Look for code blocks in the result
        code_pattern = r"```python\n(.*?)\n```"
        match = re.search(code_pattern, result, re.DOTALL)
        
        if match:
            return match.group(1)
        
        # If no code block found, check if the result looks like code
        lines = result.split('\n')
        code_lines = []
        in_code_section = False
        
        for line in lines:
            if line.strip().startswith('```python'):
                in_code_section = True
                continue
            elif line.strip() == '```' and in_code_section:
                break
            elif in_code_section:
                code_lines.append(line)
        
        if code_lines:
            return '\n'.join(code_lines)
        
        return None
    
    def _save_migration_issues(self, output_dir: Path):
        """Save unresolved migration issues to file."""
        
        issues_file = output_dir / "migration_issues.md"
        
        with open(issues_file, 'w', encoding='utf-8') as f:
            f.write("# Unresolved Migration Issues\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"Maximum iterations reached: {self.max_iterations}\n\n")
            
            if self.migration_issues:
                f.write("## Issues that could not be automatically resolved:\n\n")
                for i, issue in enumerate(self.migration_issues, 1):
                    f.write(f"### {i}. {issue.get('error', 'Unknown error')}\n")
                    f.write(f"- **File:** {issue.get('file', 'Unknown')}\n")
                    f.write(f"- **Type:** {issue.get('type', 'Unknown')}\n")
                    if 'line' in issue:
                        f.write(f"- **Line:** {issue['line']}\n")
                    f.write("\n")
            else:
                f.write("No unresolved issues logged.\n")
        
        logger.info(f"Migration issues saved to {issues_file}")
    
    def _finalize_migrated_files(self, working_dir: Path, output_dir: Path, status: str):
        """Copy final migrated files to output directory with proper structure."""
        
        try:
            # Create final output directory
            final_dir = output_dir / "final_migrated_code"
            if final_dir.exists():
                shutil.rmtree(final_dir)
            
            # Copy all migrated files to final directory
            shutil.copytree(working_dir, final_dir)
            
            # Create status file
            status_file = output_dir / "migration_status.txt"
            with open(status_file, 'w', encoding='utf-8') as f:
                f.write(f"Migration Status: {status}\n")
                f.write(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Final migrated code location: {final_dir.absolute()}\n")
                
                if status == "success":
                    f.write("\n✅ Migration completed successfully!\n")
                    f.write("All Python files should now be compatible with the target version.\n")
                else:
                    f.write(f"\n⚠️ Migration completed with status: {status}\n")
                    f.write("Some issues may remain - check migration_issues.md for details.\n")
            
            logger.info(f"Final migrated files saved to {final_dir}")
            logger.info(f"Migration status saved to {status_file}")
            
            # Create summary of migrated files
            self._create_migration_summary(final_dir, output_dir)
            
        except Exception as e:
            logger.error(f"Error finalizing migrated files: {e}")
    
    def _create_migration_summary(self, final_dir: Path, output_dir: Path):
        """Create a summary of migrated files."""
        
        summary_file = output_dir / "migrated_files_summary.md"
        
        try:
            python_files = list(final_dir.rglob("*.py"))
            
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write("# Migrated Files Summary\n\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(f"## Final migrated code location: `{final_dir.absolute()}`\n\n")
                f.write(f"## Python files migrated: {len(python_files)}\n\n")
                
                if python_files:
                    f.write("### Files processed:\n")
                    for py_file in sorted(python_files):
                        rel_path = py_file.relative_to(final_dir)
                        f.write(f"- `{rel_path}`\n")
                    f.write("\n")
                
                f.write("## Next Steps\n\n")
                f.write("1. Review the migrated code in the final directory\n")
                f.write("2. Test your application with the target Python version\n")
                f.write("3. Check migration_status.txt for overall status\n")
                f.write("4. If issues remain, review migration_issues.md\n")
                f.write("5. Run your test suite to ensure functionality is preserved\n\n")
                
                f.write("## Backup\n\n")
                f.write("- Original source code remains unchanged\n")
                f.write("- Working migration files are in `migrated_code/` directory\n")
                f.write("- Final clean migrated files are in `final_migrated_code/` directory\n")
            
            logger.info(f"Migration summary saved to {summary_file}")
            
        except Exception as e:
            logger.error(f"Error creating migration summary: {e}")


def safe_print(message):
    """Safely print messages, handling Unicode issues on Windows"""
    try:
        print(message)
    except UnicodeEncodeError:
        # Remove emojis for Windows compatibility
        emoji_pattern = re.compile("["
                                  u"\U0001F600-\U0001F64F"  # emoticons
                                  u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                                  u"\U0001F680-\U0001F6FF"  # transport & map symbols
                                  u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                                  u"\U00002702-\U000027B0"
                                  u"\U000024C2-\U0001F251"
                                  "]+", flags=re.UNICODE)
        clean_message = emoji_pattern.sub('', message)
        print(clean_message)