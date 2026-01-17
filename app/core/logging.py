"""
Logging configuration for the application.
Provides structured logging with appropriate levels for different environments.
"""
import logging
import sys
from typing import Optional

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

# Default log format
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Log level from environment (default: INFO)
DEFAULT_LOG_LEVEL = "INFO"


def setup_logging(
    level: Optional[str] = None,
    log_format: str = LOG_FORMAT,
    date_format: str = LOG_DATE_FORMAT
) -> logging.Logger:
    """
    Configure application-wide logging.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Format string for log messages
        date_format: Format string for timestamps
        
    Returns:
        Root logger configured for the application
    """
    import os
    
    # Get log level from environment or use default
    log_level = level or os.environ.get("LOG_LEVEL", DEFAULT_LOG_LEVEL)
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Create application logger
    logger = logging.getLogger("radiant")
    logger.setLevel(numeric_level)
    
    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific module.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance for the module
    """
    return logging.getLogger(f"radiant.{name}")


# =============================================================================
# MODULE-SPECIFIC LOGGERS
# =============================================================================

class LoggerMixin:
    """Mixin class that provides a logger property."""
    
    @property
    def logger(self) -> logging.Logger:
        return get_logger(self.__class__.__name__)


# Initialize logging on module import
_root_logger = setup_logging()


# Export commonly used functions
__all__ = [
    "setup_logging",
    "get_logger",
    "LoggerMixin",
]
