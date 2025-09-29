#!/usr/bin/env python3
"""
CLI Interface for Python Version Analyzer

This provides a user-friendly command-line interface for the AI-powered 
Python version analyzer.

Usage:
    python cli.py analyze [project_path] [--target-version 3.11] [--output report.json]
    python cli.py --help
"""

import argparse
import sys
import json
from pathlib import Path
from typing import Optional
import logging

# Configure logging for CLI
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)

try:
    from version_analyzer import PythonVersionAnalyzer, AnalysisResult
except ImportError as e:
    logger.error(f"❌ Could not import version_analyzer: {e}")
    logger.error("💡 Make sure you're running this from the app-py-version directory")
    sys.exit(1)


def print_banner():
    """Print welcome banner"""
    banner = """
╔═══════════════════════════════════════════════════════════════╗
║                🐍 AI-Powered Python Version Analyzer          ║
║                                                               ║
║  Intelligently analyze your Python project and identify      ║
║  migration issues using advanced AI technology               ║
╚═══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_analysis_summary(result: AnalysisResult):
    """Print a beautiful summary of the analysis results"""
    print("\n" + "="*70)
    print("📊 ANALYSIS SUMMARY")
    print("="*70)
    
    # Project Info
    print(f"📁 Project: {Path(result.project_path).name}")
    print(f"📄 Files analyzed: {result.total_files_analyzed}")
    print(f"⏰ Analysis time: {result.analysis_timestamp}")
    
    # Version Info
    print(f"\n🔍 VERSION ANALYSIS:")
    current = result.current_version
    print(f"   Current version: {current.detected_version or 'Unknown'}")
    print(f"   Minimum required: {current.minimum_version or 'Unknown'}")
    print(f"   AI recommended: {current.recommended_version or 'Unknown'}")
    print(f"   Target version: {result.target_version}")
    print(f"   Detection confidence: {current.confidence_score:.1%}")
    
    # Issues Summary
    print(f"\n🚨 MIGRATION ISSUES:")
    issues = result.migration_issues
    critical = len([i for i in issues if i.severity == 'critical'])
    major = len([i for i in issues if i.severity == 'major'])
    minor = len([i for i in issues if i.severity == 'minor'])
    info = len([i for i in issues if i.severity == 'info'])
    
    print(f"   🔴 Critical: {critical}")
    print(f"   🟡 Major: {major}")
    print(f"   🟢 Minor: {minor}")
    print(f"   ℹ️  Info: {info}")
    print(f"   📊 Total: {len(issues)}")
    
    # Risk Assessment
    risk = result.risk_assessment
    risk_emoji = {
        'low': '✅',
        'medium': '⚠️',
        'high': '🚨',
        'very_high': '🔥'
    }
    
    overall_risk = risk.get('overall_risk', 'unknown')
    print(f"\n⚖️ RISK ASSESSMENT:")
    print(f"   Overall risk: {risk_emoji.get(overall_risk, '❓')} {overall_risk.upper()}")
    print(f"   Estimated effort: {risk.get('estimated_effort', 'unknown').upper()}")
    
    # Top Issues
    if critical > 0:
        print(f"\n🔴 TOP CRITICAL ISSUES:")
        critical_issues = [i for i in issues if i.severity == 'critical'][:3]
        for i, issue in enumerate(critical_issues, 1):
            print(f"   {i}. {issue.description}")
            print(f"      📁 {issue.file_path}:{issue.line_number}")
    
    # Recommendations
    print(f"\n💡 KEY RECOMMENDATIONS:")
    for i, rec in enumerate(result.recommendations[:5], 1):
        print(f"   {i}. {rec}")
    
    if len(result.recommendations) > 5:
        print(f"   ... and {len(result.recommendations) - 5} more recommendations")
    
    print("\n" + "="*70)


def print_detailed_issues(result: AnalysisResult, max_issues: int = 10):
    """Print detailed issue breakdown"""
    issues = result.migration_issues
    if not issues:
        print("✅ No migration issues found!")
        return
    
    print(f"\n🔍 DETAILED ISSUE ANALYSIS (showing top {min(max_issues, len(issues))})")
    print("="*70)
    
    # Sort by severity
    severity_order = {'critical': 0, 'major': 1, 'minor': 2, 'info': 3}
    sorted_issues = sorted(issues, key=lambda x: (severity_order.get(x.severity, 4), -x.ai_confidence))
    
    for i, issue in enumerate(sorted_issues[:max_issues], 1):
        severity_emoji = {
            'critical': '🔴',
            'major': '🟡', 
            'minor': '🟢',
            'info': 'ℹ️'
        }
        
        print(f"\n{i}. {severity_emoji.get(issue.severity, '❓')} {issue.severity.upper()}: {issue.description}")
        print(f"   📁 File: {issue.file_path}:{issue.line_number}")
        print(f"   🔧 Type: {issue.issue_type}")
        print(f"   🎯 Confidence: {issue.ai_confidence:.1%}")
        
        if issue.code_snippet:
            print(f"   📝 Code:")
            # Indent code snippet
            for line in issue.code_snippet.split('\n')[:3]:  # Show max 3 lines
                if line.strip():
                    print(f"      {line}")
        
        if issue.suggested_fix:
            print(f"   💡 Suggested fix: {issue.suggested_fix}")
        
        if issue.explanation:
            # Truncate long explanations
            explanation = issue.explanation[:200] + "..." if len(issue.explanation) > 200 else issue.explanation
            print(f"   📚 Explanation: {explanation}")


def analyze_command(args):
    """Handle the analyze command"""
    project_path = Path(args.project_path).resolve()
    
    if not project_path.exists():
        logger.error(f"❌ Project path does not exist: {project_path}")
        return 1
    
    if not project_path.is_dir():
        logger.error(f"❌ Project path is not a directory: {project_path}")
        return 1
    
    try:
        # Initialize analyzer
        print(f"🚀 Initializing AI-powered analyzer...")
        analyzer = PythonVersionAnalyzer(target_version=args.target_version)
        
        # Run analysis
        print(f"🔍 Analyzing project: {project_path}")
        print(f"🎯 Target version: {args.target_version}")
        print("⏳ This may take a few minutes...")
        
        result = analyzer.analyze_project(str(project_path))
        
        # Save results
        output_file = analyzer.save_analysis(result, args.output)
        
        # Display results
        print_analysis_summary(result)
        
        if args.detailed:
            print_detailed_issues(result, max_issues=args.max_issues)
        
        print(f"\n💾 Full analysis saved to: {output_file}")
        print(f"🎉 Analysis complete!")
        
        return 0
        
    except KeyboardInterrupt:
        logger.error("\n⚠️ Analysis interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"❌ Analysis failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="AI-Powered Python Version Analyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py analyze .                          # Analyze current directory
  python cli.py analyze /path/to/project          # Analyze specific project
  python cli.py analyze . --target-version 3.11   # Set target version
  python cli.py analyze . --detailed              # Show detailed issues
  python cli.py analyze . --output my_report.json # Custom output file

The analyzer will:
  1. 🔍 Detect your current Python version
  2. 🤖 Use AI to identify migration issues  
  3. ⚖️ Assess migration risk and effort
  4. 💡 Provide actionable recommendations
        """
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Analyze command
    analyze_parser = subparsers.add_parser(
        'analyze', 
        help='Analyze a Python project for version migration'
    )
    analyze_parser.add_argument(
        'project_path',
        nargs='?',
        default='.',
        help='Path to the Python project to analyze (default: current directory)'
    )
    analyze_parser.add_argument(
        '--target-version',
        default=None,
        help='Target Python version (default: from .env file or 3.11)'
    )
    analyze_parser.add_argument(
        '--output',
        help='Output JSON file path (default: auto-generated)'
    )
    analyze_parser.add_argument(
        '--detailed',
        action='store_true',
        help='Show detailed issue analysis'
    )
    analyze_parser.add_argument(
        '--max-issues',
        type=int,
        default=10,
        help='Maximum number of detailed issues to show (default: 10)'
    )
    analyze_parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose error reporting'
    )
    
    args = parser.parse_args()
    
    # Print banner
    print_banner()
    
    # Handle commands
    if args.command == 'analyze':
        return analyze_command(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())