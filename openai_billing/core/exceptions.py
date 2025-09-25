"""
Custom exceptions for the billing system.
"""


class BillingException(Exception):
    """Base exception for billing-related errors."""
    pass


class ThresholdExceededException(BillingException):
    """Raised when a usage threshold is exceeded."""
    
    def __init__(self, message: str, threshold_type: str, current_value: float, limit_value: float):
        super().__init__(message)
        self.threshold_type = threshold_type
        self.current_value = current_value
        self.limit_value = limit_value


class ModelNotConfiguredException(BillingException):
    """Raised when trying to use a model that hasn't been configured."""
    
    def __init__(self, model_name: str):
        super().__init__(f"Model '{model_name}' is not configured for billing monitoring.")
        self.model_name = model_name


class TokenCountingException(BillingException):
    """Raised when token counting fails."""
    pass


class ConfigurationException(BillingException):
    """Raised when there's an issue with configuration."""
    pass
