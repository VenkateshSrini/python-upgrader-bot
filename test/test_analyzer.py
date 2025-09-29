#!/usr/bin/env python3
"""
Test script for Python Version Analyzer

This script tests the analyzer with the current project to ensure everything works correctly.
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Also add the root directory for imports
root_path = Path(__file__).parent.parent
sys.path.insert(0, str(root_path))

try:
    from src.app_py_version.version_analyzer import PythonVersionAnalyzer
    print("✅ Successfully imported PythonVersionAnalyzer")
except ImportError as e:
    print(f"❌ Failed to import PythonVersionAnalyzer: {e}")
    sys.exit(1)

def test_basic_functionality():
    """Test basic analyzer functionality"""
    print("\n🧪 Testing basic functionality...")
    
    try:
        # Initialize analyzer
        analyzer = PythonVersionAnalyzer(target_version="3.11")
        print("✅ Analyzer initialized successfully")
        
        # Test version detection on parent project
        parent_dir = Path(__file__).parent.parent
        print(f"🔍 Testing version detection on: {parent_dir}")
        
        version_info = analyzer.detect_current_python_version(parent_dir)
        print(f"✅ Version detection completed:")
        print(f"   Detected: {version_info.detected_version}")
        print(f"   Minimum: {version_info.minimum_version}")
        print(f"   Recommended: {version_info.recommended_version}")
        print(f"   Confidence: {version_info.confidence_score:.2f}")
        
        # Test file discovery
        python_files = analyzer.discover_python_files(parent_dir)
        print(f"✅ Found {len(python_files)} Python files")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ai_functionality():
    """Test AI-powered analysis (if API keys are available)"""
    print("\n🤖 Testing AI functionality...")
    
    try:
        analyzer = PythonVersionAnalyzer(target_version="3.11")
        parent_dir = Path(__file__).parent.parent
        
        # Test AI version detection
        ai_result = analyzer._ai_version_detection(parent_dir)
        if ai_result:
            print("✅ AI version detection successful")
            print(f"   AI Analysis: {ai_result.get('analysis', 'No analysis provided')}")
        else:
            print("⚠️ AI version detection returned no results (this may be normal)")
        
        # Test migration analysis on a small sample
        print("🔍 Testing migration analysis...")
        issues = analyzer.analyze_migration_issues(parent_dir, "3.8")
        print(f"✅ Migration analysis completed, found {len(issues)} potential issues")
        
        return True
        
    except Exception as e:
        print(f"❌ AI functionality test failed: {e}")
        print("💡 This might be due to:")
        print("   - Missing API keys in .env file")
        print("   - Network connectivity issues")
        print("   - LLM service unavailability")
        return False

def test_full_analysis():
    """Test full project analysis"""
    print("\n📊 Testing full analysis...")
    
    try:
        analyzer = PythonVersionAnalyzer(target_version="3.11")
        
        # Analyze current project (parent directory)
        parent_dir = Path(__file__).parent.parent
        
        print("⏳ Running full analysis (this may take a moment)...")
        result = analyzer.analyze_project(str(parent_dir))
        
        print("✅ Full analysis completed!")
        print(f"   Project: {Path(result.project_path).name}")
        print(f"   Files analyzed: {result.total_files_analyzed}")
        print(f"   Issues found: {len(result.migration_issues)}")
        print(f"   Risk level: {result.risk_assessment['overall_risk']}")
        print(f"   Recommendations: {len(result.recommendations)}")
        
        # Save test results
        output_file = analyzer.save_analysis(result, "test_analysis_results.json")
        print(f"💾 Test results saved to: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Full analysis test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🚀 Python Version Analyzer - Test Suite")
    print("=" * 50)
    
    tests = [
        ("Basic Functionality", test_basic_functionality),
        ("AI Functionality", test_ai_functionality),
        ("Full Analysis", test_full_analysis)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        print("-" * 30)
        
        try:
            success = test_func()
            results.append((test_name, success))
        except KeyboardInterrupt:
            print("\n⚠️ Tests interrupted by user")
            break
        except Exception as e:
            print(f"❌ Unexpected error in {test_name}: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status}: {test_name}")
        if success:
            passed += 1
    
    print(f"\n🎯 Results: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! The analyzer is ready to use.")
        print("\n💡 Next steps:")
        print("   1. Try: python cli.py analyze . --detailed")
        print("   2. Analyze your own projects")
        print("   3. Experiment with different target versions")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
        print("\n💡 Common issues:")
        print("   - Missing API keys in .env file")
        print("   - Required dependencies not installed")
        print("   - Network connectivity problems")

if __name__ == "__main__":
    main()