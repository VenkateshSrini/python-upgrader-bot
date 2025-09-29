#!/usr/bin/env python3
"""
AI-Powered Python Version Analyzer

This module uses LLM to intelligently analyze Python applications and identify:
- Current Python version requirements
- Potential migration issues to target versions
- Code patterns that need attention
- Dependency compatibility concerns
- Risk assessment for upgrades

Author: Your AI Python Upgrade Assistant
"""

import os
import sys
import ast
import re
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

# Load configuration from centralized manager
from .config_manager import load_config

# Import our LLM manager and prompt library
try:
    from ..llm_manager import LLMManager
    from .prompt_library import PromptLibrary, create_version_detection_messages, create_migration_analysis_messages
except ImportError:
    # Fallback for direct execution
    sys.path.append(str(Path(__file__).parent.parent))
    from llm_manager import LLMManager
    sys.path.append(str(Path(__file__).parent))
    from prompt_library import PromptLibrary, create_version_detection_messages, create_migration_analysis_messages
from langchain.schema import HumanMessage, SystemMessage

# Load configuration from both .env.keys and .env.config
load_config()

# Configure logging with UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('version_analyzer.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Helper function to safely log with emojis
def safe_log(level, message):
    """Safely log messages, falling back to ASCII if Unicode fails"""
    try:
        getattr(logger, level)(message)
    except UnicodeEncodeError:
        # Remove emojis and special characters for Windows compatibility
        import re
        ascii_message = re.sub(r'[^\x00-\x7F]+', '', message)
        getattr(logger, level)(ascii_message)


@dataclass
class PythonVersionInfo:
    """Information about Python version requirements and compatibility"""
    detected_version: Optional[str] = None
    minimum_version: Optional[str] = None
    recommended_version: Optional[str] = None
    confidence_score: float = 0.0
    detection_method: str = ""
    evidence: List[str] = None
    
    def __post_init__(self):
        if self.evidence is None:
            self.evidence = []


@dataclass
class MigrationIssue:
    """Represents a potential issue when migrating Python versions"""
    file_path: str
    line_number: int
    issue_type: str
    severity: str  # 'critical', 'major', 'minor', 'info'
    description: str
    code_snippet: str
    suggested_fix: Optional[str] = None
    explanation: Optional[str] = None
    ai_confidence: float = 0.0


@dataclass
class AnalysisResult:
    """Complete analysis result for the application"""
    project_path: str
    current_version: PythonVersionInfo
    target_version: str
    total_files_analyzed: int
    migration_issues: List[MigrationIssue]
    dependency_issues: List[Dict[str, Any]]
    risk_assessment: Dict[str, Any]
    recommendations: List[str]
    analysis_timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'project_path': self.project_path,
            'current_version': asdict(self.current_version),
            'target_version': self.target_version,
            'total_files_analyzed': self.total_files_analyzed,
            'migration_issues': [asdict(issue) for issue in self.migration_issues],
            'dependency_issues': self.dependency_issues,
            'risk_assessment': self.risk_assessment,
            'recommendations': self.recommendations,
            'analysis_timestamp': self.analysis_timestamp
        }


