"""
Comprehensive error handling and debugging utilities for the RAG Agent Service
"""
import sys
import traceback
import logging
import asyncio
from typing import Any, Dict, Optional, Callable, Union
from functools import wraps
from contextlib import contextmanager
import json
import time
from datetime import datetime

from ..utils.logger import get_logger
from ..api.models.response import ErrorResponse
from ..utils.debug_utils import get_system_diagnostics, log_system_diagnostics

logger = get_logger(__name__)


class RAGAgentErrorHandler:
    """
    Comprehensive error handler with detailed logging and debugging capabilities
    """

    def __init__(self):
        self.error_counts = {}
        self.error_timestamps = {}

    def log_error(self,
                  error: Exception,
                  context: Optional[Dict[str, Any]] = None,
                  level: str = "ERROR",
                  include_traceback: bool = True,
                  include_system_diagnostics: bool = True) -> str:
        """
        Log an error with comprehensive context and debugging information
        """
        error_id = f"err_{int(time.time())}_{hash(str(error)) % 10000}"

        # Prepare error details
        error_details = {
            "error_id": error_id,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": datetime.utcnow().isoformat(),
            "context": context or {}
        }

        if include_traceback:
            error_details["traceback"] = traceback.format_exc()

        # Include system diagnostics for debugging
        if include_system_diagnostics:
            try:
                error_details["system_diagnostics"] = get_system_diagnostics()
            except Exception as diag_error:
                logger.warning(f"Could not collect system diagnostics: {str(diag_error)}")

        # Count error occurrences
        error_type = type(error).__name__
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        self.error_timestamps[error_type] = datetime.utcnow().isoformat()

        # Log the error with different levels
        log_func = getattr(logger, level.lower(), logger.error)
        log_func(f"[{error_id}] {error_type}: {str(error)}", extra={"error_details": error_details})

        return error_id

    def handle_and_reraise(self,
                          error: Exception,
                          context: Optional[Dict[str, Any]] = None,
                          reraise: bool = True) -> Optional[ErrorResponse]:
        """
        Handle an error with logging and optionally return an error response
        """
        error_id = self.log_error(error, context)

        # Create error response
        error_response = ErrorResponse(
            error_id=error_id,
            error_type=type(error).__name__,
            message=str(error),
            timestamp=datetime.utcnow().isoformat(),
            context=context or {}
        )

        if reraise:
            raise error
        else:
            return error_response

    def get_error_summary(self) -> Dict[str, Any]:
        """
        Get a summary of error statistics
        """
        return {
            "total_errors": sum(self.error_counts.values()),
            "error_types": dict(self.error_counts),
            "last_error_times": dict(self.error_timestamps),
            "timestamp": datetime.utcnow().isoformat()
        }

    def reset_error_counts(self):
        """
        Reset error counters
        """
        self.error_counts.clear()
        self.error_timestamps.clear()


# Global error handler instance
error_handler = RAGAgentErrorHandler()


