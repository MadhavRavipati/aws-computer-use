# ABOUTME: Comprehensive retry and error handling utilities
# ABOUTME: Provides decorators and functions for resilient AWS operations

import asyncio
import functools
import logging
import time
from typing import Callable, Any, Optional, List, Type, Union
from botocore.exceptions import ClientError, ConnectionError, EndpointConnectionError
import random

logger = logging.getLogger(__name__)

class RetryConfig:
    """Configuration for retry behavior"""
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: Optional[List[Type[Exception]]] = None,
        retryable_status_codes: Optional[List[int]] = None
    ):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions or [
            ConnectionError,
            EndpointConnectionError,
            TimeoutError,
            asyncio.TimeoutError
        ]
        self.retryable_status_codes = retryable_status_codes or [
            429,  # Too Many Requests
            500,  # Internal Server Error
            502,  # Bad Gateway
            503,  # Service Unavailable
            504   # Gateway Timeout
        ]

def calculate_backoff(attempt: int, config: RetryConfig) -> float:
    """Calculate exponential backoff with optional jitter"""
    delay = min(
        config.initial_delay * (config.exponential_base ** (attempt - 1)),
        config.max_delay
    )
    
    if config.jitter:
        # Add random jitter between 0 and 25% of the delay
        jitter = delay * random.random() * 0.25
        delay += jitter
    
    return delay

def is_retryable_exception(exc: Exception, config: RetryConfig) -> bool:
    """Check if exception is retryable"""
    # Check exception type
    if any(isinstance(exc, exc_type) for exc_type in config.retryable_exceptions):
        return True
    
    # Check AWS ClientError
    if isinstance(exc, ClientError):
        error_code = exc.response.get('Error', {}).get('Code', '')
        status_code = exc.response.get('ResponseMetadata', {}).get('HTTPStatusCode', 0)
        
        # Retryable error codes
        retryable_codes = [
            'ThrottlingException',
            'TooManyRequestsException',
            'RequestLimitExceeded',
            'ServiceUnavailable',
            'InternalServerError',
            'ProvisionedThroughputExceededException'
        ]
        
        if error_code in retryable_codes or status_code in config.retryable_status_codes:
            return True
    
    return False

def retry_sync(config: Optional[RetryConfig] = None):
    """Synchronous retry decorator"""
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(1, config.max_attempts + 1):
                try:
                    result = func(*args, **kwargs)
                    
                    # If successful, return result
                    return result
                    
                except Exception as e:
                    last_exception = e
                    
                    if attempt >= config.max_attempts:
                        logger.error(f"Max retry attempts ({config.max_attempts}) reached for {func.__name__}")
                        raise
                    
                    if not is_retryable_exception(e, config):
                        logger.error(f"Non-retryable exception in {func.__name__}: {e}")
                        raise
                    
                    # Calculate backoff
                    delay = calculate_backoff(attempt, config)
                    logger.warning(
                        f"Retryable error in {func.__name__} (attempt {attempt}/{config.max_attempts}): {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    
                    time.sleep(delay)
            
            # Should never reach here, but just in case
            if last_exception:
                raise last_exception
                
        return wrapper
    return decorator

def retry_async(config: Optional[RetryConfig] = None):
    """Asynchronous retry decorator"""
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(1, config.max_attempts + 1):
                try:
                    result = await func(*args, **kwargs)
                    
                    # If successful, return result
                    return result
                    
                except Exception as e:
                    last_exception = e
                    
                    if attempt >= config.max_attempts:
                        logger.error(f"Max retry attempts ({config.max_attempts}) reached for {func.__name__}")
                        raise
                    
                    if not is_retryable_exception(e, config):
                        logger.error(f"Non-retryable exception in {func.__name__}: {e}")
                        raise
                    
                    # Calculate backoff
                    delay = calculate_backoff(attempt, config)
                    logger.warning(
                        f"Retryable error in {func.__name__} (attempt {attempt}/{config.max_attempts}): {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    
                    await asyncio.sleep(delay)
            
            # Should never reach here, but just in case
            if last_exception:
                raise last_exception
                
        return wrapper
    return decorator

class CircuitBreaker:
    """Circuit breaker pattern for preventing cascading failures"""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: Type[Exception] = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'closed'  # closed, open, half-open
    
    def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.state == 'open':
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = 'half-open'
            else:
                raise Exception(f"Circuit breaker is open. Service {func.__name__} is unavailable.")
        
        try:
            result = func(*args, **kwargs)
            if self.state == 'half-open':
                self.state = 'closed'
                self.failure_count = 0
            return result
            
        except self.expected_exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = 'open'
                logger.error(f"Circuit breaker opened for {func.__name__} after {self.failure_count} failures")
            
            raise

# AWS-specific retry configurations
bedrock_retry_config = RetryConfig(
    max_attempts=5,
    initial_delay=2.0,
    max_delay=30.0,
    retryable_exceptions=[
        ConnectionError,
        EndpointConnectionError,
        TimeoutError
    ],
    retryable_status_codes=[429, 500, 502, 503, 504]
)

ecs_retry_config = RetryConfig(
    max_attempts=3,
    initial_delay=1.0,
    max_delay=10.0
)

dynamodb_retry_config = RetryConfig(
    max_attempts=3,
    initial_delay=0.5,
    max_delay=5.0
)