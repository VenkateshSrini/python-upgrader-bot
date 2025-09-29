#!/usr/bin/env python3
"""
Python Upgrader Bot - Main Launcher

This is the primary script to run the complete Python upgrade workflow.

WHAT IT DOES:
1. Analyzes a Python project for version compatibility issues
2. Detects Python 2.x code automatically
3. Applies direct migration tools (pyupgrade, lib2to3, modernize)
4. Uses LLM guidance for intelligent tool selection
5. Performs iterative compilation checking
6. Stores final migrated files in OUTPUT_DIR

USAGE:
    python run.py

The script will automatically:
- Analyze the test project in test-project/source/simple_python2_test/
- Generate analysis reports in test-project/upgraded/
- Apply migration tools systematically
- Store final migrated code in test-project/upgraded/final_migrated_code/

OUTPUT STRUCTURE:
test-project/upgraded/
├── final_migrated_code/          # ✅ Final migrated Python files
├── migration_status.txt          # ✅ Migration success status
├── migrated_files_summary.md     # ✅ Complete file summary
├── migration_execution_*.json    # ✅ Detailed migration log
└── python_upgrade_analysis*.json # ✅ Analysis reports

This is the complete end-to-end workflow using real migration tools!
"""

import subprocess
import sys
from pathlib import Path

def main():
    """Launch the main Python upgrader bot"""
    script_path = Path(__file__).parent / "src" / "python-upgrader-bot.py"
    
    if not script_path.exists():
        print("❌ Main script not found at:", script_path)
        sys.exit(1)
    
    print("🚀 Launching Python Upgrader Bot...")
    print("📖 This will run the complete migration workflow using real tools!")
    print()
    
    # Run the main script using the same Python interpreter
    try:
        result = subprocess.run([sys.executable, str(script_path)], 
                              cwd=Path(__file__).parent)
        
        if result.returncode == 0:
            print("\n" + "=" * 70)
            print("🎉 PYTHON UPGRADER BOT COMPLETED SUCCESSFULLY!")
            print("=" * 70)
            print("📁 Check test-project/upgraded/ for all results:")
            print("   📄 final_migrated_code/ - Your migrated Python files")
            print("   📄 migration_status.txt - Success/failure status")
            print("   📄 migrated_files_summary.md - Complete file summary")
            print("   📄 migration_execution_*.json - Detailed logs")
            print()
            print("💡 Ready to use the migrated code from final_migrated_code/")
        
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\n🛑 Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error running main script: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()