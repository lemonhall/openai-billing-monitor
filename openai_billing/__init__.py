"""
OpenAI Billing Monitor - A Python library for monitoring and controlling OpenAI API costs.

This library provides:
- Token usage monitoring
- Cost calculation and threshold management
- Low-invasive integration with OpenAI API
- GUI for configuration and monitoring
"""

from .core.billing_monitor import BillingMonitor
from .core.wrapper import OpenAIWrapper
from .models.billing_models import BillingConfig, ModelConfig, UsageStats
from .core.decorators import monitor_openai_call

__version__ = "0.1.0"
__all__ = [
    "BillingMonitor",
    "OpenAIWrapper", 
    "BillingConfig",
    "ModelConfig",
    "UsageStats",
    "monitor_openai_call",
]
