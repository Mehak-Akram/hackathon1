"""
Utility functions and error handling for the RAG Agent Service
"""
import uuid
import re
import time
import statistics
from typing import Any, Dict, Optional, Callable, Awaitable, List
from pydantic import BaseModel
from functools import wraps
from contextlib import contextmanager
from datetime import datetime


class RAGAgentError(Exception):
    """
    Base exception class for RAG Agent Service errors
    """
    def __init__(self, message: str, error_code: str = "RAG_ERROR", details: Optional[Dict] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details
        }


class RetrievalError(RAGAgentError):
    """
    Exception raised when there's an error during content retrieval
    """
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(message, "RETRIEVAL_ERROR", details)


class ValidationError(RAGAgentError):
    """
    Exception raised when there's a validation error
    """
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(message, "VALIDATION_ERROR", details)


class AgentError(RAGAgentError):
    """
    Exception raised when there's an error during agent processing
    """
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(message, "AGENT_ERROR", details)


def generate_uuid() -> str:
    """
    Generate a UUID string
    """
    return str(uuid.uuid4())


def is_valid_uuid(uuid_string: str) -> bool:
    """
    Validate if a string is a valid UUID
    """
    try:
        uuid.UUID(uuid_string)
        return True
    except ValueError:
        return False


def is_valid_url(url: str) -> bool:
    """
    Validate if a string is a valid URL
    """
    regex = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url is not None and regex.search(url) is not None


@contextmanager
def timer():
    """
    Context manager for timing code execution
    """
    start_time = time.time()
    yield
    end_time = time.time()
    execution_time = end_time - start_time
    print(f"Execution time: {execution_time:.4f} seconds")


def time_it(func: Callable) -> Callable:
    """
    Decorator to time function execution
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"{func.__name__} executed in {execution_time:.4f} seconds")
        return result
    return wrapper


async def time_it_async(func: Callable) -> Callable:
    """
    Async decorator to time async function execution
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"{func.__name__} executed in {execution_time:.4f} seconds")
        return result
    return wrapper


def performance_timer(metric_name: str = None):
    """
    Decorator to time function execution and log performance metrics
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            execution_time = end_time - start_time

            # Use function name if no metric name provided
            metric = metric_name or func.__name__

            # Log performance metric
            from .logger import get_logger
            logger = get_logger(__name__)
            logger.info(f"PERFORMANCE_METRIC: {metric} took {execution_time:.4f}s")

            return result
        return wrapper
    return decorator


async def performance_timer_async(metric_name: str = None):
    """
    Async decorator to time async function execution and log performance metrics
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            result = await func(*args, **kwargs)
            end_time = time.time()
            execution_time = end_time - start_time

            # Use function name if no metric name provided
            metric = metric_name or func.__name__

            # Log performance metric
            from .logger import get_logger
            logger = get_logger(__name__)
            logger.info(f"PERFORMANCE_METRIC: {metric} took {execution_time:.4f}s")

            return result
        return wrapper
    return decorator


