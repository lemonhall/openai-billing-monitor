"""
Data models for billing configuration and usage tracking.
"""

from typing import Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ModelConfig(BaseModel):
    """Configuration for a specific model's billing."""
    
    name: str = Field(..., description="Model name (e.g., 'gpt-4', 'qwen-plus')")
    input_token_price: float = Field(..., description="Price per 1000 input tokens in USD")
    output_token_price: float = Field(..., description="Price per 1000 output tokens in USD")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens for this model")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "gpt-4",
                "input_token_price": 0.03,
                "output_token_price": 0.06,
                "max_tokens": 8192
            }
        }


class ThresholdConfig(BaseModel):
    """Threshold configuration for cost and token limits."""
    
    daily_cost_limit: Optional[float] = Field(None, description="Daily cost limit in USD")
    monthly_cost_limit: Optional[float] = Field(None, description="Monthly cost limit in USD")
    daily_token_limit: Optional[int] = Field(None, description="Daily token limit")
    monthly_token_limit: Optional[int] = Field(None, description="Monthly token limit")
    warning_threshold: float = Field(0.8, description="Warning threshold as percentage (0.0-1.0)")


class UsageStats(BaseModel):
    """Usage statistics for tracking token consumption and costs."""
    
    total_input_tokens: int = Field(default=0, description="Total input tokens used")
    total_output_tokens: int = Field(default=0, description="Total output tokens used")
    total_cost: float = Field(default=0.0, description="Total cost in USD")
    daily_input_tokens: int = Field(default=0, description="Daily input tokens used")
    daily_output_tokens: int = Field(default=0, description="Daily output tokens used")
    daily_cost: float = Field(default=0.0, description="Daily cost in USD")
    monthly_input_tokens: int = Field(default=0, description="Monthly input tokens used")
    monthly_output_tokens: int = Field(default=0, description="Monthly output tokens used")
    monthly_cost: float = Field(default=0.0, description="Monthly cost in USD")
    last_reset_date: datetime = Field(default_factory=datetime.now, description="Last reset date")
    last_daily_reset: datetime = Field(default_factory=datetime.now, description="Last daily reset")
    last_monthly_reset: datetime = Field(default_factory=datetime.now, description="Last monthly reset")
    request_count: int = Field(default=0, description="Total number of API requests")
    total_requests: int = Field(default=0, description="Total number of API requests (alias for request_count)")
    daily_requests: int = Field(default=0, description="Daily number of API requests")
    monthly_requests: int = Field(default=0, description="Monthly number of API requests")
    
    def reset_daily_stats(self) -> None:
        """Reset daily statistics."""
        self.daily_input_tokens = 0
        self.daily_output_tokens = 0
        self.daily_cost = 0.0
        self.daily_requests = 0
        self.last_daily_reset = datetime.now()
    
    def reset_monthly_stats(self) -> None:
        """Reset monthly statistics."""
        self.monthly_input_tokens = 0
        self.monthly_output_tokens = 0
        self.monthly_cost = 0.0
        self.monthly_requests = 0
        self.last_monthly_reset = datetime.now()
    
    def reset_all_stats(self) -> None:
        """Reset all statistics."""
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0
        self.daily_input_tokens = 0
        self.daily_output_tokens = 0
        self.daily_cost = 0.0
        self.monthly_input_tokens = 0
        self.monthly_output_tokens = 0
        self.monthly_cost = 0.0
        self.request_count = 0
        self.total_requests = 0
        self.daily_requests = 0
        self.monthly_requests = 0
        self.last_reset_date = datetime.now()
        self.last_daily_reset = datetime.now()
        self.last_monthly_reset = datetime.now()


