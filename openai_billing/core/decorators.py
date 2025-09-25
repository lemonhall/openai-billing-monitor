"""
Decorators for monitoring OpenAI API calls.
"""

import functools
import inspect
from typing import Any, Callable, Dict, Optional, Union

from .billing_monitor import BillingMonitor
from .token_counter import TokenCounter
from .exceptions import BillingException


# Global billing monitor instance
_global_monitor: Optional[BillingMonitor] = None


def set_global_monitor(monitor: BillingMonitor) -> None:
    """Set the global billing monitor instance."""
    global _global_monitor
    _global_monitor = monitor


def get_global_monitor() -> BillingMonitor:
    """Get or create the global billing monitor instance."""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = BillingMonitor()
    return _global_monitor


def monitor_openai_call(model_name: Optional[str] = None, 
                       monitor: Optional[BillingMonitor] = None,
                       pre_check: bool = True,
                       raise_on_limit: bool = True):
    """
    Decorator to monitor OpenAI API calls.
    
    Args:
        model_name: Name of the model. If None, tries to extract from function arguments.
        monitor: Billing monitor instance. If None, uses global monitor.
        pre_check: Whether to check limits before making the request.
        raise_on_limit: Whether to raise exceptions when limits are exceeded.
    
    Usage:
        @monitor_openai_call(model_name="gpt-4")
        def my_openai_call(**kwargs):
            return openai.ChatCompletion.create(**kwargs)
        
        # Or let it auto-detect the model
        @monitor_openai_call()
        def my_openai_call(model="gpt-4", **kwargs):
            return openai.ChatCompletion.create(model=model, **kwargs)
    """
    
    def decorator(func: Callable) -> Callable:
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get the billing monitor
            billing_monitor = monitor or get_global_monitor()
            
            if not billing_monitor.is_enabled():
                return func(*args, **kwargs)
            
            # Extract model name
            actual_model_name = model_name
            if actual_model_name is None:
                actual_model_name = _extract_model_name(func, args, kwargs)
            
            if not actual_model_name:
                # If we can't determine the model, just run the function
                return func(*args, **kwargs)
            
            # Pre-check limits if enabled
            if pre_check:
                try:
                    # Estimate tokens for pre-check
                    estimated_tokens = _estimate_request_tokens(func, args, kwargs, actual_model_name, billing_monitor.token_counter)
                    
                    check_result = billing_monitor.check_limits_before_request(actual_model_name, estimated_tokens)
                    
                    if not check_result["allowed"] and raise_on_limit:
                        warnings = check_result.get("warnings", [])
                        if warnings:
                            raise BillingException(f"Request blocked: {warnings[0]['message']}")
                
                except Exception as e:
                    if raise_on_limit:
                        raise
                    else:
                        billing_monitor.logger.warning(f"Pre-check failed: {e}")
            
            # Make the actual API call
            try:
                result = func(*args, **kwargs)
                
                # Track the usage after successful call
                try:
                    if hasattr(result, 'model_dump'):
                        # Pydantic model
                        response_data = result.model_dump()
                    elif hasattr(result, 'to_dict'):
                        # OpenAI response object
                        response_data = result.to_dict()
                    elif isinstance(result, dict):
                        # Already a dictionary
                        response_data = result
                    else:
                        # Try to convert to dict
                        response_data = dict(result) if result else {}
                    
                    usage_info = billing_monitor.track_openai_response(
                        response_data, actual_model_name, 
                        {"function": func.__name__, "args": args, "kwargs": kwargs}
                    )
                    
                    # Attach usage info to result if possible
                    if hasattr(result, '__dict__'):
                        result._billing_info = usage_info
                    
                except Exception as e:
                    billing_monitor.logger.error(f"Error tracking usage: {e}")
                    if raise_on_limit:
                        raise
                
                return result
                
            except Exception as e:
                if isinstance(e, BillingException):
                    raise
                # Re-raise the original exception
                raise
        
        return wrapper
    return decorator


def _extract_model_name(func: Callable, args: tuple, kwargs: dict) -> Optional[str]:
    """Extract model name from function arguments."""
    
    # Check kwargs first
    if 'model' in kwargs:
        return kwargs['model']
    
    # Check positional arguments
    try:
        sig = inspect.signature(func)
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()
        
        if 'model' in bound_args.arguments:
            return bound_args.arguments['model']
    except Exception:
        pass
    
    # Try common parameter names
    for param_name in ['model', 'model_name', 'engine']:
        if param_name in kwargs:
            return kwargs[param_name]
    
    return None


def _estimate_request_tokens(func: Callable, args: tuple, kwargs: dict, 
                           model_name: str, token_counter: TokenCounter) -> int:
    """Estimate tokens for a request."""
    
    try:
        # Look for messages parameter (chat completions)
        if 'messages' in kwargs:
            messages = kwargs['messages']
            if isinstance(messages, list):
                return token_counter.count_messages_tokens(messages, model_name)
        
        # Look for prompt parameter (completions)
        if 'prompt' in kwargs:
            prompt = kwargs['prompt']
            if isinstance(prompt, str):
                return token_counter.count_tokens(prompt, model_name)
            elif isinstance(prompt, list):
                total_tokens = 0
                for p in prompt:
                    if isinstance(p, str):
                        total_tokens += token_counter.count_tokens(p, model_name)
                return total_tokens
        
        # Look for input parameter (embeddings)
        if 'input' in kwargs:
            input_text = kwargs['input']
            if isinstance(input_text, str):
                return token_counter.count_tokens(input_text, model_name)
            elif isinstance(input_text, list):
                total_tokens = 0
                for text in input_text:
                    if isinstance(text, str):
                        total_tokens += token_counter.count_tokens(text, model_name)
                return total_tokens
        
        # Default estimation
        return 100  # Conservative estimate
        
    except Exception:
        return 100  # Fallback estimate


class OpenAIMonitorMixin:
    """Mixin class that can be added to OpenAI client classes."""
    
    def __init__(self, *args, billing_monitor: Optional[BillingMonitor] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._billing_monitor = billing_monitor or get_global_monitor()
    
    def _monitor_call(self, method_name: str, model_name: str, *args, **kwargs):
        """Monitor a method call."""
        if not self._billing_monitor.is_enabled():
            return getattr(super(), method_name)(*args, **kwargs)
        
        # Get the original method
        original_method = getattr(super(), method_name)
        
        # Apply monitoring
        monitored_method = monitor_openai_call(
            model_name=model_name,
            monitor=self._billing_monitor
        )(original_method)
        
        return monitored_method(*args, **kwargs)