def log_performance_metrics(func: Callable) -> Callable:
    """
    Decorator to log detailed performance metrics for function execution
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        start_memory = None

        try:
            # If psutil is available, track memory usage
            import psutil
            import os
            process = psutil.Process(os.getpid())
            start_memory = process.memory_info().rss / 1024 / 1024  # MB
        except ImportError:
            pass  # psutil not available, skip memory tracking

        try:
            result = func(*args, **kwargs)
            success = True
        except Exception as e:
            success = False
            raise
        finally:
            end_time = time.time()
            execution_time = end_time - start_time

            # Calculate memory usage if possible
            memory_used = None
            if start_memory:
                try:
                    end_memory = process.memory_info().rss / 1024 / 1024  # MB
                    memory_used = end_memory - start_memory
                except:
                    pass  # Ignore memory calculation errors

            # Log detailed performance metrics
            from .logger import get_logger
            logger = get_logger(__name__)
            log_msg = f"PERFORMANCE: {func.__name__} - "
            log_msg += f"success={success}, "
            log_msg += f"time={execution_time:.4f}s"

            if memory_used is not None:
                log_msg += f", memory_change={memory_used:+.2f}MB"

            logger.info(log_msg)

        return result
    return wrapper


async def log_performance_metrics_async(func: Callable) -> Callable:
    """
    Async decorator to log detailed performance metrics for function execution
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        start_memory = None

        try:
            # If psutil is available, track memory usage
            import psutil
            import os
            process = psutil.Process(os.getpid())
            start_memory = process.memory_info().rss / 1024 / 1024  # MB
        except ImportError:
            pass  # psutil not available, skip memory tracking

        try:
            result = await func(*args, **kwargs)
            success = True
        except Exception as e:
            success = False
            raise
        finally:
            end_time = time.time()
            execution_time = end_time - start_time

            # Calculate memory usage if possible
            memory_used = None
            if start_memory:
                try:
                    end_memory = process.memory_info().rss / 1024 / 1024  # MB
                    memory_used = end_memory - start_memory
                except:
                    pass  # Ignore memory calculation errors

            # Log detailed performance metrics
            from .logger import get_logger
            logger = get_logger(__name__)
            log_msg = f"PERFORMANCE: {func.__name__} - "
            log_msg += f"success={success}, "
            log_msg += f"time={execution_time:.4f}s"

            if memory_used is not None:
                log_msg += f", memory_change={memory_used:+.2f}MB"

            logger.info(log_msg)

        return result
    return wrapper


def log_error_with_context(error: Exception, context: Optional[Dict] = None, error_id: Optional[str] = None) -> str:
    """
    Log an error with comprehensive context information
    """
    from .logger import get_logger
    import traceback
    from datetime import datetime

    logger = get_logger(__name__)

    if error_id is None:
        error_id = f"err_{int(time.time())}_{hash(str(error)) % 10000}"

    error_info = {
        "error_id": error_id,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "timestamp": datetime.utcnow().isoformat(),
        "context": context or {},
        "traceback": traceback.format_exc()
    }

    logger.error(f"[{error_id}] {type(error).__name__}: {str(error)} - Context: {context}", extra={"error_info": error_info})

    return error_id


def safe_execute(func: Callable, fallback_return=None, log_errors: bool = True):
    """
    Decorator to safely execute a function with error handling and fallback
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if log_errors:
                context = {"function": func.__name__, "args_count": len(args), "kwargs_keys": list(kwargs.keys())}
                log_error_with_context(e, context)
            return fallback_return

    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            if log_errors:
                context = {"function": func.__name__, "args_count": len(args), "kwargs_keys": list(kwargs.keys())}
                log_error_with_context(e, context)
            return fallback_return

    # Return appropriate wrapper based on function type
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return wrapper


def validate_input_type(value: Any, expected_type: type, param_name: str = "value") -> bool:
    """
    Validate that an input matches the expected type and log if it doesn't
    """
    from .logger import get_logger
    logger = get_logger(__name__)

    is_valid = isinstance(value, expected_type)
    if not is_valid:
        logger.warning(f"Input validation failed: {param_name} expected {expected_type.__name__}, got {type(value).__name__}")

    return is_valid


def log_function_input_output(log_inputs: bool = True, log_outputs: bool = True, log_level: str = "DEBUG"):
    """
    Decorator to log function inputs and outputs for debugging purposes
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            import logging
            logger = logging.getLogger(func.__module__)

            if log_inputs:
                logger.log(getattr(logging, log_level),
                          f"Function {func.__name__} called with args: {len(args)} args, kwargs: {list(kwargs.keys())}")

            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                if log_outputs:
                    logger.log(getattr(logging, log_level),
                              f"Function {func.__name__} completed in {duration:.4f}s, returned {type(result).__name__}")

                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"Function {func.__name__} failed after {duration:.4f}s: {str(e)}")
                raise

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            import logging
            logger = logging.getLogger(func.__module__)

            if log_inputs:
                logger.log(getattr(logging, log_level),
                          f"Async function {func.__name__} called with args: {len(args)} args, kwargs: {list(kwargs.keys())}")

            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time

                if log_outputs:
                    logger.log(getattr(logging, log_level),
                              f"Async function {func.__name__} completed in {duration:.4f}s, returned {type(result).__name__}")

                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"Async function {func.__name__} failed after {duration:.4f}s: {str(e)}")
                raise

        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return wrapper

    return decorator


