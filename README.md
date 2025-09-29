# 🚀 Python Upgrader Bot# 🚀 Python Upgrader Bot# Python Migration & Modernization Toolkit



A comprehensive AI-powered toolkit for migrating and modernizing Python code using real industry-standard tools.



## ⚡ Quick StartA comprehensive AI-powered toolkit for migrating and modernizing Python code using real industry-standard tools.A comprehensive AI-powered toolkit for analyzing, migrating, and modernizing Python code. This project combines traditional analysis tools with cutting-edge AI capabilities to provide intelligent code transformation.



```bash

python run.py

```## ⚡ Quick Start## 🚀 Features



That's it! The system will analyze, migrate, and modernize your Python code automatically.



## 🎯 What It Does```bash### Core Analysis



- **Analyzes** Python projects for version compatibilitypython run.py- **Version Detection**: Automatically detect Python version requirements from code

- **Detects** Python 2.x code automatically  

- **Applies** real migration tools (pyupgrade, lib2to3, modernize)```- **Compatibility Analysis**: Identify version-specific issues and requirements

- **Uses** LLM guidance for intelligent error resolution

- **Stores** final migrated files in clean OUTPUT_DIR structure- **Dependency Analysis**: Track and analyze package dependencies



## 📚 DocumentationThat's it! The system will analyze, migrate, and modernize your Python code automatically.



👉 **[Complete Documentation](document/COMPREHENSIVE_DOCUMENTATION.md)** 👈### Direct Tool Integration + AI Analysis



Everything you need is in one comprehensive guide:## 🎯 What It Does- **PyUpgrade Tool**: Uses actual `pyupgrade` command-line tool + AI fallback

- Quick start guide

- Technical implementation details- **Python 2 to 3 Migration**: Uses `lib2to3` engine + pattern-based migration

- Migration process explanation

- Configuration options- **Analyzes** Python projects for version compatibility- **Compatibility Modernization**: Uses `python-modernize` + smart fallbacks

- Troubleshooting guide

- Real-world examples- **Detects** Python 2.x code automatically  



## 📁 Project Structure- **Applies** real migration tools (pyupgrade, lib2to3, modernize)### Key Capabilities



```- **Uses** LLM guidance for intelligent error resolution- 🔧 **Direct Tool Integration**: Uses actual pyupgrade, lib2to3, and python-modernize

py-upgrade-bot/

├── run.py                    # 🚀 PRIMARY LAUNCHER- **Stores** final migrated files in clean OUTPUT_DIR structure- 🤖 **Smart Fallbacks**: AI-powered analysis when tools unavailable

├── src/                      # Core application code

├── document/                 # 📚 Complete documentation- 📊 **Comprehensive Reporting**: Detailed analysis and recommendations

│   └── COMPREHENSIVE_DOCUMENTATION.md  # Everything you need

├── test-project/upgraded/    # Migration results## 📚 Complete Documentation- 🧪 **Extensive Testing**: Complete test coverage for all tools

└── requirements.txt          # Dependencies

```- 📚 **Rich Documentation**: Comprehensive guides and examples



## 🎉 Ready to Migrate?👉 **[See Complete Documentation](document/COMPREHENSIVE_DOCUMENTATION.md)** 👈- ⚡ **Reliable Results**: Battle-tested transformations using industry standards



```bash

python run.py

```Everything you need is in the comprehensive documentation:## 📁 Project Structure



Check `test-project/upgraded/final_migrated_code/` for your migrated Python files!- Detailed usage guide



---- Technical implementation```



*For complete documentation: [document/COMPREHENSIVE_DOCUMENTATION.md](document/COMPREHENSIVE_DOCUMENTATION.md)*- Configuration options  py-upgrade-bot/

- Troubleshooting├── src/

- Real-world examples│   └── app_py_version/

│       ├── __init__.py                 # Package exports

## 📁 Project Structure│       ├── version_analyzer.py         # Core analysis engine

│       ├── prompt_library.py          # Centralized AI prompts

```│       └── ai_tools/                  # AI migration tools

py-upgrade-bot/│           ├── __init__.py

├── run.py                    # 🚀 PRIMARY LAUNCHER│           ├── pyupgrade_tool.py      # Python syntax modernization

├── src/                      # Core application code│           ├── python2to3_tool.py     # Python 2 → 3 migration

├── document/                 # 📚 Complete documentation│           └── modernize_tool.py      # 2/3 compatibility

├── test-project/upgraded/    # Migration results├── test/

└── requirements.txt          # Dependencies│   ├── test_prompt_library.py        # Prompt library tests

```│   └── test_ai_tools.py              # AI tools test suite

├── document/

## 🎉 Ready to Migrate?│   └── ai-tools-guide.md             # Comprehensive documentation

├── demo_ai_tools.py                  # Interactive demo script

