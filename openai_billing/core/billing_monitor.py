"""
Core billing monitor that tracks usage and enforces limits.
"""

import logging
import warnings
from typing import Optional, Dict, Any, Callable
from datetime import datetime

from ..config.manager import ConfigManager
from ..models.billing_models import BillingConfig
from .token_counter import TokenCounter
from .exceptions import (
    BillingException, 
    ThresholdExceededException, 
    ModelNotConfiguredException
)


class BillingMonitor:
    """Main billing monitor class that tracks usage and enforces limits."""
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """
        Initialize the billing monitor.
        
        Args:
            config_manager: Optional custom config manager. If None, creates default.
        """
        self.config_manager = config_manager or ConfigManager()
        self.token_counter = TokenCounter()
        self.logger = logging.getLogger(__name__)
        
        # Callbacks for different events
        self.on_threshold_warning: Optional[Callable[[str, Dict[str, Any]], None]] = None
        self.on_threshold_exceeded: Optional[Callable[[str, Dict[str, Any]], None]] = None
        self.on_usage_update: Optional[Callable[[Dict[str, Any]], None]] = None
        
        # Load configuration
        self._config = self.config_manager.load_config()
    
    @property
    def config(self) -> BillingConfig:
        """Get the current billing configuration."""
        return self._config
    
    def refresh_config(self) -> None:
        """Reload configuration from file."""
        self._config = self.config_manager.load_config()
    
    def is_enabled(self) -> bool:
        """Check if billing monitoring is enabled."""
        return self._config.enabled
    
    def track_usage(self, model_name: str, input_tokens: int, output_tokens: int,
                   request_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Track token usage for a specific model.
        
        Args:
            model_name: Name of the model used
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            request_data: Optional request data for logging
            
        Returns:
            Dictionary with usage information and warnings
            
        Raises:
            ThresholdExceededException: If hard limits are exceeded
            ModelNotConfiguredException: If model is not configured
        """
        if not self.is_enabled():
            return {"enabled": False}
        
        # Check if model is configured
        if not self._config.get_model_config(model_name):
            if self.config.models:  # Only raise if we have other models configured
                raise ModelNotConfiguredException(model_name)
            else:
                # If no models are configured, log warning and continue
                self.logger.warning(f"Model '{model_name}' not configured, using default pricing")
        
        # Check for daily/monthly resets
        self._config.check_daily_reset()
        self._config.check_monthly_reset()
        
        # Calculate cost and update usage
        cost = self._config.update_usage(model_name, input_tokens, output_tokens)
        
        # Check thresholds
        threshold_warnings = self._config.check_thresholds()
        
        # Prepare usage info
        usage_info = {
            "model_name": model_name,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost": cost,
            "total_cost": self._config.usage_stats.total_cost,
            "daily_cost": self._config.usage_stats.daily_cost,
            "monthly_cost": self._config.usage_stats.monthly_cost,
            "warnings": threshold_warnings,
            "timestamp": datetime.now().isoformat()
        }
        
        # Handle threshold warnings and limits
        self._handle_threshold_warnings(threshold_warnings, usage_info)
        
        # Save configuration if auto_save is enabled
        if self._config.auto_save:
            self.config_manager.save_config(self._config)
        
        # Call usage update callback
        if self.on_usage_update:
            try:
                self.on_usage_update(usage_info)
            except Exception as e:
                self.logger.error(f"Error in usage update callback: {e}")
        
        return usage_info
    
    def track_openai_response(self, response_data: Dict[str, Any], model_name: str,
                            request_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Track usage from an OpenAI API response.
        
        Args:
            response_data: The API response data
            model_name: Name of the model used
            request_data: Optional request data
            
        Returns:
            Dictionary with usage information
        """
        try:
            # Extract token usage from response
            input_tokens, output_tokens = self.token_counter.estimate_tokens_from_response(
                response_data, model_name
            )
            
            return self.track_usage(model_name, input_tokens, output_tokens, request_data)
            
        except Exception as e:
            self.logger.error(f"Error tracking OpenAI response: {e}")
            return {"error": str(e)}
    
    def estimate_cost(self, model_name: str, input_tokens: int, output_tokens: int) -> Optional[float]:
        """
        Estimate cost for given token usage without tracking it.
        
        Args:
            model_name: Name of the model
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Estimated cost in USD, or None if model not configured
        """
        return self._config.calculate_cost(model_name, input_tokens, output_tokens)
    
    def check_limits_before_request(self, model_name: str, estimated_tokens: int) -> Dict[str, Any]:
        """
        Check if a request would exceed limits before making it.
        
        Args:
            model_name: Name of the model
            estimated_tokens: Estimated tokens for the request
            
        Returns:
            Dictionary with check results
        """
        if not self.is_enabled():
            return {"allowed": True, "enabled": False}
        
        # Estimate cost for the request
        estimated_cost = self.estimate_cost(model_name, estimated_tokens, 0)
        if estimated_cost is None:
            estimated_cost = 0.0
        
        current_stats = self._config.usage_stats
        thresholds = self._config.thresholds
        
        result = {
            "allowed": True,
            "warnings": [],
            "estimated_cost": estimated_cost,
            "current_daily_cost": current_stats.daily_cost,
            "current_monthly_cost": current_stats.monthly_cost,
        }
        
        # Check daily cost limit
        if thresholds.daily_cost_limit:
            projected_daily_cost = current_stats.daily_cost + estimated_cost
            if projected_daily_cost > thresholds.daily_cost_limit:
                result["allowed"] = False
                result["warnings"].append({
                    "type": "daily_cost_limit",
                    "message": f"Request would exceed daily cost limit",
                    "current": current_stats.daily_cost,
                    "projected": projected_daily_cost,
                    "limit": thresholds.daily_cost_limit
                })
        
        # Check monthly cost limit
        if thresholds.monthly_cost_limit:
            projected_monthly_cost = current_stats.monthly_cost + estimated_cost
            if projected_monthly_cost > thresholds.monthly_cost_limit:
                result["allowed"] = False
                result["warnings"].append({
                    "type": "monthly_cost_limit", 
                    "message": f"Request would exceed monthly cost limit",
                    "current": current_stats.monthly_cost,
                    "projected": projected_monthly_cost,
                    "limit": thresholds.monthly_cost_limit
                })
        
        # Check daily token limit
        if thresholds.daily_token_limit:
            current_daily_tokens = current_stats.daily_input_tokens + current_stats.daily_output_tokens
            projected_daily_tokens = current_daily_tokens + estimated_tokens
            if projected_daily_tokens > thresholds.daily_token_limit:
                result["allowed"] = False
                result["warnings"].append({
                    "type": "daily_token_limit",
                    "message": f"Request would exceed daily token limit",
                    "current": current_daily_tokens,
                    "projected": projected_daily_tokens,
                    "limit": thresholds.daily_token_limit
                })
        
        # Check monthly token limit
        if thresholds.monthly_token_limit:
            current_monthly_tokens = current_stats.monthly_input_tokens + current_stats.monthly_output_tokens
            projected_monthly_tokens = current_monthly_tokens + estimated_tokens
            if projected_monthly_tokens > thresholds.monthly_token_limit:
                result["allowed"] = False
                result["warnings"].append({
                    "type": "monthly_token_limit",
                    "message": f"Request would exceed monthly token limit",
                    "current": current_monthly_tokens,
                    "projected": projected_monthly_tokens,
                    "limit": thresholds.monthly_token_limit
                })
        
        return result
    
    def get_usage_summary(self) -> Dict[str, Any]:
        """Get a summary of current usage statistics."""
        stats = self._config.usage_stats
        thresholds = self._config.thresholds
        
        summary = {
            "total_requests": stats.total_requests,
            "daily_requests": stats.daily_requests,
            "monthly_requests": stats.monthly_requests,
            "total_cost": stats.total_cost,
            "daily_cost": stats.daily_cost,
            "monthly_cost": stats.monthly_cost,
            "total_input_tokens": stats.total_input_tokens,
            "total_output_tokens": stats.total_output_tokens,
            "daily_input_tokens": stats.daily_input_tokens,
            "daily_output_tokens": stats.daily_output_tokens,
            "monthly_input_tokens": stats.monthly_input_tokens,
            "monthly_output_tokens": stats.monthly_output_tokens,
            "last_reset_date": stats.last_reset_date.isoformat(),
            "last_daily_reset": stats.last_daily_reset.isoformat(),
            "last_monthly_reset": stats.last_monthly_reset.isoformat(),
        }
        
        # Add threshold information
        if thresholds.daily_cost_limit:
            summary["daily_cost_limit"] = thresholds.daily_cost_limit
            summary["daily_cost_usage_percent"] = (stats.daily_cost / thresholds.daily_cost_limit) * 100
        
        if thresholds.monthly_cost_limit:
            summary["monthly_cost_limit"] = thresholds.monthly_cost_limit
            summary["monthly_cost_usage_percent"] = (stats.monthly_cost / thresholds.monthly_cost_limit) * 100
        
        if thresholds.daily_token_limit:
            daily_tokens = stats.daily_input_tokens + stats.daily_output_tokens
            summary["daily_token_limit"] = thresholds.daily_token_limit
            summary["daily_token_usage_percent"] = (daily_tokens / thresholds.daily_token_limit) * 100
        
        if thresholds.monthly_token_limit:
            monthly_tokens = stats.monthly_input_tokens + stats.monthly_output_tokens
            summary["monthly_token_limit"] = thresholds.monthly_token_limit
            summary["monthly_token_usage_percent"] = (monthly_tokens / thresholds.monthly_token_limit) * 100
        
        return summary
    
    def reset_usage_stats(self, reset_type: str = "all") -> None:
        """
        Reset usage statistics.
        
        Args:
            reset_type: Type of reset - "all", "daily", or "monthly"
        """
        self.config_manager.reset_usage_stats(reset_type)
        self.refresh_config()
    
    def _handle_threshold_warnings(self, warnings: Dict[str, Any], usage_info: Dict[str, Any]) -> None:
        """Handle threshold warnings and exceeded limits."""
        
        # Check for hard limits (throw exceptions)
        exceeded_types = []
        for warning_type in warnings:
            if warning_type.endswith("_exceeded"):
                exceeded_types.append(warning_type)
        
        if exceeded_types:
            # Call threshold exceeded callback
            if self.on_threshold_exceeded:
                try:
                    self.on_threshold_exceeded(exceeded_types[0], usage_info)
                except Exception as e:
                    self.logger.error(f"Error in threshold exceeded callback: {e}")
            
            # Raise exception for the first exceeded threshold
            exceeded_type = exceeded_types[0]
            if exceeded_type == "daily_cost_exceeded":
                raise ThresholdExceededException(
                    f"Daily cost limit exceeded: ${usage_info['daily_cost']:.4f} >= ${self._config.thresholds.daily_cost_limit}",
                    "daily_cost",
                    usage_info['daily_cost'],
                    self._config.thresholds.daily_cost_limit
                )
            elif exceeded_type == "monthly_cost_exceeded":
                raise ThresholdExceededException(
                    f"Monthly cost limit exceeded: ${usage_info['monthly_cost']:.4f} >= ${self._config.thresholds.monthly_cost_limit}",
                    "monthly_cost",
                    usage_info['monthly_cost'],
                    self._config.thresholds.monthly_cost_limit
                )
            elif exceeded_type == "daily_token_exceeded":
                daily_tokens = self._config.usage_stats.daily_input_tokens + self._config.usage_stats.daily_output_tokens
                raise ThresholdExceededException(
                    f"Daily token limit exceeded: {daily_tokens} >= {self._config.thresholds.daily_token_limit}",
                    "daily_token",
                    daily_tokens,
                    self._config.thresholds.daily_token_limit
                )
            elif exceeded_type == "monthly_token_exceeded":
                monthly_tokens = self._config.usage_stats.monthly_input_tokens + self._config.usage_stats.monthly_output_tokens
                raise ThresholdExceededException(
                    f"Monthly token limit exceeded: {monthly_tokens} >= {self._config.thresholds.monthly_token_limit}",
                    "monthly_token",
                    monthly_tokens,
                    self._config.thresholds.monthly_token_limit
                )
        
        # Handle warning thresholds
        warning_types = [w for w in warnings if w.endswith("_warning")]
        if warning_types:
            # Call warning callback
            if self.on_threshold_warning:
                try:
                    self.on_threshold_warning(warning_types[0], usage_info)
                except Exception as e:
                    self.logger.error(f"Error in threshold warning callback: {e}")
            
            # Issue warnings
            for warning_type in warning_types:
                if warning_type == "daily_cost_warning":
                    warnings.warn(
                        f"Daily cost approaching limit: ${usage_info['daily_cost']:.4f} "
                        f"(limit: ${self._config.thresholds.daily_cost_limit})",
                        UserWarning
                    )
                elif warning_type == "monthly_cost_warning":
                    warnings.warn(
                        f"Monthly cost approaching limit: ${usage_info['monthly_cost']:.4f} "
                        f"(limit: ${self._config.thresholds.monthly_cost_limit})",
                        UserWarning
                    )
                elif warning_type == "daily_token_warning":
                    daily_tokens = self._config.usage_stats.daily_input_tokens + self._config.usage_stats.daily_output_tokens
                    warnings.warn(
                        f"Daily tokens approaching limit: {daily_tokens} "
                        f"(limit: {self._config.thresholds.daily_token_limit})",
                        UserWarning
                    )
                elif warning_type == "monthly_token_warning":
                    monthly_tokens = self._config.usage_stats.monthly_input_tokens + self._config.usage_stats.monthly_output_tokens
                    warnings.warn(
                        f"Monthly tokens approaching limit: {monthly_tokens} "
                        f"(limit: {self._config.thresholds.monthly_token_limit})",
                        UserWarning
                    )
