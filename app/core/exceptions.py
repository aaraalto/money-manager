"""
Custom exceptions for the Radiant Finance application.

These typed exceptions provide clear error categorization and 
user-friendly messages for different failure scenarios.
"""
from typing import Optional


class RadiantException(Exception):
    """Base exception for all Radiant-specific errors."""
    
    def __init__(
        self, 
        message: str, 
        user_message: Optional[str] = None,
        retry_allowed: bool = True,
        error_code: Optional[str] = None
    ):
        super().__init__(message)
        self.message = message
        self.user_message = user_message or message
        self.retry_allowed = retry_allowed
        self.error_code = error_code


# =============================================================================
# DATA ERRORS
# =============================================================================

class DataError(RadiantException):
    """Base class for data-related errors."""
    pass


class DataNotFoundError(DataError):
    """Raised when requested data cannot be found."""
    
    def __init__(self, resource: str, identifier: Optional[str] = None):
        message = f"{resource} not found"
        if identifier:
            message = f"{resource} with ID '{identifier}' not found"
        
        super().__init__(
            message=message,
            user_message=f"We couldn't find the requested {resource.lower()}. It may have been removed or doesn't exist.",
            retry_allowed=False,
            error_code="DATA_NOT_FOUND"
        )
        self.resource = resource
        self.identifier = identifier


class DataValidationError(DataError):
    """Raised when data fails validation."""
    
    def __init__(self, field: str, reason: str):
        super().__init__(
            message=f"Validation failed for '{field}': {reason}",
            user_message=f"There's an issue with the {field.replace('_', ' ')}: {reason}",
            retry_allowed=True,
            error_code="VALIDATION_ERROR"
        )
        self.field = field
        self.reason = reason


class DataCorruptionError(DataError):
    """Raised when data appears to be corrupted or invalid."""
    
    def __init__(self, resource: str, details: Optional[str] = None):
        message = f"Data corruption detected in {resource}"
        if details:
            message += f": {details}"
        
        super().__init__(
            message=message,
            user_message="We found an issue with your data. Please try refreshing, or contact support if this persists.",
            retry_allowed=True,
            error_code="DATA_CORRUPTION"
        )


# =============================================================================
# CALCULATION ERRORS
# =============================================================================

class CalculationError(RadiantException):
    """Base class for calculation-related errors."""
    pass


class InsufficientDataError(CalculationError):
    """Raised when there's not enough data to perform a calculation."""
    
    def __init__(self, calculation: str, missing: str):
        super().__init__(
            message=f"Cannot perform {calculation}: missing {missing}",
            user_message=f"We need more information to calculate your {calculation.replace('_', ' ')}. Please add {missing.replace('_', ' ')}.",
            retry_allowed=True,
            error_code="INSUFFICIENT_DATA"
        )


class InvalidScenarioError(CalculationError):
    """Raised when a scenario configuration is invalid."""
    
    def __init__(self, reason: str):
        super().__init__(
            message=f"Invalid scenario: {reason}",
            user_message=f"This scenario isn't valid: {reason}. Please adjust your settings.",
            retry_allowed=True,
            error_code="INVALID_SCENARIO"
        )


class SimulationOverflowError(CalculationError):
    """Raised when a simulation exceeds safe limits."""
    
    def __init__(self, simulation_type: str, limit_exceeded: str):
        super().__init__(
            message=f"{simulation_type} exceeded {limit_exceeded}",
            user_message=f"This {simulation_type.lower()} would take too long to calculate. Try adjusting your payment amount.",
            retry_allowed=True,
            error_code="SIMULATION_OVERFLOW"
        )


# =============================================================================
# SERVICE ERRORS
# =============================================================================

class ServiceError(RadiantException):
    """Base class for service-level errors."""
    pass


class RepositoryError(ServiceError):
    """Raised when there's an error accessing the data repository."""
    
    def __init__(self, operation: str, details: Optional[str] = None):
        message = f"Repository error during {operation}"
        if details:
            message += f": {details}"
        
        super().__init__(
            message=message,
            user_message="We're having trouble accessing your data. Please try again in a moment.",
            retry_allowed=True,
            error_code="REPOSITORY_ERROR"
        )


class RateLimitError(ServiceError):
    """Raised when rate limits are exceeded."""
    
    def __init__(self, wait_seconds: int = 60):
        super().__init__(
            message=f"Rate limit exceeded. Wait {wait_seconds} seconds.",
            user_message=f"You're doing that too quickly. Please wait a moment before trying again.",
            retry_allowed=True,
            error_code="RATE_LIMIT"
        )
        self.wait_seconds = wait_seconds


class ExternalServiceError(ServiceError):
    """Raised when an external service fails."""
    
    def __init__(self, service: str, details: Optional[str] = None):
        message = f"External service '{service}' failed"
        if details:
            message += f": {details}"
        
        super().__init__(
            message=message,
            user_message=f"We're having trouble connecting to {service}. Please try again shortly.",
            retry_allowed=True,
            error_code="EXTERNAL_SERVICE_ERROR"
        )


# =============================================================================
# ERROR RESPONSE HELPER
# =============================================================================

def format_error_response(exception: RadiantException) -> dict:
    """
    Format an exception into a standardized error response.
    
    Args:
        exception: The RadiantException to format
        
    Returns:
        Dictionary with error details suitable for API response
    """
    return {
        "error": True,
        "message": exception.user_message,
        "code": exception.error_code,
        "retry_allowed": exception.retry_allowed,
    }
