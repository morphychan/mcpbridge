"""
LLM Module Exception Classes.

This module defines exception classes specific to LLM interactions,
providing structured error handling for various failure scenarios
in LLM client operations.
"""

from __future__ import annotations

from typing import Optional, Dict, Any


class LLMError(Exception):
    """
    Base exception class for all LLM-related errors.
    
    This is the parent class for all LLM module exceptions, providing
    a common interface and structure for error handling.
    
    Attributes:
        message (str): Human-readable error message
        details (Optional[Dict[str, Any]]): Additional error details
    """
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize the base LLM error.
        
        Args:
            message (str): Human-readable error message
            details (Optional[Dict[str, Any]]): Additional error context
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self) -> str:
        """Return a string representation of the error."""
        if self.details:
            return f"{self.message} (details: {self.details})"
        return self.message


class LLMConfigurationError(LLMError):
    """
    Exception raised for LLM configuration errors.
    
    This exception is raised when there are issues with LLM configuration,
    such as missing environment variables, invalid parameter values,
    or misconfigured settings.
    """
    pass


class LLMConnectionError(LLMError):
    """
    Exception raised for LLM connection errors.
    
    This exception is raised when there are network-level issues
    connecting to the LLM service, such as DNS resolution failures,
    connection timeouts, or network unreachability.
    """
    pass


class LLMAuthenticationError(LLMError):
    """
    Exception raised for LLM authentication errors.
    
    This exception is raised when authentication with the LLM service
    fails, typically due to invalid API keys, expired tokens, or
    insufficient permissions.
    """
    pass


class LLMAPIError(LLMError):
    """
    Exception raised for LLM API-level errors.
    
    This exception is raised when the LLM service returns an error
    response, such as invalid request parameters, rate limiting,
    or server-side errors.
    
    Additional Attributes:
        status_code (Optional[int]): HTTP status code from the API response
        error_code (Optional[str]): Error code from the API response
    """
    
    def __init__(
        self, 
        message: str, 
        details: Optional[Dict[str, Any]] = None,
        status_code: Optional[int] = None,
        error_code: Optional[str] = None
    ) -> None:
        """
        Initialize the LLM API error.
        
        Args:
            message (str): Human-readable error message
            details (Optional[Dict[str, Any]]): Additional error context
            status_code (Optional[int]): HTTP status code from API
            error_code (Optional[str]): Error code from API response
        """
        super().__init__(message, details)
        self.status_code = status_code
        self.error_code = error_code
    
    def __str__(self) -> str:
        """Return a string representation of the API error."""
        parts = [self.message]
        
        if self.status_code:
            parts.append(f"status_code={self.status_code}")
        
        if self.error_code:
            parts.append(f"error_code={self.error_code}")
        
        if self.details:
            parts.append(f"details={self.details}")
        
        if len(parts) > 1:
            return f"{parts[0]} ({', '.join(parts[1:])})"
        return parts[0]


class LLMTimeoutError(LLMError):
    """
    Exception raised for LLM request timeout errors.
    
    This exception is raised when a request to the LLM service
    exceeds the configured timeout period.
    """
    pass


class LLMRateLimitError(LLMAPIError):
    """
    Exception raised for LLM rate limiting errors.
    
    This exception is raised when the LLM service returns a rate
    limiting error, indicating that the request quota has been
    exceeded and the client should retry after a delay.
    
    Additional Attributes:
        retry_after (Optional[float]): Suggested retry delay in seconds
    """
    
    def __init__(
        self, 
        message: str, 
        details: Optional[Dict[str, Any]] = None,
        status_code: Optional[int] = None,
        error_code: Optional[str] = None,
        retry_after: Optional[float] = None
    ) -> None:
        """
        Initialize the rate limit error.
        
        Args:
            message (str): Human-readable error message
            details (Optional[Dict[str, Any]]): Additional error context
            status_code (Optional[int]): HTTP status code from API
            error_code (Optional[str]): Error code from API response
            retry_after (Optional[float]): Suggested retry delay in seconds
        """
        super().__init__(message, details, status_code, error_code)
        self.retry_after = retry_after


class LLMResponseError(LLMError):
    """
    Exception raised for LLM response parsing errors.
    
    This exception is raised when the LLM service returns a response
    that cannot be parsed or is in an unexpected format.
    """
    pass


class LLMModelError(LLMAPIError):
    """
    Exception raised for LLM model-specific errors.
    
    This exception is raised when there are issues specific to the
    requested model, such as model not found, model overloaded,
    or unsupported model features.
    """
    pass


class LLMTokenLimitError(LLMAPIError):
    """
    Exception raised for LLM token limit errors.
    
    This exception is raised when a request exceeds the token
    limits of the LLM model, either for input or output tokens.
    """
    pass 