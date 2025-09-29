"""LLM manager for handling multiple AI providers (OpenAI, Anthropic, AWS Bedrock) with LangChain"""
import os
from pathlib import Path
from abc import ABC, abstractmethod
from typing import Dict, Any
from config import DEFAULT_MODEL, GPT4_MODEL, DEFAULT_TEMPERATURE, GPT4_TEMPERATURE, PROVIDER

# Load configuration from centralized manager
from app_py_version.config_manager import load_config

# Import Bedrock region if it's configured
try:
    from config import BEDROCK_REGION
except ImportError:
    BEDROCK_REGION = 'us-east-1'  # Default region

# Load configuration from both .env.keys and .env.config
load_config()

class ModelProvider(ABC):
    """Abstract base class for AI model providers"""
    
    @abstractmethod
    def setup_api_key(self) -> None:
        """Setup API key for the provider"""
        pass
    
    @abstractmethod
    def create_llm(self, model_name: str, temperature: float) -> Any:
        """Create LLM instance for the provider"""
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Get the name of the provider"""
        pass


class OpenAIProvider(ModelProvider):
    """OpenAI model provider implementation"""
    
    def setup_api_key(self) -> None:
        """Setup OpenAI API key"""
        if "OPENAI_API_KEY" not in os.environ or os.environ["OPENAI_API_KEY"].strip() == "":
            print("🔑 OpenAI API key not found in environment variables.")
            api_key = input("Please enter your OpenAI API key: ").strip()
            if not api_key:
                raise ValueError("OpenAI API key cannot be empty!")
            os.environ['OPENAI_API_KEY'] = api_key
            print("✅ OpenAI API key is set successfully!")
        else:
            print("✅ OpenAI API key is already set.")
    
    def create_llm(self, model_name: str, temperature: float) -> Any:
        """Create OpenAI LLM instance"""
        from langchain_community.chat_models import ChatOpenAI
        return ChatOpenAI(model=model_name, temperature=temperature)
    
    def get_provider_name(self) -> str:
        return "OpenAI"


class AnthropicProvider(ModelProvider):
    """Anthropic model provider implementation"""
    
    def setup_api_key(self) -> None:
        """Setup Anthropic API key"""
        if "ANTHROPIC_API_KEY" not in os.environ or os.environ["ANTHROPIC_API_KEY"].strip() == "":
            print("🔑 Anthropic API key not found in environment variables.")
            print("💡 You can get your API key from: https://console.anthropic.com/")
            api_key = input("Please enter your Anthropic API key: ").strip()
            if not api_key:
                raise ValueError("Anthropic API key cannot be empty!")
            os.environ['ANTHROPIC_API_KEY'] = api_key
            print("✅ Anthropic API key is set successfully!")
        else:
            print("✅ Anthropic API key is already set.")
    
    def create_llm(self, model_name: str, temperature: float) -> Any:
        """Create Anthropic LLM instance"""
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model=model_name, temperature=temperature)
    
    def get_provider_name(self) -> str:
        return "Anthropic"


class BedrockProvider(ModelProvider):
    """AWS Bedrock model provider implementation"""
    
    def setup_api_key(self) -> None:
        """Setup AWS credentials for Bedrock"""
        # Check for AWS credentials
        aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID', '').strip()
        aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY', '').strip()
        aws_region = os.environ.get('AWS_DEFAULT_REGION', BEDROCK_REGION).strip()
        
        if not aws_access_key or not aws_secret_key:
            print("🔑 AWS credentials not found in environment variables.")
            print("💡 You need AWS Access Key ID and Secret Access Key to use Bedrock.")
            print("💡 You can get these from: https://console.aws.amazon.com/iam/")
            
            if not aws_access_key:
                aws_access_key = input("Please enter your AWS Access Key ID: ").strip()
                if not aws_access_key:
                    raise ValueError("AWS Access Key ID cannot be empty!")
                os.environ['AWS_ACCESS_KEY_ID'] = aws_access_key
            
            if not aws_secret_key:
                aws_secret_key = input("Please enter your AWS Secret Access Key: ").strip()
                if not aws_secret_key:
                    raise ValueError("AWS Secret Access Key cannot be empty!")
                os.environ['AWS_SECRET_ACCESS_KEY'] = aws_secret_key
            
            if not aws_region:
                region_input = input(f"Please enter your AWS region (default: {BEDROCK_REGION}): ").strip()
                aws_region = region_input if region_input else BEDROCK_REGION
                os.environ['AWS_DEFAULT_REGION'] = aws_region
            
            print("✅ AWS credentials are set successfully!")
        else:
            print("✅ AWS credentials are already set.")
            
        # Set the region for Bedrock
        if not os.environ.get('AWS_DEFAULT_REGION'):
            os.environ['AWS_DEFAULT_REGION'] = aws_region or BEDROCK_REGION
    
    def create_llm(self, model_name: str, temperature: float) -> Any:
        """Create AWS Bedrock LLM instance"""
        try:
            from langchain_aws import ChatBedrock
            return ChatBedrock(
                model_id=model_name,
                model_kwargs={"temperature": temperature},
                region_name=os.environ.get('AWS_DEFAULT_REGION', BEDROCK_REGION)
            )
        except ImportError:
            raise ImportError("langchain-aws package is required for Bedrock support. "
                            "Install it with: pip install langchain-aws boto3")
    
    def get_provider_name(self) -> str:
        return "AWS Bedrock"


class ModelProviderFactory:
    """Factory class for creating model providers"""
    
    _providers = {
        'openai': OpenAIProvider,
        'anthropic': AnthropicProvider,
        'bedrock': BedrockProvider
    }
    
    @classmethod
    def create_provider(cls, provider_name: str) -> ModelProvider:
        """Create a model provider instance"""
        provider_name = provider_name.lower()
        if provider_name not in cls._providers:
            raise ValueError(f"Unsupported provider: {provider_name}. "
                           f"Supported providers: {list(cls._providers.keys())}")
        return cls._providers[provider_name]()
    
    @classmethod
    def get_supported_providers(cls) -> list:
        """Get list of supported providers"""
        return list(cls._providers.keys())


class LLMManager:
    """Unified LLM manager that works with multiple AI providers"""
    
    def __init__(self):
        self.provider = ModelProviderFactory.create_provider(PROVIDER)
        self.provider.setup_api_key()
        self._llm_cache: Dict[str, Any] = {}
        print(f"✅ LLM Manager initialized with {self.provider.get_provider_name()} provider!")
    
    def get_llm(self, model_name: str = DEFAULT_MODEL, temperature: float = DEFAULT_TEMPERATURE) -> Any:
        """Get LLM instance (cached for performance)"""
        cache_key = f"{model_name}_{temperature}"
        if cache_key not in self._llm_cache:
            try:
                self._llm_cache[cache_key] = self.provider.create_llm(model_name, temperature)
                print(f"✅ Created {self.provider.get_provider_name()} LLM instance: {model_name}")
            except Exception as e:
                raise RuntimeError(f"Failed to create LLM instance: {e}")
        return self._llm_cache[cache_key]
    
    def get_gpt35_llm(self) -> Any:
        """Get default model LLM instance (maintains backward compatibility)"""
        return self.get_llm(DEFAULT_MODEL, DEFAULT_TEMPERATURE)
    
    def get_gpt4_llm(self) -> Any:
        """Get advanced model LLM instance (maintains backward compatibility)"""
        return self.get_llm(GPT4_MODEL, GPT4_TEMPERATURE)
    
    def get_provider_info(self) -> Dict[str, str]:
        """Get information about the current provider"""
        return {
            "provider": self.provider.get_provider_name(),
            "default_model": DEFAULT_MODEL,
            "advanced_model": GPT4_MODEL
        }