def calculate_response_time_percentile(response_times: List[float], percentile: float = 95.0) -> float:
    """
    Calculate response time percentile from a list of response times
    """
    if not response_times:
        return 0.0

    sorted_times = sorted(response_times)
    index = int(len(sorted_times) * percentile / 100.0)

    # Ensure index is within bounds
    index = min(index, len(sorted_times) - 1)
    index = max(index, 0)

    return sorted_times[index]


def get_performance_summary(response_times: List[float]) -> Dict[str, float]:
    """
    Get a summary of performance metrics from response times
    """
    if not response_times:
        return {
            "count": 0,
            "avg": 0.0,
            "min": 0.0,
            "max": 0.0,
            "p50": 0.0,
            "p95": 0.0,
            "p99": 0.0
        }

    sorted_times = sorted(response_times)

    return {
        "count": len(response_times),
        "avg": statistics.mean(response_times),
        "min": min(response_times),
        "max": max(response_times),
        "p50": calculate_response_time_percentile(response_times, 50.0),
        "p95": calculate_response_time_percentile(response_times, 95.0),
        "p99": calculate_response_time_percentile(response_times, 99.0)
    }


def calculate_similarity_score(text1: str, text2: str) -> float:
    """
    Calculate a basic similarity score between two texts (0.0 to 1.0)
    """
    if not text1 or not text2:
        return 0.0

    # Simple character-based similarity
    set1 = set(text1.lower())
    set2 = set(text2.lower())

    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))

    if union == 0:
        return 0.0

    return intersection / union


def format_timestamp(timestamp: Optional[datetime] = None) -> str:
    """
    Format a datetime object as an ISO string
    """
    if timestamp is None:
        timestamp = datetime.now()
    return timestamp.isoformat()


def generate_uuid() -> str:
    """
    Generate a UUID string
    """
    return str(uuid.uuid4())


def is_valid_uuid(uuid_string: str) -> bool:
    """
    Validate if a string is a valid UUID
    """
    try:
        uuid.UUID(uuid_string)
        return True
    except ValueError:
        return False


def is_valid_url(url: str) -> bool:
    """
    Validate if a string is a valid URL
    """
    regex = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url is not None and regex.search(url) is not None


@contextmanager
def timer():
    """
    Context manager for timing code execution
    """
    start_time = time.time()
    yield
    end_time = time.time()
    execution_time = end_time - start_time
    print(f"Execution time: {execution_time:.4f} seconds")


def time_it(func: Callable) -> Callable:
    """
    Decorator to time function execution
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"{func.__name__} executed in {execution_time:.4f} seconds")
        return result
    return wrapper


async def time_it_async(func: Callable) -> Callable:
    """
    Async decorator to time async function execution
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"{func.__name__} executed in {execution_time:.4f} seconds")
        return result
    return wrapper


def performance_timer(metric_name: str = None):
    """
    Decorator to time function execution and log performance metrics
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            execution_time = end_time - start_time

            # Use function name if no metric name provided
            metric = metric_name or func.__name__

            # Log performance metric
            logger = get_logger(__name__)
            logger.info(f"PERFORMANCE_METRIC: {metric} took {execution_time:.4f}s")

            return result
        return wrapper
    return decorator


async def performance_timer_async(metric_name: str = None):
    """
    Async decorator to time async function execution and log performance metrics
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            result = await func(*args, **kwargs)
            end_time = time.time()
            execution_time = end_time - start_time

            # Use function name if no metric name provided
            metric = metric_name or func.__name__

            # Log performance metric
            logger = get_logger(__name__)
            logger.info(f"PERFORMANCE_METRIC: {metric} took {execution_time:.4f}s")

            return result
        return wrapper
    return decorator