class PythonVersionAnalyzer:
    """AI-powered Python version analyzer using LLM for intelligent assessment"""
    
    def __init__(self, target_version: Optional[str] = None):
        """Initialize the analyzer with LLM support"""
        self.llm_manager = LLMManager()
        self.target_version = target_version or self._load_target_version_from_env()
        self.python_files = []
        self.analysis_cache = {}
        
        safe_log("info", f"🚀 Python Version Analyzer initialized")
        safe_log("info", f"🎯 Target version: {self.target_version}")
        safe_log("info", f"🤖 LLM Provider: {self.llm_manager.get_provider_info()['provider']}")
    
    def _load_target_version_from_env(self) -> str:
        """Load target Python version from environment variables (loaded via dotenv)"""
        target_version = os.getenv('TARGET_PYTHON_VERSION', '3.11')
        logger.info(f"📄 Target version loaded from environment: {target_version}")
        return target_version
    
    def discover_python_files(self, project_path: Path) -> List[Path]:
        """Discover all Python files in the project"""
        python_files = []
        
        # Patterns to exclude
        exclude_patterns = {
            '.venv', 'venv', '__pycache__', '.git', 'build', 'dist', 
            '.pytest_cache', '.mypy_cache', 'node_modules', '.tox'
        }
        
        for file_path in project_path.rglob("*.py"):
            # Skip excluded directories
            if any(pattern in file_path.parts for pattern in exclude_patterns):
                continue
            python_files.append(file_path)
        
        safe_log("info", f"🔍 Discovered {len(python_files)} Python files")
        return python_files
    
    def detect_current_python_version(self, project_path: Path) -> PythonVersionInfo:
        """Detect the current Python version requirements using multiple methods"""
        version_info = PythonVersionInfo()
        evidence = []
        detection_methods = []
        
        # Method 1: Check setup.py, pyproject.toml, requirements.txt
        version_from_config = self._check_config_files(project_path)
        if version_from_config:
            version_info.detected_version = version_from_config
            evidence.append(f"Found in configuration files: {version_from_config}")
            detection_methods.append("config_files")
        
        # Method 2: Analyze code syntax using AST
        version_from_syntax = self._analyze_syntax_features(project_path)
        if version_from_syntax:
            if not version_info.detected_version or version_from_syntax > version_info.detected_version:
                version_info.minimum_version = version_from_syntax
                evidence.append(f"Minimum version from syntax analysis: {version_from_syntax}")
                detection_methods.append("syntax_analysis")
        
        # Method 3: Check shebang lines
        version_from_shebang = self._check_shebang_lines(project_path)
        if version_from_shebang:
            evidence.append(f"Found in shebang lines: {version_from_shebang}")
            detection_methods.append("shebang")
        
        # Method 4: Use AI to analyze the codebase
        ai_analysis = self._ai_version_detection(project_path)
        if ai_analysis:
            version_info.recommended_version = ai_analysis.get('recommended_version')
            version_info.confidence_score = ai_analysis.get('confidence', 0.0)
            evidence.extend(ai_analysis.get('evidence', []))
            detection_methods.append("ai_analysis")
        
        version_info.evidence = evidence
        version_info.detection_method = ", ".join(detection_methods)
        
        # Final determination
        if not version_info.detected_version and version_info.minimum_version:
            version_info.detected_version = version_info.minimum_version
        
        safe_log("info", f"🔍 Version Detection Results:")
        logger.info(f"   Detected: {version_info.detected_version}")
        logger.info(f"   Minimum: {version_info.minimum_version}")
        logger.info(f"   Recommended: {version_info.recommended_version}")
        logger.info(f"   Confidence: {version_info.confidence_score:.2f}")
        
        return version_info
    
    def _check_config_files(self, project_path: Path) -> Optional[str]:
        """Check configuration files for Python version requirements"""
        config_files = {
            'setup.py': self._parse_setup_py,
            'pyproject.toml': self._parse_pyproject_toml,
            'requirements.txt': self._parse_requirements_txt,
            'Pipfile': self._parse_pipfile,
            'runtime.txt': self._parse_runtime_txt
        }
        
        for filename, parser in config_files.items():
            file_path = project_path / filename
            if file_path.exists():
                try:
                    version = parser(file_path)
                    if version:
                        logger.info(f"📄 Found Python version in {filename}: {version}")
                        return version
                except Exception as e:
                    logger.warning(f"⚠️ Error parsing {filename}: {e}")
        
        return None
    
    def _parse_setup_py(self, file_path: Path) -> Optional[str]:
        """Parse setup.py for python_requires"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Look for python_requires
        match = re.search(r"python_requires\s*=\s*['\"]([^'\"]+)['\"]", content)
        if match:
            return self._extract_version_from_specifier(match.group(1))
        
        return None
    
    def _parse_pyproject_toml(self, file_path: Path) -> Optional[str]:
        """Parse pyproject.toml for Python version"""
        try:
            import tomli
        except ImportError:
            try:
                import tomllib as tomli  # Python 3.11+ built-in
            except ImportError:
                logger.warning("📦 tomli/tomllib not available, cannot parse pyproject.toml")
                return None
        
        with open(file_path, 'rb') as f:
            data = tomli.load(f)
        
        # Check different locations
        if 'project' in data and 'requires-python' in data['project']:
            return self._extract_version_from_specifier(data['project']['requires-python'])
        
        if 'tool' in data and 'poetry' in data['tool'] and 'dependencies' in data['tool']['poetry']:
            python_req = data['tool']['poetry']['dependencies'].get('python')
            if python_req:
                return self._extract_version_from_specifier(python_req)
        
        return None
    
    def _parse_requirements_txt(self, file_path: Path) -> Optional[str]:
        """Parse requirements.txt for Python version hints"""
        # This is less reliable but can provide hints
        return None
    
    def _parse_pipfile(self, file_path: Path) -> Optional[str]:
        """Parse Pipfile for Python version"""
        try:
            import tomli
        except ImportError:
            try:
                import tomllib as tomli  # Python 3.11+ built-in
            except ImportError:
                logger.warning("📦 tomli/tomllib not available, cannot parse Pipfile")
                return None
        
        with open(file_path, 'rb') as f:
            data = tomli.load(f)
        
        if 'requires' in data and 'python_version' in data['requires']:
            return data['requires']['python_version']
        
        return None
    
    def _parse_runtime_txt(self, file_path: Path) -> Optional[str]:
        """Parse runtime.txt (Heroku-style) for Python version"""
        with open(file_path, 'r') as f:
            content = f.read().strip()
        
        match = re.search(r'python-(\d+\.\d+(?:\.\d+)?)', content)
        if match:
            return match.group(1)
        
        return None
    
    def _extract_version_from_specifier(self, specifier: str) -> Optional[str]:
        """Extract version number from requirement specifier like '>=3.8' """
        # Remove common operators and extract version
        version_match = re.search(r'(\d+\.\d+(?:\.\d+)?)', specifier)
        if version_match:
            return version_match.group(1)
        return None
    
    def _analyze_syntax_features(self, project_path: Path) -> Optional[str]:
        """Analyze code syntax to determine minimum Python version"""
        python_files = self.discover_python_files(project_path)
        max_version_needed = (2, 7)  # Start with Python 2.7 as minimum
        detected_python2 = False
        
        # Python 2.x indicators (if found, likely Python 2.x codebase)
        python2_indicators = [
            'print ', 'print\t', 'print\n',  # print statements (not function calls)
            'raw_input(', 'xrange(', 'unicode(',
            '.iterkeys()', '.itervalues()', '.iteritems()',
            'file(', 'execfile(', 'reload(',
            'import ConfigParser', 'import cPickle', 'import urllib2',
            '__nonzero__', 'has_key(', '.encode("string-escape")'
        ]
        
        # Version-specific features to look for (Python 3.x)
        feature_versions = {
            (3, 0): ['print(', 'input(', 'range('],  # Python 3 basics
            (3, 6): ['f"', "f'"],  # f-strings
            (3, 8): [':='],  # Walrus operator
            (3, 9): ['dict | dict', 'list[', 'dict[', 'tuple['],  # Dict union, generic types
            (3, 10): ['match ', 'case '],  # Match-case statements
            (3, 11): ['except*'],  # Exception groups
            (3, 12): ['type ', '@override']  # Type statement, override decorator
        }
        
        for file_path in python_files[:10]:  # Sample first 10 files for performance
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for Python 2.x indicators first
                for indicator in python2_indicators:
                    if indicator in content:
                        # Additional validation for print statements (avoid false positives)
                        if indicator.startswith('print '):
                            # Check if it's really a print statement, not a function call
                            if re.search(r'\bprint\s+[^(]', content):
                                detected_python2 = True
                                max_version_needed = (2, 7)
                                logger.debug(f"Found Python 2.x indicator '{indicator}' in {file_path}")
                                break
                        else:
                            detected_python2 = True
                            max_version_needed = (2, 7)
                            logger.debug(f"Found Python 2.x indicator '{indicator}' in {file_path}")
                            break
                
                # If not Python 2.x, check for Python 3.x features
                if not detected_python2:
                    for version, features in feature_versions.items():
                        for feature in features:
                            if feature in content:
                                if version > max_version_needed:
                                    max_version_needed = version
                                    logger.debug(f"Found {feature} in {file_path}, needs Python {version[0]}.{version[1]}+")
                
            except Exception as e:
                logger.debug(f"Could not analyze {file_path}: {e}")
        
        # Return the detected version
        if max_version_needed >= (2, 7):
            return f"{max_version_needed[0]}.{max_version_needed[1]}"
        
        return None
    
    def _check_shebang_lines(self, project_path: Path) -> Optional[str]:
        """Check shebang lines for Python version hints"""
        python_files = self.discover_python_files(project_path)
        
        for file_path in python_files[:5]:  # Check first few files
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    first_line = f.readline().strip()
                
                if first_line.startswith('#!') and 'python' in first_line:
                    # Extract version from shebang like #!/usr/bin/python2.7 or #!/usr/bin/python3.9
                    version_match = re.search(r'python(\d+(?:\.\d+)?)', first_line)
                    if version_match:
                        version = version_match.group(1)
                        # Handle cases like 'python2' -> '2.7', 'python3' -> '3.0'
                        if version == '2':
                            return '2.7'
                        elif version == '3':
                            return '3.0'
                        else:
                            return version
                    
                    # Check for plain 'python' which might indicate Python 2.x in older systems
                    if re.search(r'\bpython\b(?!\d)', first_line):
                        logger.debug(f"Found plain 'python' shebang in {file_path}, might be Python 2.x")
                        
            except Exception as e:
                logger.debug(f"Could not check shebang in {file_path}: {e}")
        
        return None
    
    def _ai_version_detection(self, project_path: Path) -> Optional[Dict[str, Any]]:
        """Use AI to analyze the codebase and recommend Python version"""
        try:
            # Get a sample of the codebase
            code_samples = self._get_code_samples(project_path)
            dependencies = self._get_dependencies(project_path)
            
            # Create AI prompt for version analysis using prompt library
            llm = self.llm_manager.get_llm()
            messages = create_version_detection_messages(dependencies, code_samples)
            
            response = llm.invoke(messages)
            
            # Parse AI response
            try:
                # First try direct JSON parsing
                ai_result = json.loads(response.content)
                logger.info(f"🤖 AI Analysis: {ai_result.get('analysis', 'No detailed analysis')}")
                return ai_result
            except json.JSONDecodeError:
                # Try to extract JSON from text response
                try:
                    import re
                    # Look for JSON block in the response
                    json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
                    if json_match:
                        ai_result = json.loads(json_match.group())
                        logger.info(f"🤖 AI Analysis (extracted): {ai_result.get('analysis', 'No detailed analysis')}")
                        return ai_result
                    else:
                        logger.warning(f"⚠️ Could not find JSON in AI response: {response.content[:200]}...")
                        return None
                except json.JSONDecodeError as e:
                    logger.warning(f"⚠️ Could not parse AI response as JSON: {e}")
                    logger.debug(f"Response content: {response.content[:500]}...")
                    return None
                
        except Exception as e:
            logger.error(f"❌ AI analysis failed: {e}")
            return None
    
    def _get_code_samples(self, project_path: Path, max_samples: int = 5) -> List[Dict[str, str]]:
        """Get representative code samples from the project"""
        python_files = self.discover_python_files(project_path)
        samples = []
        
        for file_path in python_files[:max_samples]:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Get first 50 lines or 2000 characters, whichever is smaller
                lines = content.splitlines()[:50]
                sample_content = '\n'.join(lines)[:2000]
                
                samples.append({
                    'file': str(file_path.relative_to(project_path)),
                    'content': sample_content
                })
                
            except Exception as e:
                logger.debug(f"Could not sample {file_path}: {e}")
        
        return samples
    
    def _get_dependencies(self, project_path: Path) -> Dict[str, Any]:
        """Extract project dependencies"""
        dependencies = {
            'requirements': [],
            'setup_py': [],
            'pyproject_toml': [],
            'pipfile': []
        }
        
        # Check requirements.txt
        req_file = project_path / 'requirements.txt'
        if req_file.exists():
            try:
                with open(req_file, 'r') as f:
                    dependencies['requirements'] = [
                        line.strip() for line in f 
                        if line.strip() and not line.startswith('#')
                    ]
            except Exception as e:
                logger.debug(f"Could not read requirements.txt: {e}")
        
        # Add other dependency sources as needed
        return dependencies
    
    def analyze_migration_issues(self, project_path: Path, current_version: str) -> List[MigrationIssue]:
        """Analyze potential migration issues using AI"""
        issues = []
        python_files = self.discover_python_files(project_path)
        
        logger.info(f"🔍 Analyzing migration issues from Python {current_version} to {self.target_version}")
        
        # Analyze files in batches for better performance
        batch_size = 5
        for i in range(0, min(len(python_files), 20), batch_size):  # Limit to first 20 files
            batch_files = python_files[i:i+batch_size]
            batch_issues = self._analyze_file_batch(batch_files, current_version, project_path)
            issues.extend(batch_issues)
        
        logger.info(f"🚨 Found {len(issues)} potential migration issues")
        return issues
    
    def _analyze_file_batch(self, files: List[Path], current_version: str, project_path: Path) -> List[MigrationIssue]:
        """Analyze a batch of files for migration issues"""
        try:
            # Prepare code content for analysis
            file_contents = {}
            for file_path in files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    file_contents[str(file_path.relative_to(project_path))] = content[:5000]  # Limit content size
                except Exception as e:
                    logger.debug(f"Could not read {file_path}: {e}")
            
            if not file_contents:
                return []
            
            # AI prompt for migration analysis using prompt library
            llm = self.llm_manager.get_llm()
            messages = create_migration_analysis_messages(file_contents, current_version, self.target_version)
            
            response = llm.invoke(messages)
            
            # Parse AI response
            try:
                # First try direct JSON parsing
                issues_data = json.loads(response.content)
                issues = []
                
                for issue_data in issues_data:
                    issue = MigrationIssue(
                        file_path=issue_data.get('file_path', ''),
                        line_number=issue_data.get('line_number', 0),
                        issue_type=issue_data.get('issue_type', 'unknown'),
                        severity=issue_data.get('severity', 'info'),
                        description=issue_data.get('description', ''),
                        code_snippet=issue_data.get('code_snippet', ''),
                        suggested_fix=issue_data.get('suggested_fix'),
                        explanation=issue_data.get('explanation'),
                        ai_confidence=issue_data.get('ai_confidence', 0.0)
                    )
                    issues.append(issue)
                
                return issues
                
            except json.JSONDecodeError as e:
                # Try to extract JSON array from text response
                try:
                    import re
                    # Look for JSON array in the response (improved regex)
                    # First try to find complete JSON array
                    json_match = re.search(r'```json\s*(\[.*?\])\s*```', response.content, re.DOTALL)
                    if not json_match:
                        # Fallback to simple array pattern
                        json_match = re.search(r'(\[.*?\])', response.content, re.DOTALL)
                    
                    if json_match:
                        json_text = json_match.group(1) if json_match.groups() else json_match.group()
                        issues_data = json.loads(json_text)
                        issues = []
                        for issue_data in issues_data:
                            issue = MigrationIssue(
                                file_path=issue_data.get('file_path', ''),
                                line_number=issue_data.get('line_number', 0),
                                issue_type=issue_data.get('issue_type', 'unknown'),
                                severity=issue_data.get('severity', 'info'),
                                description=issue_data.get('description', ''),
                                code_snippet=issue_data.get('code_snippet', ''),
                                suggested_fix=issue_data.get('suggested_fix'),
                                explanation=issue_data.get('explanation'),
                                ai_confidence=issue_data.get('ai_confidence', 0.0)
                            )
                            issues.append(issue)
                        return issues
                    else:
                        logger.warning(f"⚠️ Could not find JSON array in migration analysis: {response.content[:200]}...")
                        return []
                except json.JSONDecodeError as nested_e:
                    logger.warning(f"⚠️ Could not parse AI migration analysis: {e}")
                    logger.debug(f"Response content: {response.content[:500]}...")
                    return []
                
        except Exception as e:
            logger.error(f"❌ Migration analysis failed: {e}")
            return []
    
    def analyze_project(self, project_path: str) -> AnalysisResult:
        """Main method to analyze the entire project"""
        project_path = Path(project_path).resolve()
        
        safe_log("info", f"🚀 Starting comprehensive analysis of: {project_path}")
        safe_log("info", f"🎯 Target Python version: {self.target_version}")
        
        # Step 1: Discover Python files
        self.python_files = self.discover_python_files(project_path)
        
        # Step 2: Detect current Python version
        current_version_info = self.detect_current_python_version(project_path)
        
        # Step 3: Analyze migration issues
        migration_issues = []
        if current_version_info.detected_version:
            migration_issues = self.analyze_migration_issues(
                project_path, 
                current_version_info.detected_version
            )
        
        # Step 4: Analyze dependencies (placeholder for now)
        dependency_issues = []
        
        # Step 5: Generate risk assessment and recommendations
        risk_assessment = self._generate_risk_assessment(current_version_info, migration_issues)
        recommendations = self._generate_recommendations(current_version_info, migration_issues)
        
        # Create analysis result
        result = AnalysisResult(
            project_path=str(project_path),
            current_version=current_version_info,
            target_version=self.target_version,
            total_files_analyzed=len(self.python_files),
            migration_issues=migration_issues,
            dependency_issues=dependency_issues,
            risk_assessment=risk_assessment,
            recommendations=recommendations,
            analysis_timestamp=datetime.now().isoformat()
        )
        
        logger.info(f"✅ Analysis complete!")
        logger.info(f"   📁 Files analyzed: {result.total_files_analyzed}")
        logger.info(f"   🚨 Issues found: {len(result.migration_issues)}")
        logger.info(f"   ⚠️ Risk level: {result.risk_assessment.get('overall_risk', 'unknown')}")
        
        return result
    
    def _generate_risk_assessment(self, version_info: PythonVersionInfo, issues: List[MigrationIssue]) -> Dict[str, Any]:
        """Generate risk assessment for the migration"""
        critical_issues = [i for i in issues if i.severity == 'critical']
        major_issues = [i for i in issues if i.severity == 'major']
        minor_issues = [i for i in issues if i.severity == 'minor']
        
        # Check if this is a Python 2.x to 3.x migration
        is_python2_migration = (version_info.detected_version and 
                               version_info.detected_version.startswith('2.') and 
                               self.target_version.startswith('3.'))
        
        # Calculate overall risk - Python 2.x migrations are inherently riskier
        if is_python2_migration:
            # Python 2 to 3 migrations are always at least medium risk
            if len(critical_issues) > 3 or len(major_issues) > 15:
                overall_risk = "very_high"
            elif len(critical_issues) > 0 or len(major_issues) > 5:
                overall_risk = "high"
            else:
                overall_risk = "medium"  # Minimum for Python 2 -> 3
        else:
            # Standard risk calculation for Python 3.x upgrades
            if len(critical_issues) > 5:
                overall_risk = "very_high"
            elif len(critical_issues) > 0 or len(major_issues) > 10:
                overall_risk = "high"
            elif len(major_issues) > 0 or len(minor_issues) > 20:
                overall_risk = "medium"
            else:
                overall_risk = "low"
        
        return {
            "overall_risk": overall_risk,
            "critical_issues": len(critical_issues),
            "major_issues": len(major_issues),
            "minor_issues": len(minor_issues),
            "total_issues": len(issues),
            "confidence_score": version_info.confidence_score,
            "estimated_effort": self._estimate_effort(issues, is_python2_migration),
            "blocking_issues": [i.description for i in critical_issues[:5]],
            "is_python2_migration": is_python2_migration,
            "migration_type": "Python 2.x → 3.x" if is_python2_migration else f"Python 3.x upgrade"
        }
    
    def _estimate_effort(self, issues: List[MigrationIssue], is_python2_migration: bool = False) -> str:
        """Estimate effort required for migration"""
        critical = len([i for i in issues if i.severity == 'critical'])
        major = len([i for i in issues if i.severity == 'major'])
        
        if is_python2_migration:
            # Python 2 to 3 migrations require more effort
            if critical > 5 or major > 30:
                return "very_high"
            elif critical > 2 or major > 10:
                return "high"
            elif critical > 0 or major > 0:
                return "medium"
            else:
                return "medium"  # Minimum for Python 2 -> 3
        else:
            # Standard effort calculation for Python 3.x upgrades
            if critical > 10 or major > 50:
                return "very_high"
            elif critical > 5 or major > 20:
                return "high"
            elif critical > 0 or major > 5:
                return "medium"
            else:
                return "low"
    
    def _generate_recommendations(self, version_info: PythonVersionInfo, issues: List[MigrationIssue]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Check if this is a Python 2.x migration
        is_python2_migration = (version_info.detected_version and 
                               version_info.detected_version.startswith('2.') and 
                               self.target_version.startswith('3.'))
        
        # Version-related recommendations
        if version_info.detected_version:
            current = version_info.detected_version
            target = self.target_version
            if is_python2_migration:
                recommendations.append(f"🚨 MAJOR MIGRATION: Python {current} → {target} (Breaking changes expected)")
                recommendations.append("� This is a major version upgrade with significant breaking changes")
            else:
                recommendations.append(f"�🔄 Plan migration from Python {current} to {target}")
        else:
            recommendations.append("🔍 First determine the exact current Python version being used")
        
        # Issue-based recommendations
        critical_issues = [i for i in issues if i.severity == 'critical']
        if critical_issues:
            recommendations.append(f"🚨 Address {len(critical_issues)} critical issues before migration")
            recommendations.append("⚠️ Critical issues must be fixed to ensure compatibility")
        
        major_issues = [i for i in issues if i.severity == 'major']
        if major_issues:
            recommendations.append(f"⚡ Plan to fix {len(major_issues)} major issues")
        
        # Python 2.x specific recommendations
        if is_python2_migration:
            recommendations.extend([
                "🛠️ Consider using 2to3 tool for initial automated conversion",
                "🔧 Plan for extensive manual code review and testing",
                "📝 Update all print statements to print() function calls",
                "🔤 Review string/unicode handling throughout codebase",
                "📊 Test integer division behavior (/ vs //)",
                "📦 Update all import statements for Python 3 compatibility",
                "🧪 Set up dual Python 2/3 testing during transition (if needed)"
            ])
        
        # General recommendations
        if is_python2_migration:
            recommendations.extend([
                "🧪 Set up comprehensive testing - Python 2→3 migrations are complex",
                "📦 Verify ALL dependencies support Python 3",
                "💾 Create full backup and consider feature freeze during migration",
                "📚 Review Python 3 migration guide and breaking changes documentation",
                "⏰ Plan for extended testing and debugging period"
            ])
        else:
            recommendations.extend([
                "🧪 Set up comprehensive testing before migration",
                "📦 Check all dependencies for target version compatibility",
                "🔄 Consider incremental migration if jumping multiple versions",
                "💾 Create full backup before starting migration",
                "📚 Review Python version changelog for breaking changes"
            ])
        
        return recommendations
    
    def save_analysis(self, result: AnalysisResult, output_file: Optional[str] = None) -> str:
        """Save analysis result to JSON file"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"python_version_analysis_{timestamp}.json"
        
        output_path = Path(output_file)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Analysis saved to: {output_path.absolute()}")
        return str(output_path.absolute())


if __name__ == "__main__":
    # Example usage
    analyzer = PythonVersionAnalyzer()
    
    # Analyze current project
    project_path = Path(__file__).parent.parent
    result = analyzer.analyze_project(str(project_path))
    
    # Save results
    output_file = analyzer.save_analysis(result)
    
    print(f"\n🎉 Analysis Complete!")
    print(f"📊 Results saved to: {output_file}")
    print(f"🔍 Current version: {result.current_version.detected_version}")
    print(f"🎯 Target version: {result.target_version}")
    print(f"🚨 Issues found: {len(result.migration_issues)}")
    print(f"⚠️ Risk level: {result.risk_assessment['overall_risk']}")