class BillingConfig(BaseModel):
    """Main billing configuration."""
    
    models: Dict[str, ModelConfig] = Field(default_factory=dict, description="Model configurations")
    thresholds: ThresholdConfig = Field(default_factory=ThresholdConfig, description="Threshold configurations")
    usage_stats: UsageStats = Field(default_factory=UsageStats, description="Current usage statistics")
    enabled: bool = Field(default=True, description="Whether billing monitoring is enabled")
    auto_save: bool = Field(default=True, description="Automatically save usage stats")
    config_file_path: Optional[str] = Field(None, description="Path to configuration file")
    
    def add_model_config(self, model_config: ModelConfig) -> None:
        """Add a model configuration."""
        self.models[model_config.name] = model_config
    
    def get_model_config(self, model_name: str) -> Optional[ModelConfig]:
        """Get model configuration by name."""
        return self.models.get(model_name)
    
    def calculate_cost(self, model_name: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for given token usage."""
        model_config = self.get_model_config(model_name)
        if not model_config:
            return 0.0
        
        input_cost = (input_tokens / 1000) * model_config.input_token_price
        output_cost = (output_tokens / 1000) * model_config.output_token_price
        return input_cost + output_cost
    
    def update_usage(self, model_name: str, input_tokens: int, output_tokens: int) -> float:
        """Update usage statistics and return the cost."""
        cost = self.calculate_cost(model_name, input_tokens, output_tokens)
        
        # Update totals
        self.usage_stats.total_input_tokens += input_tokens
        self.usage_stats.total_output_tokens += output_tokens
        self.usage_stats.total_cost += cost
        self.usage_stats.request_count += 1
        self.usage_stats.total_requests += 1  # Keep both fields in sync
        
        # Update daily stats
        self.usage_stats.daily_input_tokens += input_tokens
        self.usage_stats.daily_output_tokens += output_tokens
        self.usage_stats.daily_cost += cost
        self.usage_stats.daily_requests += 1
        
        # Update monthly stats
        self.usage_stats.monthly_input_tokens += input_tokens
        self.usage_stats.monthly_output_tokens += output_tokens
        self.usage_stats.monthly_cost += cost
        self.usage_stats.monthly_requests += 1
        
        return cost
    
    def check_daily_reset(self) -> None:
        """Check if daily stats should be reset."""
        now = datetime.now()
        if now.date() > self.usage_stats.last_daily_reset.date():
            self.usage_stats.reset_daily_stats()
    
    def check_monthly_reset(self) -> None:
        """Check if monthly stats should be reset."""
        now = datetime.now()
        if (now.year > self.usage_stats.last_monthly_reset.year or 
            now.month > self.usage_stats.last_monthly_reset.month):
            self.usage_stats.reset_monthly_stats()
    
    def check_thresholds(self) -> Dict[str, Any]:
        """Check if any thresholds are exceeded."""
        warnings = {}
        
        # Check daily limits
        if self.thresholds.daily_cost_limit:
            if self.usage_stats.daily_cost >= self.thresholds.daily_cost_limit:
                warnings["daily_cost_exceeded"] = True
            elif (self.usage_stats.daily_cost >= 
                  self.thresholds.daily_cost_limit * self.thresholds.warning_threshold):
                warnings["daily_cost_warning"] = True
        
        if self.thresholds.daily_token_limit:
            daily_tokens = self.usage_stats.daily_input_tokens + self.usage_stats.daily_output_tokens
            if daily_tokens >= self.thresholds.daily_token_limit:
                warnings["daily_token_exceeded"] = True
            elif daily_tokens >= self.thresholds.daily_token_limit * self.thresholds.warning_threshold:
                warnings["daily_token_warning"] = True
        
        # Check monthly limits
        if self.thresholds.monthly_cost_limit:
            if self.usage_stats.monthly_cost >= self.thresholds.monthly_cost_limit:
                warnings["monthly_cost_exceeded"] = True
            elif (self.usage_stats.monthly_cost >= 
                  self.thresholds.monthly_cost_limit * self.thresholds.warning_threshold):
                warnings["monthly_cost_warning"] = True
        
        if self.thresholds.monthly_token_limit:
            monthly_tokens = self.usage_stats.monthly_input_tokens + self.usage_stats.monthly_output_tokens
            if monthly_tokens >= self.thresholds.monthly_token_limit:
                warnings["monthly_token_exceeded"] = True
            elif monthly_tokens >= self.thresholds.monthly_token_limit * self.thresholds.warning_threshold:
                warnings["monthly_token_warning"] = True
        
        return warnings