def handle_exceptions(
    fallback_return=None,
    log_error: bool = True,
    reraise: bool = False,
    context_func: Optional[Callable] = None,
    include_system_diagnostics: bool = True
):
    """
    Decorator for comprehensive exception handling with logging and debugging
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                context = context_func(*args, **kwargs) if context_func else {}
                context.update({
                    "function": func.__name__,
                    "args_count": len(args),
                    "kwargs_keys": list(kwargs.keys())
                })

                if log_error:
                    error_id = error_handler.log_error(e, context, include_system_diagnostics=include_system_diagnostics)
                    context["error_id"] = error_id

                if reraise:
                    raise
                else:
                    return fallback_return

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                context = context_func(*args, **kwargs) if context_func else {}
                context.update({
                    "function": func.__name__,
                    "args_count": len(args),
                    "kwargs_keys": list(kwargs.keys())
                })

                if log_error:
                    error_id = error_handler.log_error(e, context, include_system_diagnostics=include_system_diagnostics)
                    context["error_id"] = error_id

                if reraise:
                    raise
                else:
                    return fallback_return

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


@contextmanager
def debug_context(operation_name: str,
                  log_level: str = "DEBUG",
                  log_inputs: bool = True,
                  log_outputs: bool = True,
                  include_system_diagnostics: bool = False):
    """
    Context manager for debugging with detailed logging of operation flow
    """
    start_time = time.time()
    logger.log(getattr(logging, log_level), f"Starting operation: {operation_name}")

    if log_inputs:
        # Log any inputs passed to the context (though this is limited in context managers)
        logger.debug(f"Operation '{operation_name}' started with context")

    # Log system diagnostics at start if requested
    if include_system_diagnostics:
        try:
            diagnostics = get_system_diagnostics()
            logger.debug(f"System diagnostics at start of '{operation_name}'", extra={"diagnostics": diagnostics})
        except Exception as e:
            logger.warning(f"Could not collect system diagnostics at start of '{operation_name}': {str(e)}")

    error_occurred = False
    try:
        yield
    except Exception as e:
        error_occurred = True
        error_id = error_handler.log_error(e, {
            "operation": operation_name,
            "stage": "during_operation"
        }, include_system_diagnostics=include_system_diagnostics)
        logger.error(f"Error in operation '{operation_name}' - Error ID: {error_id}")
        raise
    finally:
        end_time = time.time()
        duration = end_time - start_time

        status = "FAILED" if error_occurred else "COMPLETED"
        logger.log(getattr(logging, log_level),
                  f"Operation '{operation_name}' {status} in {duration:.4f}s")

        # Log system diagnostics at end if requested
        if include_system_diagnostics and not error_occurred:
            try:
                diagnostics = get_system_diagnostics()
                logger.debug(f"System diagnostics at end of '{operation_name}'", extra={"diagnostics": diagnostics})
            except Exception as e:
                logger.warning(f"Could not collect system diagnostics at end of '{operation_name}': {str(e)}")

        if log_outputs and not error_occurred:
            logger.debug(f"Operation '{operation_name}' completed successfully")


def log_function_call(include_args: bool = True,
                      include_result: bool = True,
                      log_level: str = "DEBUG"):
    """
    Decorator to log function calls with arguments and results
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            func_name = func.__name__

            # Log function entry
            if include_args:
                logger.log(getattr(logging, log_level),
                          f"Calling function: {func_name} with args={len(args)}, kwargs={list(kwargs.keys())}")
            else:
                logger.log(getattr(logging, log_level),
                          f"Calling function: {func_name}")

            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time

                if include_result:
                    logger.log(getattr(logging, log_level),
                              f"Function {func_name} completed in {duration:.4f}s, result type: {type(result).__name__}")
                else:
                    logger.log(getattr(logging, log_level),
                              f"Function {func_name} completed in {duration:.4f}s")

                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"Function {func_name} failed after {duration:.4f}s: {str(e)}")
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            func_name = func.__name__

            # Log function entry
            if include_args:
                logger.log(getattr(logging, log_level),
                          f"Calling function: {func_name} with args={len(args)}, kwargs={list(kwargs.keys())}")
            else:
                logger.log(getattr(logging, log_level),
                          f"Calling function: {func_name}")

            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                if include_result:
                    logger.log(getattr(logging, log_level),
                              f"Function {func_name} completed in {duration:.4f}s, result type: {type(result).__name__}")
                else:
                    logger.log(getattr(logging, log_level),
                              f"Function {func_name} completed in {duration:.4f}s")

                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"Function {func_name} failed after {duration:.4f}s: {str(e)}")
                raise

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def validate_and_log_input(validation_func: Callable[[Any], bool],
                          error_message: str = "Invalid input provided"):
    """
    Decorator to validate function inputs and log validation results
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Validate inputs
            for i, arg in enumerate(args):
                if not validation_func(arg):
                    logger.warning(f"Input validation failed for arg {i} in function {func.__name__}: {error_message}")
                    error_handler.log_error(ValueError(error_message), {
                        "function": func.__name__,
                        "arg_index": i,
                        "arg_value": str(arg)[:100]  # Limit length for logging
                    })
                    raise ValueError(error_message)

            for key, value in kwargs.items():
                if not validation_func(value):
                    logger.warning(f"Input validation failed for kwarg '{key}' in function {func.__name__}: {error_message}")
                    error_handler.log_error(ValueError(error_message), {
                        "function": func.__name__,
                        "kwarg_key": key,
                        "kwarg_value": str(value)[:100]  # Limit length for logging
                    })
                    raise ValueError(error_message)

            # Log successful validation
            logger.debug(f"Input validation passed for function {func.__name__}")
            return func(*args, **kwargs)

        return wrapper
    return decorator


def performance_debug(log_threshold: float = 1.0):  # Log if function takes more than 1 second
    """
    Decorator to log performance debugging information for slow functions
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            result = await func(*args, **kwargs)
            duration = time.time() - start_time

            if duration > log_threshold:
                logger.warning(f"SLOW FUNCTION: {func.__name__} took {duration:.4f}s (threshold: {log_threshold}s)")
                logger.debug(f"Slow function details - Args: {len(args)} args, Kwargs: {list(kwargs.keys())}")
            else:
                logger.debug(f"Function {func.__name__} completed in {duration:.4f}s")

            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            duration = time.time() - start_time

            if duration > log_threshold:
                logger.warning(f"SLOW FUNCTION: {func.__name__} took {duration:.4f}s (threshold: {log_threshold}s)")
                logger.debug(f"Slow function details - Args: {len(args)} args, Kwargs: {list(kwargs.keys())}")
            else:
                logger.debug(f"Function {func.__name__} completed in {duration:.4f}s")

            return result

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# Helper function to get detailed error information
def get_detailed_error_info(error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Get detailed error information including system state
    """
    import psutil
    import os

    error_info = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "timestamp": datetime.utcnow().isoformat(),
        "context": context or {},
        "system_info": {
            "process_id": os.getpid(),
            "memory_usage_mb": psutil.Process().memory_info().rss / 1024 / 1024 if 'psutil' in sys.modules else "N/A",
            "cpu_percent": psutil.Process().cpu_percent() if 'psutil' in sys.modules else "N/A"
        }
    }

    # Add traceback if available
    try:
        error_info["traceback"] = traceback.format_exc()
    except:
        error_info["traceback"] = "Could not format traceback"

    return error_info


# Export commonly used functions
__all__ = [
    'error_handler',
    'handle_exceptions',
    'debug_context',
    'log_function_call',
    'validate_and_log_input',
    'performance_debug',
    'get_detailed_error_info'
]