```bash├── requirements.txt                   # Project dependencies

python run.py├── config.py                         # Configuration settings

```└── llm_manager.py                    # AI/LLM integration

```

Check `test-project/upgraded/final_migrated_code/` for your migrated Python files!

## 🛠️ Installation

---

1. **Clone the repository**:

*For complete documentation, configuration, and troubleshooting: [document/COMPREHENSIVE_DOCUMENTATION.md](document/COMPREHENSIVE_DOCUMENTATION.md)*   ```bash
   git clone <repository-url>
   cd py-upgrade-bot
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify installation**:
   ```python
   python -m pytest test/
   ```

## 🎯 Quick Start

### Basic Usage

```python
from src.app_py_version.ai_tools import PyUpgradeTool, Python2To3Tool, ModernizeTool

# Modernize Python code to latest syntax
pyupgrade = PyUpgradeTool(target_version="3.11")
modern_code = pyupgrade.run("old_code_here")

# Migrate Python 2 to Python 3
migration = Python2To3Tool()
python3_code = migration.run("python2_code_here")

# Create 2/3 compatible code
compatibility = ModernizeTool()
compatible_code = compatibility.run("code_needing_compatibility")
```

### Interactive Demo

Run the comprehensive demo to see all tools in action:

```bash
python demo_ai_tools.py
```

## 🔧 AI Tools Details

### PyUpgradeTool
**Purpose**: Uses the actual `pyupgrade` command-line tool for reliable modernization
- Converts old string formatting to f-strings
- Updates Union types to use `|` operator (Python 3.10+)
- Removes unnecessary `__future__` imports
- Optimizes for target Python version
- Falls back to pattern-based processing when tool unavailable

**Example**:
```python
# Input
message = "Hello, {}!".format(name)
Union[str, int]

# Output (using real pyupgrade)
message = f"Hello, {name}!"
str | int
```

### Python2To3Tool
**Purpose**: Uses `lib2to3` engine (same as 2to3 command) for reliable migration
- Converts print statements to print functions
- Updates exception handling syntax
- Migrates import statements (urllib2 → urllib.request)
- Replaces deprecated functions (raw_input → input, xrange → range)
- Falls back to pattern-based migration when lib2to3 unavailable

**Example**:
```python
# Input (Python 2)
print "Hello, World!"
import urllib2
name = raw_input("Name: ")

# Output (Python 3 using lib2to3)
print("Hello, World!")
import urllib.request
name = input("Name: ")
```

### ModernizeTool
**Purpose**: Uses `python-modernize` tool for reliable 2/3 compatibility
- Adds appropriate `from __future__` imports
- Handles division behavior differences
- Manages string/unicode compatibility
- Creates code that works on both Python 2.7+ and 3.x
- Falls back to pattern-based processing when tool unavailable

**Example**:
```python
# Input
print "Starting..."
result = 5 / 2

# Output (using python-modernize)
from __future__ import division, print_function
print("Starting...")
result = 5 / 2  # Now behaves consistently
```

## 🧪 Testing

The project includes comprehensive test coverage:

```bash
# Run all tests
python -m pytest test/

# Run specific test file
python -m pytest test/test_ai_tools.py -v

# Test with coverage
python -m pytest test/ --cov=src/app_py_version
```

## 📊 Analysis Capabilities

### Version Detection
- Automatically detects minimum Python version requirements
- Identifies version-specific syntax and features
- Provides detailed compatibility reports

### Code Pattern Recognition
- Identifies outdated patterns and practices
- Suggests modern alternatives
- Provides migration recommendations

## 🔌 Integration

### LangChain Compatibility
All AI tools are built as LangChain `BaseTool` implementations:

```python
from langchain.agents import initialize_agent
from src.app_py_version.ai_tools import PyUpgradeTool

tools = [PyUpgradeTool(target_version="3.11")]
agent = initialize_agent(tools, llm, agent="zero-shot-react-description")
```

### Custom Workflows
Tools can be easily integrated into custom analysis workflows:

```python
# Create analysis pipeline
analyzer = VersionAnalyzer()
pyupgrade = PyUpgradeTool()

# Analyze and modernize
analysis = analyzer.analyze_code(code)
modernized = pyupgrade.run(code)
```

## 📚 Documentation

- **[AI Tools Guide](document/ai-tools-guide.md)**: Comprehensive tool documentation
- **[API Reference](src/app_py_version/)**: Detailed code documentation
- **[Test Examples](test/)**: Usage examples and test cases

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with [LangChain](https://langchain.com/) for AI tool integration
- Uses [pyupgrade](https://github.com/asottile/pyupgrade), [modernize](https://github.com/python-modernize/python-modernize), and other excellent Python tools
- Inspired by the Python community's commitment to code quality and maintainability

---

**Ready to modernize your Python code? Get started with the demo!**

```bash
python demo_ai_tools.py
```