"""
Advanced debugging utilities for the RAG Agent Service
"""
import sys
import os
import psutil
import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from contextlib import contextmanager
from functools import wraps
import asyncio
import logging
from dataclasses import dataclass, asdict
from enum import Enum

from .logger import get_logger
from .helpers import format_timestamp

logger = get_logger(__name__)


class DebugLevel(Enum):
    """Debug levels for different types of debugging information"""
    TRACE = "TRACE"      # Detailed function entry/exit tracing
    PERFORMANCE = "PERFORMANCE"  # Performance metrics and timing
    MEMORY = "MEMORY"    # Memory usage tracking
    NETWORK = "NETWORK"  # Network and API call debugging
    DATA = "DATA"        # Data flow and transformation debugging


@dataclass
class DebugInfo:
    """Data class to hold debugging information"""
    timestamp: str
    function_name: str
    operation: str
    duration: Optional[float] = None
    memory_before: Optional[float] = None
    memory_after: Optional[float] = None
    memory_delta: Optional[float] = None
    input_size: Optional[int] = None
    output_size: Optional[int] = None
    error_occurred: bool = False
    error_message: Optional[str] = None
    debug_level: DebugLevel = DebugLevel.TRACE
    extra_info: Optional[Dict[str, Any]] = None


class DebuggingContext:
    """Context manager for debugging operations"""

    def __init__(self,
                 operation_name: str,
                 debug_level: DebugLevel = DebugLevel.TRACE,
                 log_inputs: bool = True,
                 log_outputs: bool = True,
                 log_memory: bool = False,
                 log_performance: bool = True):
        self.operation_name = operation_name
        self.debug_level = debug_level
        self.log_inputs = log_inputs
        self.log_outputs = log_outputs
        self.log_memory = log_memory
        self.log_performance = log_performance
        self.start_time = None
        self.memory_before = None
        self.memory_after = None
        self.error_occurred = False
        self.error_message = None
        self.process = None

        # Get process reference for memory tracking
        if self.log_memory:
            try:
                self.process = psutil.Process(os.getpid())
            except:
                self.log_memory = False  # Disable if psutil not available

    def __enter__(self):
        self.start_time = time.time()

        # Log memory before operation
        if self.log_memory and self.process:
            try:
                self.memory_before = self.process.memory_info().rss / 1024 / 1024  # MB
            except:
                self.log_memory = False

        # Log operation start
        log_func = getattr(logger, self.debug_level.value.lower(), logger.debug)
        log_func(f"DEBUG: Starting operation '{self.operation_name}'")

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        duration = self.end_time - self.start_time

        # Log memory after operation
        if self.log_memory and self.process:
            try:
                self.memory_after = self.process.memory_info().rss / 1024 / 1024  # MB
                self.memory_delta = self.memory_after - self.memory_before if self.memory_before else None
            except:
                self.log_memory = False

        # Track error
        if exc_type is not None:
            self.error_occurred = True
            self.error_message = str(exc_val)

        # Create debug info
        debug_info = DebugInfo(
            timestamp=format_timestamp(),
            function_name=self.operation_name,
            operation="exit",
            duration=duration,
            memory_before=self.memory_before,
            memory_after=self.memory_after,
            memory_delta=self.memory_delta,
            error_occurred=self.error_occurred,
            error_message=self.error_message,
            debug_level=self.debug_level
        )

        # Log operation completion
        log_func = getattr(logger, self.debug_level.value.lower(), logger.debug)
        status = "FAILED" if self.error_occurred else "COMPLETED"
        log_msg = f"DEBUG: Operation '{self.operation_name}' {status} in {duration:.4f}s"

        if self.log_memory and self.memory_delta is not None:
            log_msg += f", memory change: {self.memory_delta:+.2f}MB"

        if self.error_occurred:
            log_func(log_msg, extra={"debug_info": asdict(debug_info)})
        else:
            log_func(log_msg)