def log_performance_metrics(func: Callable) -> Callable:
    """
    Decorator to log detailed performance metrics for function execution
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        start_memory = None

        try:
            # If psutil is available, track memory usage
            import psutil
            import os
            process = psutil.Process(os.getpid())
            start_memory = process.memory_info().rss / 1024 / 1024  # MB
        except ImportError:
            pass  # psutil not available, skip memory tracking

        try:
            result = func(*args, **kwargs)
            success = True
        except Exception as e:
            success = False
            raise
        finally:
            end_time = time.time()
            execution_time = end_time - start_time

            # Calculate memory usage if possible
            memory_used = None
            if start_memory:
                try:
                    end_memory = process.memory_info().rss / 1024 / 1024  # MB
                    memory_used = end_memory - start_memory
                except:
                    pass  # Ignore memory calculation errors

            # Log detailed performance metrics
            logger = get_logger(__name__)
            log_msg = f"PERFORMANCE: {func.__name__} - "
            log_msg += f"success={success}, "
            log_msg += f"time={execution_time:.4f}s"

            if memory_used is not None:
                log_msg += f", memory_change={memory_used:+.2f}MB"

            logger.info(log_msg)

        return result
    return wrapper


async def log_performance_metrics_async(func: Callable) -> Callable:
    """
    Async decorator to log detailed performance metrics for function execution
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        start_memory = None

        try:
            # If psutil is available, track memory usage
            import psutil
            import os
            process = psutil.Process(os.getpid())
            start_memory = process.memory_info().rss / 1024 / 1024  # MB
        except ImportError:
            pass  # psutil not available, skip memory tracking

        try:
            result = await func(*args, **kwargs)
            success = True
        except Exception as e:
            success = False
            raise
        finally:
            end_time = time.time()
            execution_time = end_time - start_time

            # Calculate memory usage if possible
            memory_used = None
            if start_memory:
                try:
                    end_memory = process.memory_info().rss / 1024 / 1024  # MB
                    memory_used = end_memory - start_memory
                except:
                    pass  # Ignore memory calculation errors

            # Log detailed performance metrics
            logger = get_logger(__name__)
            log_msg = f"PERFORMANCE: {func.__name__} - "
            log_msg += f"success={success}, "
            log_msg += f"time={execution_time:.4f}s"

            if memory_used is not None:
                log_msg += f", memory_change={memory_used:+.2f}MB"

            logger.info(log_msg)

        return result
    return wrapper


def calculate_response_time_percentile(response_times: List[float], percentile: float = 95.0) -> float:
    """
    Calculate response time percentile from a list of response times
    """
    if not response_times:
        return 0.0

    sorted_times = sorted(response_times)
    index = int(len(sorted_times) * percentile / 100.0)

    # Ensure index is within bounds
    index = min(index, len(sorted_times) - 1)
    index = max(index, 0)

    return sorted_times[index]


def get_performance_summary(response_times: List[float]) -> Dict[str, float]:
    """
    Get a summary of performance metrics from response times
    """
    if not response_times:
        return {
            "count": 0,
            "avg": 0.0,
            "min": 0.0,
            "max": 0.0,
            "p50": 0.0,
            "p95": 0.0,
            "p99": 0.0
        }

    sorted_times = sorted(response_times)

    return {
        "count": len(response_times),
        "avg": sum(response_times) / len(response_times),
        "min": min(response_times),
        "max": max(response_times),
        "p50": calculate_response_time_percentile(response_times, 50.0),
        "p95": calculate_response_time_percentile(response_times, 95.0),
        "p99": calculate_response_time_percentile(response_times, 99.0)
    }


def calculate_similarity_score(text1: str, text2: str) -> float:
    """
    Calculate a basic similarity score between two texts (0.0 to 1.0)
    """
    if not text1 or not text2:
        return 0.0

    # Simple character-based similarity
    set1 = set(text1.lower())
    set2 = set(text2.lower())

    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))

    if union == 0:
        return 0.0

    return intersection / union


def format_timestamp(timestamp: Optional[datetime] = None) -> str:
    """
    Format a datetime object as an ISO string
    """
    if timestamp is None:
        timestamp = datetime.now()
    return timestamp.isoformat()