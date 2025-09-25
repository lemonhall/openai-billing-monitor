"""
Default model configurations for popular AI models.
Prices are based on public pricing as of 2024.
"""

from typing import Dict, List, Optional
from ..models.billing_models import ModelConfig


def get_default_model_configs() -> Dict[str, ModelConfig]:
    """Get default model configurations for popular AI models."""
    
    configs = {
        # OpenAI Models
        "gpt-4": ModelConfig(
            name="gpt-4",
            input_token_price=0.03,
            output_token_price=0.06,
            max_tokens=8192
        ),
        "gpt-4-32k": ModelConfig(
            name="gpt-4-32k",
            input_token_price=0.06,
            output_token_price=0.12,
            max_tokens=32768
        ),
        "gpt-4-turbo": ModelConfig(
            name="gpt-4-turbo",
            input_token_price=0.01,
            output_token_price=0.03,
            max_tokens=128000
        ),
        "gpt-4o": ModelConfig(
            name="gpt-4o",
            input_token_price=0.005,
            output_token_price=0.015,
            max_tokens=128000
        ),
        "gpt-4o-mini": ModelConfig(
            name="gpt-4o-mini",
            input_token_price=0.00015,
            output_token_price=0.0006,
            max_tokens=128000
        ),
        "gpt-3.5-turbo": ModelConfig(
            name="gpt-3.5-turbo",
            input_token_price=0.0015,
            output_token_price=0.002,
            max_tokens=16385
        ),
        "gpt-3.5-turbo-16k": ModelConfig(
            name="gpt-3.5-turbo-16k",
            input_token_price=0.003,
            output_token_price=0.004,
            max_tokens=16385
        ),
        
        # Qwen Models (Alibaba Cloud)
        "qwen-turbo": ModelConfig(
            name="qwen-turbo",
            input_token_price=0.002,
            output_token_price=0.006,
            max_tokens=8192
        ),
        "qwen-plus": ModelConfig(
            name="qwen-plus",
            input_token_price=0.004,
            output_token_price=0.012,
            max_tokens=32768
        ),
        "qwen-max": ModelConfig(
            name="qwen-max",
            input_token_price=0.02,
            output_token_price=0.06,
            max_tokens=8192
        ),
        "qwen-max-longcontext": ModelConfig(
            name="qwen-max-longcontext",
            input_token_price=0.02,
            output_token_price=0.06,
            max_tokens=30000
        ),
        
        # Claude Models (Anthropic)
        "claude-3-opus": ModelConfig(
            name="claude-3-opus",
            input_token_price=0.015,
            output_token_price=0.075,
            max_tokens=200000
        ),
        "claude-3-sonnet": ModelConfig(
            name="claude-3-sonnet",
            input_token_price=0.003,
            output_token_price=0.015,
            max_tokens=200000
        ),
        "claude-3-haiku": ModelConfig(
            name="claude-3-haiku",
            input_token_price=0.00025,
            output_token_price=0.00125,
            max_tokens=200000
        ),
        
        # Gemini Models (Google)
        "gemini-pro": ModelConfig(
            name="gemini-pro",
            input_token_price=0.0005,
            output_token_price=0.0015,
            max_tokens=32768
        ),
        "gemini-pro-vision": ModelConfig(
            name="gemini-pro-vision",
            input_token_price=0.0005,
            output_token_price=0.0015,
            max_tokens=16384
        ),
        
        # DeepSeek Models
        "deepseek-chat": ModelConfig(
            name="deepseek-chat",
            input_token_price=0.00014,
            output_token_price=0.00028,
            max_tokens=32768
        ),
        "deepseek-coder": ModelConfig(
            name="deepseek-coder",
            input_token_price=0.00014,
            output_token_price=0.00028,
            max_tokens=16384
        ),
        
        # Moonshot Models
        "moonshot-v1-8k": ModelConfig(
            name="moonshot-v1-8k",
            input_token_price=0.001,
            output_token_price=0.001,
            max_tokens=8192
        ),
        "moonshot-v1-32k": ModelConfig(
            name="moonshot-v1-32k",
            input_token_price=0.002,
            output_token_price=0.002,
            max_tokens=32768
        ),
        "moonshot-v1-128k": ModelConfig(
            name="moonshot-v1-128k",
            input_token_price=0.008,
            output_token_price=0.008,
            max_tokens=131072
        ),
        
        # Baichuan Models
        "baichuan2-turbo": ModelConfig(
            name="baichuan2-turbo",
            input_token_price=0.008,
            output_token_price=0.008,
            max_tokens=32768
        ),
        "baichuan2-turbo-192k": ModelConfig(
            name="baichuan2-turbo-192k",
            input_token_price=0.016,
            output_token_price=0.016,
            max_tokens=196608
        ),
    }
    
    return configs


def get_model_config_by_name(model_name: str) -> Optional[ModelConfig]:
    """Get a specific model configuration by name."""
    configs = get_default_model_configs()
    return configs.get(model_name)


def get_available_models() -> List[str]:
    """Get list of available model names."""
    return list(get_default_model_configs().keys())