def debug_trace(include_args: bool = True,
                include_result: bool = True,
                log_level: str = "DEBUG"):
    """
    Decorator to trace function calls with detailed debugging information
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            func_name = func.__name__

            # Log function entry
            if include_args:
                logger.log(getattr(logging, log_level),
                          f"TRACE: Entering {func_name} with args={len(args)}, kwargs={list(kwargs.keys())}")
            else:
                logger.log(getattr(logging, log_level),
                          f"TRACE: Entering {func_name}")

            start_time = time.time()
            memory_before = None
            memory_after = None
            memory_delta = None

            # Get memory before if possible
            try:
                process = psutil.Process(os.getpid())
                memory_before = process.memory_info().rss / 1024 / 1024  # MB
            except:
                pass  # psutil not available

            try:
                result = await func(*args, **kwargs)
                success = True
                error_msg = None
            except Exception as e:
                success = False
                error_msg = str(e)
                raise
            finally:
                end_time = time.time()
                duration = end_time - start_time

                # Get memory after if possible
                try:
                    memory_after = process.memory_info().rss / 1024 / 1024  # MB
                    memory_delta = memory_after - memory_before if memory_before is not None else None
                except:
                    pass  # psutil not available

                # Log function exit
                if include_result:
                    result_info = f", result type: {type(result).__name__}" if success else ""
                    if memory_delta is not None:
                        logger.log(getattr(logging, log_level),
                                  f"TRACE: Exiting {func_name} in {duration:.4f}s (success={success}){result_info}, mem_change={memory_delta:+.2f}MB")
                    else:
                        logger.log(getattr(logging, log_level),
                                  f"TRACE: Exiting {func_name} in {duration:.4f}s (success={success}){result_info}")
                else:
                    if memory_delta is not None:
                        logger.log(getattr(logging, log_level),
                                  f"TRACE: Exiting {func_name} in {duration:.4f}s (success={success}), mem_change={memory_delta:+.2f}MB")
                    else:
                        logger.log(getattr(logging, log_level),
                                  f"TRACE: Exiting {func_name} in {duration:.4f}s (success={success})")

                # Log error if it occurred
                if not success and error_msg:
                    logger.error(f"TRACE: Error in {func_name}: {error_msg}")

            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            func_name = func.__name__

            # Log function entry
            if include_args:
                logger.log(getattr(logging, log_level),
                          f"TRACE: Entering {func_name} with args={len(args)}, kwargs={list(kwargs.keys())}")
            else:
                logger.log(getattr(logging, log_level),
                          f"TRACE: Entering {func_name}")

            start_time = time.time()
            memory_before = None
            memory_after = None
            memory_delta = None

            # Get memory before if possible
            try:
                process = psutil.Process(os.getpid())
                memory_before = process.memory_info().rss / 1024 / 1024  # MB
            except:
                pass  # psutil not available

            try:
                result = func(*args, **kwargs)
                success = True
                error_msg = None
            except Exception as e:
                success = False
                error_msg = str(e)
                raise
            finally:
                end_time = time.time()
                duration = end_time - start_time

                # Get memory after if possible
                try:
                    memory_after = process.memory_info().rss / 1024 / 1024  # MB
                    memory_delta = memory_after - memory_before if memory_before is not None else None
                except:
                    pass  # psutil not available

                # Log function exit
                if include_result:
                    result_info = f", result type: {type(result).__name__}" if success else ""
                    if memory_delta is not None:
                        logger.log(getattr(logging, log_level),
                                  f"TRACE: Exiting {func_name} in {duration:.4f}s (success={success}){result_info}, mem_change={memory_delta:+.2f}MB")
                    else:
                        logger.log(getattr(logging, log_level),
                                  f"TRACE: Exiting {func_name} in {duration:.4f}s (success={success}){result_info}")
                else:
                    if memory_delta is not None:
                        logger.log(getattr(logging, log_level),
                                  f"TRACE: Exiting {func_name} in {duration:.4f}s (success={success}), mem_change={memory_delta:+.2f}MB")
                    else:
                        logger.log(getattr(logging, log_level),
                                  f"TRACE: Exiting {func_name} in {duration:.4f}s (success={success})")

                # Log error if it occurred
                if not success and error_msg:
                    logger.error(f"TRACE: Error in {func_name}: {error_msg}")

            return result

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def debug_memory_monitor(threshold_mb: float = 100.0):
    """
    Decorator to monitor memory usage and log if it exceeds threshold
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                process = psutil.Process(os.getpid())
                memory_before = process.memory_info().rss / 1024 / 1024  # MB
            except:
                return await func(*args, **kwargs)  # Skip monitoring if psutil not available

            result = await func(*args, **kwargs)

            try:
                memory_after = process.memory_info().rss / 1024 / 1024  # MB
                memory_delta = memory_after - memory_before
                memory_peak = max(memory_before, memory_after)

                if memory_delta > threshold_mb:
                    logger.warning(
                        f"MEMORY: Function {func.__name__} caused memory increase of {memory_delta:+.2f}MB "
                        f"(before: {memory_before:.2f}MB, after: {memory_after:.2f}MB)"
                    )

                if memory_peak > 500:  # Log if memory usage is high
                    logger.warning(
                        f"MEMORY: Function {func.__name__} peak memory usage: {memory_peak:.2f}MB"
                    )
            except:
                pass  # Ignore monitoring errors

            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                process = psutil.Process(os.getpid())
                memory_before = process.memory_info().rss / 1024 / 1024  # MB
            except:
                return func(*args, **kwargs)  # Skip monitoring if psutil not available

            result = func(*args, **kwargs)

            try:
                memory_after = process.memory_info().rss / 1024 / 1024  # MB
                memory_delta = memory_after - memory_before
                memory_peak = max(memory_before, memory_after)

                if memory_delta > threshold_mb:
                    logger.warning(
                        f"MEMORY: Function {func.__name__} caused memory increase of {memory_delta:+.2f}MB "
                        f"(before: {memory_before:.2f}MB, after: {memory_after:.2f}MB)"
                    )

                if memory_peak > 500:  # Log if memory usage is high
                    logger.warning(
                        f"MEMORY: Function {func.__name__} peak memory usage: {memory_peak:.2f}MB"
                    )
            except:
                pass  # Ignore monitoring errors

            return result

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def debug_performance_monitor(
    time_threshold: float = 1.0,  # Log if function takes more than 1 second
    memory_threshold: float = 50.0  # Log if memory usage increases by more than 50MB
):
    """
    Decorator to monitor both performance and memory usage
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            memory_before = None
            memory_after = None

            # Get memory before if possible
            try:
                process = psutil.Process(os.getpid())
                memory_before = process.memory_info().rss / 1024 / 1024  # MB
            except:
                pass

            try:
                result = await func(*args, **kwargs)
                success = True
            except Exception as e:
                success = False
                raise
            finally:
                end_time = time.time()
                duration = end_time - start_time

                # Get memory after if possible
                try:
                    memory_after = process.memory_info().rss / 1024 / 1024  # MB
                    memory_delta = memory_after - memory_before if memory_before is not None else 0
                except:
                    memory_delta = 0

                # Log performance issues
                if duration > time_threshold:
                    logger.warning(
                        f"PERFORMANCE: Slow function {func.__name__} took {duration:.4f}s "
                        f"(threshold: {time_threshold}s, success: {success})"
                    )

                # Log memory issues
                if memory_delta and memory_delta > memory_threshold:
                    logger.warning(
                        f"MEMORY: Function {func.__name__} memory increase: {memory_delta:+.2f}MB "
                        f"(threshold: {memory_threshold}MB, success: {success})"
                    )

            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            memory_before = None
            memory_after = None

            # Get memory before if possible
            try:
                process = psutil.Process(os.getpid())
                memory_before = process.memory_info().rss / 1024 / 1024  # MB
            except:
                pass

            try:
                result = func(*args, **kwargs)
                success = True
            except Exception as e:
                success = False
                raise
            finally:
                end_time = time.time()
                duration = end_time - start_time

                # Get memory after if possible
                try:
                    memory_after = process.memory_info().rss / 1024 / 1024  # MB
                    memory_delta = memory_after - memory_before if memory_before is not None else 0
                except:
                    memory_delta = 0

                # Log performance issues
                if duration > time_threshold:
                    logger.warning(
                        f"PERFORMANCE: Slow function {func.__name__} took {duration:.4f}s "
                        f"(threshold: {time_threshold}s, success: {success})"
                    )

                # Log memory issues
                if memory_delta and memory_delta > memory_threshold:
                    logger.warning(
                        f"MEMORY: Function {func.__name__} memory increase: {memory_delta:+.2f}MB "
                        f"(threshold: {memory_threshold}MB, success: {success})"
                    )

            return result

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def log_data_flow(operation: str = "data_processing"):
    """
    Decorator to log data flow through functions for debugging
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Log input data characteristics
            input_size = 0
            input_types = []

            for i, arg in enumerate(args):
                if hasattr(arg, '__len__'):
                    try:
                        size = len(arg)
                        input_size += size
                    except:
                        input_size += 1  # For non-sequence types
                else:
                    input_size += 1
                input_types.append(type(arg).__name__)

            for key, value in kwargs.items():
                if hasattr(value, '__len__'):
                    try:
                        size = len(value)
                        input_size += size
                    except:
                        input_size += 1
                else:
                    input_size += 1
                input_types.append(f"{key}:{type(value).__name__}")

            logger.debug(f"DATA_FLOW: {operation} - Input to {func.__name__}: "
                        f"size={input_size}, types={input_types}")

            start_time = time.time()
            try:
                result = await func(*args, **kwargs)

                # Log output data characteristics
                output_size = 0
                output_type = type(result).__name__

                if hasattr(result, '__len__'):
                    try:
                        output_size = len(result)
                    except:
                        output_size = 1
                else:
                    output_size = 1

                duration = time.time() - start_time
                logger.debug(f"DATA_FLOW: {operation} - Output from {func.__name__}: "
                            f"type={output_type}, size={output_size}, time={duration:.4f}s")

                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"DATA_FLOW: {operation} - Error in {func.__name__} after {duration:.4f}s: {str(e)}")
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Log input data characteristics
            input_size = 0
            input_types = []

            for i, arg in enumerate(args):
                if hasattr(arg, '__len__'):
                    try:
                        size = len(arg)
                        input_size += size
                    except:
                        input_size += 1  # For non-sequence types
                else:
                    input_size += 1
                input_types.append(type(arg).__name__)

            for key, value in kwargs.items():
                if hasattr(value, '__len__'):
                    try:
                        size = len(value)
                        input_size += size
                    except:
                        input_size += 1
                else:
                    input_size += 1
                input_types.append(f"{key}:{type(value).__name__}")

            logger.debug(f"DATA_FLOW: {operation} - Input to {func.__name__}: "
                        f"size={input_size}, types={input_types}")

            start_time = time.time()
            try:
                result = func(*args, **kwargs)

                # Log output data characteristics
                output_size = 0
                output_type = type(result).__name__

                if hasattr(result, '__len__'):
                    try:
                        output_size = len(result)
                    except:
                        output_size = 1
                else:
                    output_size = 1

                duration = time.time() - start_time
                logger.debug(f"DATA_FLOW: {operation} - Output from {func.__name__}: "
                            f"type={output_type}, size={output_size}, time={duration:.4f}s")

                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"DATA_FLOW: {operation} - Error in {func.__name__} after {duration:.4f}s: {str(e)}")
                raise

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def get_system_diagnostics() -> Dict[str, Any]:
    """
    Get comprehensive system diagnostics for debugging
    """
    try:
        process = psutil.Process(os.getpid())

        diagnostics = {
            "timestamp": format_timestamp(),
            "process": {
                "pid": process.pid,
                "name": process.name(),
                "status": process.status(),
                "cpu_percent": process.cpu_percent(),
                "memory_info": {
                    "rss_mb": process.memory_info().rss / 1024 / 1024,
                    "vms_mb": process.memory_info().vms / 1024 / 1024,
                    "percent": process.memory_percent()
                },
                "num_threads": process.num_threads(),
                "num_fds": process.num_fds() if os.name != 'nt' else "N/A",
                "create_time": datetime.fromtimestamp(process.create_time()).isoformat()
            },
            "system": {
                "cpu_count": psutil.cpu_count(),
                "cpu_percent": psutil.cpu_percent(),
                "memory_total_mb": psutil.virtual_memory().total / 1024 / 1024,
                "memory_available_mb": psutil.virtual_memory().available / 1024 / 1024,
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage_percent": psutil.disk_usage('/').percent if os.name != 'nt' else "N/A",
                "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat()
            },
            "python": {
                "version": sys.version,
                "implementation": sys.implementation.name,
                "executable": sys.executable,
                "maxsize": sys.maxsize,
                "platform": sys.platform
            }
        }

        return diagnostics
    except Exception as e:
        logger.error(f"Error getting system diagnostics: {str(e)}")
        return {"error": str(e), "timestamp": format_timestamp()}


