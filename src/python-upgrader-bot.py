#!/usr/bin/env python3
"""
Python Upgrader Bot - Main Script

This script analyzes a Python project for version compatibility and generates
an upgrade analysis report with recommendations for migrating to a target Python version.

Usage:
    python python-upgrader-bot.py
    
This will analyze the test project and generate reports in the upgraded directory.
"""

import sys
import os
from pathlib import Path
import json
from datetime import datetime
import logging
import re

# Load configuration from centralized manager
from app_py_version.config_manager import load_config

# Load environment variables from both .env.keys and .env.config
load_config()

# Windows Unicode handling
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

# Add current directory to Python path to import our modules
sys.path.insert(0, str(Path(__file__).parent))

try:
    from app_py_version.version_analyzer import PythonVersionAnalyzer
    from app_py_version.migration_executor import MigrationExecutor
    safe_print("✅ Successfully imported PythonVersionAnalyzer and MigrationExecutor")
except ImportError as e:
    safe_print(f"❌ Failed to import required modules: {e}")
    safe_print("💡 Make sure you're running this from the project root directory")
    sys.exit(1)


def main():
    """Main function to run the Python upgrade analysis and automated migration"""
    
    # Configuration (paths relative to project root)
    project_root = Path(__file__).parent.parent
    SOURCE_PROJECT = project_root / "test-project/source/simple_python2_test"
    OUTPUT_DIR = project_root / "test-project/upgraded"
    TARGET_VERSION = "3.11"  # Target Python version from .env
    MAX_MIGRATION_ITERATIONS = int(os.getenv("MAX_MIGRATION_ITERATIONS", "5"))  # Configurable iterations
    
    safe_print("🚀 Python Upgrader Bot Starting...")
    safe_print("=" * 70)
    safe_print(f"📁 Source Project: {SOURCE_PROJECT.absolute()}")
    safe_print(f"📁 Output Directory: {OUTPUT_DIR.absolute()}")
    safe_print(f"🎯 Target Python Version: {TARGET_VERSION}")
    safe_print(f"🔄 Max Migration Iterations: {MAX_MIGRATION_ITERATIONS}")
    safe_print("=" * 70)
    
    # Validate source project exists
    if not SOURCE_PROJECT.exists():
        safe_print(f"❌ Source project not found: {SOURCE_PROJECT.absolute()}")
        safe_print("💡 Please ensure the test project exists in the specified location")
        sys.exit(1)
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        # Initialize the analyzer
        safe_print("🔧 Initializing Python Version Analyzer...")
        analyzer = PythonVersionAnalyzer(target_version=TARGET_VERSION)
        
        # Perform comprehensive analysis
        safe_print(f"🔍 Analyzing project: {SOURCE_PROJECT.name}")
        safe_print("⏳ This may take a moment...")
        
        result = analyzer.analyze_project(str(SOURCE_PROJECT.absolute()))
        
        # Generate output filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"python_upgrade_analysis_{timestamp}.json"
        output_path = OUTPUT_DIR / output_filename
        
        # Save detailed analysis results
        safe_print(f"💾 Saving analysis results...")
        analyzer.save_analysis(result, str(output_path))
        
        # Create human-readable summary report
        summary_filename = f"upgrade_summary_{timestamp}.md"
        summary_path = OUTPUT_DIR / summary_filename
        create_summary_report(result, summary_path, SOURCE_PROJECT, TARGET_VERSION)
        
        # Display summary
        safe_print("\n" + "=" * 60)
        safe_print("📊 ANALYSIS COMPLETE!")
        safe_print("=" * 60)
        project_name = Path(result.project_path).name
        safe_print(f"✅ Project analyzed: {project_name}")
        safe_print(f"📁 Files analyzed: {result.total_files_analyzed}")
        safe_print(f"🔍 Current Python version detected: {result.current_version.detected_version}")
        safe_print(f"🎯 Target Python version: {result.target_version}")
        safe_print(f"🚨 Migration issues found: {len(result.migration_issues)}")
        safe_print(f"⚠️  Risk level: {result.risk_assessment.get('overall_risk', 'unknown')}")
        safe_print(f"💡 Recommendations: {len(result.recommendations)}")
        
        # File outputs
        safe_print(f"\n📄 Detailed analysis saved to: {output_path.absolute()}")
        safe_print(f"📄 Summary report saved to: {summary_path.absolute()}")
        
        # Show top issues if any
        if result.migration_issues:
            safe_print(f"\n🔍 Top Migration Issues:")
            for i, issue in enumerate(result.migration_issues[:3], 1):
                safe_print(f"  {i}. {getattr(issue, 'description', 'Unknown issue')} "
                      f"(Severity: {getattr(issue, 'severity', 'unknown')})")
            if len(result.migration_issues) > 3:
                safe_print(f"  ... and {len(result.migration_issues) - 3} more issues")
        
        # Show top recommendations
        if result.recommendations:
            safe_print(f"\n💡 Top Recommendations:")
            for i, rec in enumerate(result.recommendations[:3], 1):
                safe_print(f"  {i}. {rec}")
            if len(result.recommendations) > 3:
                safe_print(f"  ... and {len(result.recommendations) - 3} more recommendations")
        
        safe_print(f"\n🎉 Analysis completed successfully!")
        
        # Start automated migration process if Python 2 is detected or migration issues found
        needs_migration = (result.migration_issues or 
                          result.current_version.detected_version.startswith('2.'))
        
        if needs_migration:
            safe_print("\n" + "=" * 70)
            safe_print("🤖 STARTING AUTOMATED MIGRATION PROCESS")
            safe_print("=" * 70)
            
            if result.current_version.detected_version.startswith('2.'):
                safe_print("🔍 Python 2.x detected - migration required!")
            if result.migration_issues:
                safe_print(f"🚨 {len(result.migration_issues)} migration issues detected")
            
            try:
                # Initialize migration executor with the same LLM manager
                executor = MigrationExecutor(
                    max_iterations=MAX_MIGRATION_ITERATIONS,
                    llm_manager=analyzer.llm_manager  # Pass the LLM manager from analyzer
                )
                
                # Execute automated migration
                safe_print("� Executing LLM-guided migration tools...")
                migration_result = executor.execute_migration(
                    result, SOURCE_PROJECT, OUTPUT_DIR
                )
                
                # Save migration execution results
                migration_log_path = OUTPUT_DIR / f"migration_execution_{timestamp}.json"
                with open(migration_log_path, 'w', encoding='utf-8') as f:
                    json.dump(migration_result, f, indent=2, ensure_ascii=False)
                
                # Report migration results
                safe_print(f"\n📊 MIGRATION EXECUTION COMPLETE!")
                safe_print("=" * 70)
                safe_print(f"🔄 Iterations completed: {len(migration_result['iterations'])}")
                safe_print(f"🏗️  Compilation attempts: {migration_result['compilation_attempts']}")
                safe_print(f"✅ Final status: {migration_result['final_status']}")
                
                if migration_result['successful_fixes']:
                    safe_print(f"🔧 Successful fixes applied: {len(migration_result['successful_fixes'])}")
                    for fix in migration_result['successful_fixes'][:3]:
                        safe_print(f"   - {fix}")
                
                if migration_result['unresolved_issues']:
                    safe_print(f"⚠️  Unresolved issues: {len(migration_result['unresolved_issues'])}")
                    safe_print("   See migration_issues.md for details")
                
                safe_print(f"📄 Migration log saved to: {migration_log_path.absolute()}")
                safe_print(f"📁 Working migration files: {migration_result['working_dir']}")
                
                # Show final migrated files location
                final_migrated_dir = OUTPUT_DIR / "final_migrated_code"
                if final_migrated_dir.exists():
                    safe_print(f"📁 Final migrated code: {final_migrated_dir.absolute()}")
                    safe_print(f"📄 Migration status: {OUTPUT_DIR / 'migration_status.txt'}")
                    safe_print(f"📄 Files summary: {OUTPUT_DIR / 'migrated_files_summary.md'}")
                
                if migration_result['final_status'] == 'success':
                    safe_print("\n🎉 PROJECT SUCCESSFULLY MIGRATED AND COMPILES!")
                    safe_print("✅ Ready to use final migrated code from OUTPUT_DIR")
                else:
                    safe_print(f"\n⚠️  Migration completed with status: {migration_result['final_status']}")
                    safe_print("💡 Check migration_issues.md for remaining problems")
                
            except Exception as e:
                safe_print(f"\n❌ Error during automated migration: {e}")
                safe_print("💡 Manual review of analysis results may be needed")
        else:
            safe_print("\n✅ No migration issues detected - project should be ready!")
        
        safe_print("\n💡 Review all generated reports for complete upgrade guidance.")
        return 0
        
    except Exception as e:
        safe_print(f"\n❌ Error during analysis: {e}")
        safe_print("💡 Please check the error message and try again")
        return 1


