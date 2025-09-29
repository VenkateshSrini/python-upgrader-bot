"""Configuration settings for Helm Bot"""
import os

# Note: Configuration is loaded by the centralized config_manager
# when imported by other modules. No need to load here to avoid circular imports.

# Directory paths
TEMPLATE_DIR = 'sample_helm'
TEMPLATES_SUBDIR = os.path.join(TEMPLATE_DIR, 'templates')

# File names
GENERATED_QUESTIONS_FILE = 'generated_questions.txt'
VALUES_FILE = 'values.yaml'
GENERATED_VALUES_FILE = 'generated_values.yaml'

# LLM settings
# OpenAI Models (commented out)
# DEFAULT_MODEL = 'gpt-3.5-turbo'
# GPT4_MODEL = 'gpt-4.1'

# Anthropic Models (active)
DEFAULT_MODEL = 'claude-sonnet-4-20250514'
GPT4_MODEL = 'claude-sonnet-4-20250514'

# AWS Bedrock Models (commented out)
# DEFAULT_MODEL = 'anthropic.claude-3-5-sonnet-20241022-v2:0'
# GPT4_MODEL = 'anthropic.claude-3-5-sonnet-20241022-v2:0'
# BEDROCK_REGION = 'us-east-1'

DEFAULT_TEMPERATURE = 0.7
GPT4_TEMPERATURE = 0.3

# Model provider configuration
PROVIDER = 'anthropic'  # Options: 'openai', 'anthropic', 'bedrock'