def log_system_diagnostics():
    """
    Log system diagnostics for debugging purposes
    """
    diagnostics = get_system_diagnostics()
    logger.info("SYSTEM_DIAGNOSTICS", extra={"diagnostics": diagnostics})


def debug_on_error(debug_func: Optional[Callable] = None):
    """
    Decorator to run debugging function when an error occurs
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if debug_func:
                    try:
                        debug_result = debug_func()
                        logger.error(f"DEBUG_ON_ERROR: {func.__name__} - Debug result: {debug_result}")
                    except Exception as debug_e:
                        logger.error(f"DEBUG_ON_ERROR: {func.__name__} - Debug function error: {str(debug_e)}")

                # Log system diagnostics on error
                diagnostics = get_system_diagnostics()
                logger.error(f"DEBUG_ON_ERROR: {func.__name__} - System diagnostics at error time",
                           extra={"diagnostics": diagnostics})

                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if debug_func:
                    try:
                        debug_result = debug_func()
                        logger.error(f"DEBUG_ON_ERROR: {func.__name__} - Debug result: {debug_result}")
                    except Exception as debug_e:
                        logger.error(f"DEBUG_ON_ERROR: {func.__name__} - Debug function error: {str(debug_e)}")

                # Log system diagnostics on error
                diagnostics = get_system_diagnostics()
                logger.error(f"DEBUG_ON_ERROR: {func.__name__} - System diagnostics at error time",
                           extra={"diagnostics": diagnostics})

                raise

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# Helper functions for debugging
def print_debug_info(title: str, data: Any, max_length: int = 500):
    """
    Print debug information with a title, truncating long data
    """
    if isinstance(data, (str, list, dict)):
        data_str = str(data)
        if len(data_str) > max_length:
            data_str = data_str[:max_length] + f"... (truncated, total length: {len(data_str)})"
    else:
        data_str = str(data)

    print(f"\n=== DEBUG: {title} ===")
    print(data_str)
    print("=" * (12 + len(title) + 4))


def time_block(operation_name: str):
    """
    Context manager to time a block of code
    """
    @contextmanager
    def timer():
        start = time.time()
        try:
            yield
        finally:
            end = time.time()
            logger.debug(f"TIMED_BLOCK: {operation_name} took {end - start:.4f}s")

    return timer()


# Export commonly used functions
__all__ = [
    'DebuggingContext',
    'debug_trace',
    'debug_memory_monitor',
    'debug_performance_monitor',
    'log_data_flow',
    'get_system_diagnostics',
    'log_system_diagnostics',
    'debug_on_error',
    'print_debug_info',
    'time_block',
    'DebugLevel',
    'DebugInfo'
]