"""
Configuration manager for loading, saving, and managing billing configurations.
"""

import os
import json
import yaml
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from ..models.billing_models import BillingConfig, ModelConfig, UsageStats, ThresholdConfig
from .default_configs import get_default_model_configs


class ConfigManager:
    """Manager for billing configuration files."""
    
    DEFAULT_CONFIG_FILE = "openai_billing_config.yaml"
    DEFAULT_STATS_FILE = "openai_billing_stats.json"
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_dir: Directory to store configuration files. 
                       Defaults to user home directory.
        """
        if config_dir is None:
            config_dir = os.path.expanduser("~/.openai_billing")
        
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.config_file = self.config_dir / self.DEFAULT_CONFIG_FILE
        self.stats_file = self.config_dir / self.DEFAULT_STATS_FILE
        
        self._billing_config: Optional[BillingConfig] = None
    
    def load_config(self) -> BillingConfig:
        """Load billing configuration from file or create default."""
        if self._billing_config is not None:
            return self._billing_config
        
        # Try to load existing configuration
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
                
                # Parse the configuration
                billing_config = self._parse_config_data(config_data)
                
                # Load usage stats separately
                usage_stats = self.load_usage_stats()
                billing_config.usage_stats = usage_stats
                
                self._billing_config = billing_config
                return billing_config
            
            except Exception as e:
                print(f"Error loading configuration: {e}")
                print("Using default configuration.")
        
        # Create default configuration
        billing_config = self._create_default_config()
        self._billing_config = billing_config
        self.save_config(billing_config)
        
        return billing_config
    
    def save_config(self, billing_config: BillingConfig) -> None:
        """Save billing configuration to file."""
        try:
            # Prepare config data for saving (exclude usage stats)
            config_data = {
                "enabled": billing_config.enabled,
                "auto_save": billing_config.auto_save,
                "thresholds": {
                    "daily_cost_limit": billing_config.thresholds.daily_cost_limit,
                    "monthly_cost_limit": billing_config.thresholds.monthly_cost_limit,
                    "daily_token_limit": billing_config.thresholds.daily_token_limit,
                    "monthly_token_limit": billing_config.thresholds.monthly_token_limit,
                    "warning_threshold": billing_config.thresholds.warning_threshold,
                },
                "models": {}
            }
            
            # Add model configurations
            for name, model_config in billing_config.models.items():
                config_data["models"][name] = {
                    "name": model_config.name,
                    "input_token_price": model_config.input_token_price,
                    "output_token_price": model_config.output_token_price,
                    "max_tokens": model_config.max_tokens,
                }
            
            # Save configuration
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
            
            # Save usage stats separately
            self.save_usage_stats(billing_config.usage_stats)
            
            # Update the cached config
            self._billing_config = billing_config
            
        except Exception as e:
            print(f"Error saving configuration: {e}")
    
    def load_usage_stats(self) -> UsageStats:
        """Load usage statistics from file."""
        if not self.stats_file.exists():
            return UsageStats()
        
        try:
            with open(self.stats_file, 'r', encoding='utf-8') as f:
                stats_data = json.load(f)
            
            # Parse datetime fields
            for date_field in ['last_reset_date', 'last_daily_reset', 'last_monthly_reset']:
                if date_field in stats_data and stats_data[date_field]:
                    stats_data[date_field] = datetime.fromisoformat(stats_data[date_field])
            
            return UsageStats(**stats_data)
        
        except Exception as e:
            print(f"Error loading usage stats: {e}")
            return UsageStats()
    
    def save_usage_stats(self, usage_stats: UsageStats) -> None:
        """Save usage statistics to file."""
        try:
            # Convert to dictionary and handle datetime serialization
            stats_data = usage_stats.model_dump()
            
            # Convert datetime objects to ISO format strings
            for date_field in ['last_reset_date', 'last_daily_reset', 'last_monthly_reset']:
                if date_field in stats_data and stats_data[date_field]:
                    stats_data[date_field] = stats_data[date_field].isoformat()
            
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats_data, f, indent=2, ensure_ascii=False)
        
        except Exception as e:
            print(f"Error saving usage stats: {e}")
    
    def reset_usage_stats(self, reset_type: str = "all") -> None:
        """
        Reset usage statistics.
        
        Args:
            reset_type: Type of reset - "all", "daily", or "monthly"
        """
        config = self.load_config()
        
        if reset_type == "all":
            config.usage_stats.reset_all_stats()
        elif reset_type == "daily":
            config.usage_stats.reset_daily_stats()
        elif reset_type == "monthly":
            config.usage_stats.reset_monthly_stats()
        
        self.save_usage_stats(config.usage_stats)
    
    def add_model_config(self, model_config: ModelConfig) -> None:
        """Add or update a model configuration."""
        config = self.load_config()
        config.add_model_config(model_config)
        self.save_config(config)
    
    def remove_model_config(self, model_name: str) -> None:
        """Remove a model configuration."""
        config = self.load_config()
        if model_name in config.models:
            del config.models[model_name]
            self.save_config(config)
    
    def update_thresholds(self, threshold_config: ThresholdConfig) -> None:
        """Update threshold configuration."""
        config = self.load_config()
        config.thresholds = threshold_config
        self.save_config(config)
    
    def _create_default_config(self) -> BillingConfig:
        """Create a default billing configuration."""
        # Load default model configurations
        default_models = get_default_model_configs()
        
        # Create default threshold configuration
        default_thresholds = ThresholdConfig(
            daily_cost_limit=10.0,  # $10 per day
            monthly_cost_limit=100.0,  # $100 per month
            daily_token_limit=1000000,  # 1M tokens per day
            monthly_token_limit=10000000,  # 10M tokens per month
            warning_threshold=0.8  # 80% warning threshold
        )
        
        # Create billing configuration
        billing_config = BillingConfig(
            models=default_models,
            thresholds=default_thresholds,
            usage_stats=UsageStats(),
            enabled=True,
            auto_save=True,
            config_file_path=str(self.config_file)
        )
        
        return billing_config
    
    def _parse_config_data(self, config_data: Dict[str, Any]) -> BillingConfig:
        """Parse configuration data from file."""
        # Parse threshold configuration
        thresholds_data = config_data.get("thresholds", {})
        thresholds = ThresholdConfig(**thresholds_data)
        
        # Parse model configurations
        models = {}
        models_data = config_data.get("models", {})
        
        # Add default models first
        default_models = get_default_model_configs()
        models.update(default_models)
        
        # Override with custom configurations
        for name, model_data in models_data.items():
            models[name] = ModelConfig(**model_data)
        
        # Create billing configuration
        billing_config = BillingConfig(
            models=models,
            thresholds=thresholds,
            usage_stats=UsageStats(),  # Will be loaded separately
            enabled=config_data.get("enabled", True),
            auto_save=config_data.get("auto_save", True),
            config_file_path=str(self.config_file)
        )
        
        return billing_config
    
    def export_config(self, export_path: str) -> None:
        """Export configuration to a specific file."""
        config = self.load_config()
        
        export_file = Path(export_path)
        if export_file.suffix.lower() == '.json':
            # Export as JSON
            config_dict = config.model_dump()
            # Handle datetime serialization
            for date_field in ['last_reset_date', 'last_daily_reset', 'last_monthly_reset']:
                if hasattr(config_dict['usage_stats'], date_field):
                    date_val = config_dict['usage_stats'][date_field]
                    if date_val:
                        config_dict['usage_stats'][date_field] = date_val.isoformat()
            
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
        else:
            # Export as YAML (default)
            config_data = self._prepare_config_for_export(config)
            with open(export_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
    
    def _prepare_config_for_export(self, config: BillingConfig) -> Dict[str, Any]:
        """Prepare configuration data for export."""
        return {
            "enabled": config.enabled,
            "auto_save": config.auto_save,
            "thresholds": {
                "daily_cost_limit": config.thresholds.daily_cost_limit,
                "monthly_cost_limit": config.thresholds.monthly_cost_limit,
                "daily_token_limit": config.thresholds.daily_token_limit,
                "monthly_token_limit": config.thresholds.monthly_token_limit,
                "warning_threshold": config.thresholds.warning_threshold,
            },
            "models": {
                name: {
                    "name": model.name,
                    "input_token_price": model.input_token_price,
                    "output_token_price": model.output_token_price,
                    "max_tokens": model.max_tokens,
                }
                for name, model in config.models.items()
            }
        }