def create_summary_report(result, output_path: Path, source_project: Path, target_version: str):
    """Create a human-readable markdown summary report"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"# Python Upgrade Analysis Report\n\n")
        f.write(f"**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Project Overview
        f.write("## Project Overview\n\n")
        f.write(f"- **Project Name:** {Path(result.project_path).name}\n")
        f.write(f"- **Source Location:** {source_project.absolute()}\n")
        f.write(f"- **Files Analyzed:** {result.total_files_analyzed}\n")
        f.write(f"- **Current Python Version:** {result.current_version.detected_version}\n")
        f.write(f"- **Target Python Version:** {target_version}\n")
        f.write(f"- **Analysis Date:** {result.analysis_timestamp.strftime('%Y-%m-%d %H:%M:%S') if hasattr(result.analysis_timestamp, 'strftime') else str(result.analysis_timestamp)}\n\n")
        
        # Risk Assessment
        f.write("## Risk Assessment\n\n")
        risk_level = result.risk_assessment.get('overall_risk', 'unknown')
        f.write(f"**Overall Risk Level:** {risk_level.upper()}\n\n")
        
        if 'risk_factors' in result.risk_assessment:
            f.write("### Risk Factors:\n")
            for factor in result.risk_assessment['risk_factors']:
                f.write(f"- {factor}\n")
            f.write("\n")
        
        # Migration Issues
        f.write("## Migration Issues\n\n")
        if result.migration_issues:
            f.write(f"Found {len(result.migration_issues)} potential migration issues:\n\n")
            for i, issue in enumerate(result.migration_issues, 1):
                # MigrationIssue is a dataclass, access attributes directly
                severity = getattr(issue, 'severity', 'unknown')
                description = getattr(issue, 'description', 'No description available')
                file_path = getattr(issue, 'file_path', 'Unknown file')
                line_number = getattr(issue, 'line_number', 'Unknown line')
                
                f.write(f"### {i}. {description}\n")
                f.write(f"- **Severity:** {severity}\n")
                f.write(f"- **File:** {file_path}\n")
                f.write(f"- **Line:** {line_number}\n")
                
                if hasattr(issue, 'suggested_fix') and issue.suggested_fix:
                    f.write(f"- **Suggested Fix:** {issue.suggested_fix}\n")
                if hasattr(issue, 'explanation') and issue.explanation:
                    f.write(f"- **Explanation:** {issue.explanation}\n")
                f.write("\n")
        else:
            f.write("✅ No migration issues detected!\n\n")
        
        # Recommendations
        f.write("## Recommendations\n\n")
        if result.recommendations:
            for i, recommendation in enumerate(result.recommendations, 1):
                f.write(f"{i}. {recommendation}\n")
        else:
            f.write("No specific recommendations available.\n")
        f.write("\n")
        
        # Version Detection Details
        f.write("## Version Detection Details\n\n")
        f.write(f"- **Detected Version:** {result.current_version.detected_version}\n")
        f.write(f"- **Minimum Required:** {result.current_version.minimum_version}\n")
        f.write(f"- **Confidence Level:** {result.current_version.confidence_score:.2f}\n")
        
        if result.current_version.detection_method:
            f.write(f"- **Detection Method:** {result.current_version.detection_method}\n")
        if result.current_version.evidence:
            f.write(f"- **Evidence:** {', '.join(result.current_version.evidence)}\n")
        f.write("\n")
        
        # Footer
        f.write("---\n")
        f.write("*Report generated by Python Upgrader Bot*\n")


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)