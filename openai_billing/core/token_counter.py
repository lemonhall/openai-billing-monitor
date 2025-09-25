"""
Token counting utilities for different models and providers.
"""

import tiktoken
from typing import Optional, Dict, Any, List, Union
from .exceptions import TokenCountingException


class TokenCounter:
    """Utility class for counting tokens in different formats."""
    
    # Model encoding mappings
    MODEL_ENCODINGS = {
        # OpenAI models
        "gpt-4": "cl100k_base",
        "gpt-4-32k": "cl100k_base",
        "gpt-4-turbo": "cl100k_base",
        "gpt-4o": "o200k_base",
        "gpt-4o-mini": "o200k_base",
        "gpt-3.5-turbo": "cl100k_base",
        "gpt-3.5-turbo-16k": "cl100k_base",
        
        # For non-OpenAI models, we'll use cl100k_base as approximation
        "qwen-turbo": "cl100k_base",
        "qwen-plus": "cl100k_base", 
        "qwen-max": "cl100k_base",
        "qwen-max-longcontext": "cl100k_base",
        "claude-3-opus": "cl100k_base",
        "claude-3-sonnet": "cl100k_base",
        "claude-3-haiku": "cl100k_base",
        "gemini-pro": "cl100k_base",
        "gemini-pro-vision": "cl100k_base",
        "deepseek-chat": "cl100k_base",
        "deepseek-coder": "cl100k_base",
        "moonshot-v1-8k": "cl100k_base",
        "moonshot-v1-32k": "cl100k_base",
        "moonshot-v1-128k": "cl100k_base",
        "baichuan2-turbo": "cl100k_base",
        "baichuan2-turbo-192k": "cl100k_base",
    }
    
    def __init__(self):
        self._encoders: Dict[str, tiktoken.Encoding] = {}
    
    def _get_encoder(self, model_name: str) -> tiktoken.Encoding:
        """Get or create an encoder for the specified model."""
        encoding_name = self.MODEL_ENCODINGS.get(model_name, "cl100k_base")
        
        if encoding_name not in self._encoders:
            try:
                self._encoders[encoding_name] = tiktoken.get_encoding(encoding_name)
            except Exception as e:
                raise TokenCountingException(f"Failed to get encoding for {encoding_name}: {e}")
        
        return self._encoders[encoding_name]
    
    def count_tokens(self, text: str, model_name: str) -> int:
        """
        Count tokens in a text string for a specific model.
        
        Args:
            text: The text to count tokens for
            model_name: The name of the model
            
        Returns:
            Number of tokens
        """
        if not text:
            return 0
        
        try:
            encoder = self._get_encoder(model_name)
            return len(encoder.encode(text))
        except Exception as e:
            raise TokenCountingException(f"Failed to count tokens: {e}")
    
    def count_messages_tokens(self, messages: List[Dict[str, Any]], model_name: str) -> int:
        """
        Count tokens in a list of messages (OpenAI format).
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model_name: The name of the model
            
        Returns:
            Number of tokens including message formatting overhead
        """
        if not messages:
            return 0
        
        try:
            encoder = self._get_encoder(model_name)
            
            # Different models have different token counting rules
            if model_name.startswith("gpt-4") or model_name.startswith("gpt-3.5"):
                return self._count_openai_messages_tokens(messages, encoder, model_name)
            else:
                # For other models, use a simpler approximation
                return self._count_generic_messages_tokens(messages, encoder)
                
        except Exception as e:
            raise TokenCountingException(f"Failed to count message tokens: {e}")
    
    def _count_openai_messages_tokens(self, messages: List[Dict[str, Any]], 
                                    encoder: tiktoken.Encoding, model_name: str) -> int:
        """Count tokens for OpenAI-style messages with proper formatting."""
        
        # Token costs for message formatting (based on OpenAI's documentation)
        if model_name.startswith("gpt-4"):
            tokens_per_message = 3
            tokens_per_name = 1
        elif model_name.startswith("gpt-3.5-turbo"):
            if "0613" in model_name or "16k" in model_name:
                tokens_per_message = 3
                tokens_per_name = 1
            else:
                tokens_per_message = 4
                tokens_per_name = -1  # If there's a name, subtract 1 token
        else:
            tokens_per_message = 3
            tokens_per_name = 1
        
        num_tokens = 0
        
        for message in messages:
            num_tokens += tokens_per_message
            
            for key, value in message.items():
                if key == "content":
                    if isinstance(value, str):
                        num_tokens += len(encoder.encode(value))
                    elif isinstance(value, list):
                        # Handle multi-modal content
                        for content_item in value:
                            if isinstance(content_item, dict) and "text" in content_item:
                                num_tokens += len(encoder.encode(content_item["text"]))
                elif key == "role":
                    num_tokens += len(encoder.encode(value))
                elif key == "name":
                    num_tokens += len(encoder.encode(value))
                    if tokens_per_name > 0:
                        num_tokens += tokens_per_name
        
        # Add tokens for the assistant's reply
        num_tokens += 3
        
        return num_tokens
    
    def _count_generic_messages_tokens(self, messages: List[Dict[str, Any]], 
                                     encoder: tiktoken.Encoding) -> int:
        """Count tokens for generic message format (approximation)."""
        num_tokens = 0
        
        for message in messages:
            # Add tokens for role
            if "role" in message:
                num_tokens += len(encoder.encode(message["role"]))
            
            # Add tokens for content
            if "content" in message:
                content = message["content"]
                if isinstance(content, str):
                    num_tokens += len(encoder.encode(content))
                elif isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and "text" in item:
                            num_tokens += len(encoder.encode(item["text"]))
            
            # Add overhead for message formatting
            num_tokens += 4  # Approximate overhead per message
        
        return num_tokens
    
    def estimate_tokens_from_response(self, response_data: Dict[str, Any], 
                                    model_name: str) -> tuple[int, int]:
        """
        Estimate input and output tokens from an API response.
        
        Args:
            response_data: The API response data
            model_name: The name of the model used
            
        Returns:
            Tuple of (input_tokens, output_tokens)
        """
        try:
            # Try to get usage data from response first
            usage = response_data.get("usage", {})
            if usage:
                prompt_tokens = usage.get("prompt_tokens", 0)
                completion_tokens = usage.get("completion_tokens", 0)
                return prompt_tokens, completion_tokens
            
            # Fallback: estimate from content
            input_tokens = 0
            output_tokens = 0
            
            # Estimate output tokens from choices
            choices = response_data.get("choices", [])
            for choice in choices:
                message = choice.get("message", {})
                content = message.get("content", "")
                if content:
                    output_tokens += self.count_tokens(content, model_name)
            
            return input_tokens, output_tokens
            
        except Exception as e:
            raise TokenCountingException(f"Failed to estimate tokens from response: {e}")
    
    def get_supported_models(self) -> List[str]:
        """Get list of supported model names."""
        return list(self.MODEL_ENCODINGS.keys())
    
    def add_model_encoding(self, model_name: str, encoding_name: str) -> None:
        """
        Add a custom model encoding mapping.
        
        Args:
            model_name: Name of the model
            encoding_name: Name of the tiktoken encoding to use
        """
        self.MODEL_ENCODINGS[model_name] = encoding_name
