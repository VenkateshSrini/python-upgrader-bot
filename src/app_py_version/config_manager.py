#!/usr/bin/env python3
"""
Configuration Manager for Python Upgrader Bot

This module handles loading configuration from multiple environment files:
- .env.keys: LLM API keys (sensitive data)
- .env.config: Application-specific settings
- .env: Fallback for backward compatibility

Usage:
    from app_py_version.config_manager import load_config
    load_config()  # Loads all configuration files
    
    # Or load specific config
    from app_py_version.config_manager import load_keys_config, load_app_config
    load_keys_config()    # Load only API keys
    load_app_config()     # Load only application settings
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Get the project root directory."""
    # Start from current file and go up to find project root
    current_path = Path(__file__).resolve()
    
    # Go up until we find the project root (contains run.py)
    for parent in current_path.parents:
        if (parent / "run.py").exists():
            return parent
    
    # Fallback to parent of src directory
    return current_path.parent.parent

def load_keys_config(project_root: Path = None) -> bool:
    """
    Load LLM API keys from .env.keys file.
    
    Args:
        project_root: Path to project root. If None, will auto-detect.
        
    Returns:
        bool: True if keys file was loaded successfully
    """
    if project_root is None:
        project_root = get_project_root()
    
    keys_file = project_root / ".env.keys"
    
    if keys_file.exists():
        load_dotenv(keys_file, override=False)
        logger.info(f"✅ Loaded API keys from {keys_file}")
        return True
    else:
        logger.warning(f"⚠️ API keys file not found: {keys_file}")
        return False

def load_app_config(project_root: Path = None) -> bool:
    """
    Load application configuration from .env.config file.
    
    Args:
        project_root: Path to project root. If None, will auto-detect.
        
    Returns:
        bool: True if config file was loaded successfully
    """
    if project_root is None:
        project_root = get_project_root()
    
    config_file = project_root / ".env.config"
    
    if config_file.exists():
        load_dotenv(config_file, override=False)
        logger.info(f"✅ Loaded application config from {config_file}")
        return True
    else:
        logger.warning(f"⚠️ Application config file not found: {config_file}")
        return False

def load_legacy_config(project_root: Path = None) -> bool:
    """
    Load legacy .env file for backward compatibility.
    
    Args:
        project_root: Path to project root. If None, will auto-detect.
        
    Returns:
        bool: True if legacy config file was loaded successfully
    """
    if project_root is None:
        project_root = get_project_root()
    
    legacy_file = project_root / ".env"
    
    if legacy_file.exists():
        load_dotenv(legacy_file, override=False)
        logger.info(f"✅ Loaded legacy config from {legacy_file}")
        return True
    else:
        logger.info(f"ℹ️ No legacy .env file found (this is normal)")
        return False

def load_config(project_root: Path = None) -> dict:
    """
    Load all configuration files in the correct order.
    
    Priority order (later files don't override earlier ones):
    1. .env.keys (API keys - highest priority)
    2. .env.config (application settings)
    3. .env (legacy fallback - lowest priority)
    
    Args:
        project_root: Path to project root. If None, will auto-detect.
        
    Returns:
        dict: Summary of loaded configuration files
    """
    if project_root is None:
        project_root = get_project_root()
    
    logger.info("🔧 Loading Python Upgrader Bot configuration...")
    
    results = {
        "project_root": str(project_root),
        "keys_loaded": False,
        "config_loaded": False,
        "legacy_loaded": False
    }
    
    # Load in reverse priority order (load_dotenv with override=False 
    # means first loaded values take precedence)
    
    # 3. Legacy .env (lowest priority)
    results["legacy_loaded"] = load_legacy_config(project_root)
    
    # 2. Application config (medium priority)
    results["config_loaded"] = load_app_config(project_root)
    
    # 1. API keys (highest priority)
    results["keys_loaded"] = load_keys_config(project_root)
    
    # Validate critical configuration
    validate_config()
    
    logger.info("✅ Configuration loading complete!")
    return results

def validate_config():
    """Validate that critical configuration is available."""
    
    # Check for required API keys
    if not os.getenv("ANTHROPIC_API_KEY"):
        logger.error("❌ ANTHROPIC_API_KEY not found in configuration!")
        logger.error("💡 Please ensure .env.keys file exists with valid API key")
    else:
        logger.info("✅ Anthropic API key is configured")
    
    # Check for important app settings
    target_version = os.getenv("TARGET_PYTHON_VERSION", "3.11")
    max_iterations = os.getenv("MAX_MIGRATION_ITERATIONS", "5")
    
    logger.info(f"🎯 Target Python version: {target_version}")
    logger.info(f"🔄 Max migration iterations: {max_iterations}")

def get_config_summary() -> dict:
    """Get a summary of current configuration values."""
    
    # Safely get config values (don't expose API keys)
    return {
        "target_python_version": os.getenv("TARGET_PYTHON_VERSION", "3.11"),
        "max_migration_iterations": int(os.getenv("MAX_MIGRATION_ITERATIONS", "5")),
        "max_files_to_analyze": int(os.getenv("MAX_FILES_TO_ANALYZE", "20")),
        "llm_temperature": float(os.getenv("LLM_TEMPERATURE", "0.1")),
        "enable_detailed_logging": os.getenv("ENABLE_DETAILED_LOGGING", "true").lower() == "true",
        "migration_verbose_logging": os.getenv("MIGRATION_VERBOSE_LOGGING", "true").lower() == "true",
        "has_anthropic_key": bool(os.getenv("ANTHROPIC_API_KEY")),
        "has_openai_key": bool(os.getenv("OPENAI_API_KEY")),
        "has_google_key": bool(os.getenv("GOOGLE_API_KEY")),
        "has_groq_key": bool(os.getenv("GROQ_API_KEY"))
    }

# Auto-load configuration when this module is run directly
if __name__ == "__main__":
    try:
        results = load_config()
        print("🎉 Configuration loaded successfully!")
        print(f"📊 Summary: {get_config_summary()}")
    except Exception as e:
        logger.error(f"❌ Error loading configuration: {e}")