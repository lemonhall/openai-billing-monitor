"""
OpenAI API wrapper with billing monitoring.
"""

from typing import Any, Optional, Dict, List, Union
import openai
from openai import OpenAI

from .billing_monitor import BillingMonitor
from .decorators import monitor_openai_call, get_global_monitor


class OpenAIWrapper:
    """
    Wrapper for OpenAI client with built-in billing monitoring.
    
    This wrapper provides the same interface as the OpenAI client but adds
    automatic billing tracking and cost control.
    """
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 billing_monitor: Optional[BillingMonitor] = None,
                 **client_kwargs):
        """
        Initialize the OpenAI wrapper.
        
        Args:
            api_key: OpenAI API key. If None, uses environment variable.
            billing_monitor: Billing monitor instance. If None, uses global monitor.
            **client_kwargs: Additional arguments for OpenAI client.
        """
        self.billing_monitor = billing_monitor or get_global_monitor()
        
        # Initialize OpenAI client
        client_args = {}
        if api_key is not None:
            client_args['api_key'] = api_key
        client_args.update(client_kwargs)
        
        self.client = OpenAI(**client_args)
        
        # Wrap the completions and chat completions
        self._wrap_client_methods()
    
    def _wrap_client_methods(self):
        """Wrap OpenAI client methods with billing monitoring."""
        
        # Wrap chat completions
        original_chat_create = self.client.chat.completions.create
        
        @monitor_openai_call(monitor=self.billing_monitor)
        def monitored_chat_create(*args, **kwargs):
            return original_chat_create(*args, **kwargs)
        
        self.client.chat.completions.create = monitored_chat_create
        
        # Wrap completions (if available)
        if hasattr(self.client, 'completions'):
            original_completions_create = self.client.completions.create
            
            @monitor_openai_call(monitor=self.billing_monitor)
            def monitored_completions_create(*args, **kwargs):
                return original_completions_create(*args, **kwargs)
            
            self.client.completions.create = monitored_completions_create
        
        # Wrap embeddings
        if hasattr(self.client, 'embeddings'):
            original_embeddings_create = self.client.embeddings.create
            
            @monitor_openai_call(monitor=self.billing_monitor)
            def monitored_embeddings_create(*args, **kwargs):
                return original_embeddings_create(*args, **kwargs)
            
            self.client.embeddings.create = monitored_embeddings_create
    
    def __getattr__(self, name: str) -> Any:
        """Delegate attribute access to the wrapped client."""
        return getattr(self.client, name)
    
    def get_usage_summary(self) -> Dict[str, Any]:
        """Get billing usage summary."""
        return self.billing_monitor.get_usage_summary()
    
    def reset_usage_stats(self, reset_type: str = "all") -> None:
        """Reset usage statistics."""
        self.billing_monitor.reset_usage_stats(reset_type)
    
    def check_limits(self, model_name: str, estimated_tokens: int) -> Dict[str, Any]:
        """Check if a request would exceed limits."""
        return self.billing_monitor.check_limits_before_request(model_name, estimated_tokens)
    
    def estimate_cost(self, model_name: str, input_tokens: int, output_tokens: int) -> Optional[float]:
        """Estimate cost for given token usage."""
        return self.billing_monitor.estimate_cost(model_name, input_tokens, output_tokens)
    
    def set_threshold_callbacks(self, 
                               on_warning: Optional[callable] = None,
                               on_exceeded: Optional[callable] = None,
                               on_usage_update: Optional[callable] = None):
        """Set callback functions for threshold events."""
        if on_warning:
            self.billing_monitor.on_threshold_warning = on_warning
        if on_exceeded:
            self.billing_monitor.on_threshold_exceeded = on_exceeded
        if on_usage_update:
            self.billing_monitor.on_usage_update = on_usage_update


# Convenience functions for easy migration
def create_monitored_client(api_key: Optional[str] = None,
                          billing_monitor: Optional[BillingMonitor] = None,
                          **client_kwargs) -> OpenAIWrapper:
    """
    Create a monitored OpenAI client.
    
    This is a convenience function that creates an OpenAIWrapper instance.
    """
    return OpenAIWrapper(api_key=api_key, billing_monitor=billing_monitor, **client_kwargs)


def patch_openai_client(client: OpenAI, 
                       billing_monitor: Optional[BillingMonitor] = None) -> OpenAI:
    """
    Patch an existing OpenAI client with billing monitoring.
    
    Args:
        client: Existing OpenAI client instance
        billing_monitor: Billing monitor to use
        
    Returns:
        The patched client (same instance)
    """
    monitor = billing_monitor or get_global_monitor()
    
    # Wrap chat completions
    original_chat_create = client.chat.completions.create
    
    @monitor_openai_call(monitor=monitor)
    def monitored_chat_create(*args, **kwargs):
        return original_chat_create(*args, **kwargs)
    
    client.chat.completions.create = monitored_chat_create
    
    # Wrap completions (if available)
    if hasattr(client, 'completions'):
        original_completions_create = client.completions.create
        
        @monitor_openai_call(monitor=monitor)
        def monitored_completions_create(*args, **kwargs):
            return original_completions_create(*args, **kwargs)
        
        client.completions.create = monitored_completions_create
    
    # Wrap embeddings
    if hasattr(client, 'embeddings'):
        original_embeddings_create = client.embeddings.create
        
        @monitor_openai_call(monitor=monitor)
        def monitored_embeddings_create(*args, **kwargs):
            return original_embeddings_create(*args, **kwargs)
        
        client.embeddings.create = monitored_embeddings_create
    
    return client


# Context manager for temporary monitoring
class temporary_monitoring:
    """Context manager for temporary billing monitoring."""
    
    def __init__(self, billing_monitor: Optional[BillingMonitor] = None):
        self.billing_monitor = billing_monitor or get_global_monitor()
        self.original_enabled = None
    
    def __enter__(self):
        self.original_enabled = self.billing_monitor.config.enabled
        self.billing_monitor.config.enabled = True
        return self.billing_monitor
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.original_enabled is not None:
            self.billing_monitor.config.enabled = self.original_enabled


class disable_monitoring:
    """Context manager for temporarily disabling monitoring."""
    
    def __init__(self, billing_monitor: Optional[BillingMonitor] = None):
        self.billing_monitor = billing_monitor or get_global_monitor()
        self.original_enabled = None
    
    def __enter__(self):
        self.original_enabled = self.billing_monitor.config.enabled
        self.billing_monitor.config.enabled = False
        return self.billing_monitor
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.original_enabled is not None:
            self.billing_monitor.config.enabled = self.original_enabled
