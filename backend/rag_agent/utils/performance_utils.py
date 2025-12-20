"""
Performance measurement and optimization utilities for the RAG Agent Service
"""
import time
import asyncio
import functools
from typing import Callable, Any, Dict, List
from contextlib import contextmanager
from functools import wraps
from collections import deque
import statistics
from ..utils.logger import get_logger


logger = get_logger(__name__)


class PerformanceTimer:
    """
    Performance timer with statistics tracking
    """
    def __init__(self, name: str = "Operation"):
        self.name = name
        self.start_time = None
        self.elapsed_time = 0
        self.times = deque(maxlen=1000)  # Keep last 1000 measurements

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.elapsed_time = time.time() - self.start_time
        self.times.append(self.elapsed_time)

        logger.info(f"{self.name} completed in {self.elapsed_time:.4f}s")
        if len(self.times) >= 10:
            avg_time = statistics.mean(self.times)
            p95_time = self.get_percentile(95)
            logger.info(f"{self.name} - Avg: {avg_time:.4f}s, P95: {p95_time:.4f}s")

    def get_percentile(self, percentile: float) -> float:
        """Calculate percentile of recorded times"""
        if not self.times:
            return 0.0

        sorted_times = sorted(self.times)
        index = int(len(sorted_times) * percentile / 100.0)
        index = min(index, len(sorted_times) - 1)
        index = max(index, 0)
        return sorted_times[index]

    def get_stats(self) -> Dict[str, float]:
        """Get performance statistics"""
        if not self.times:
            return {
                "count": 0,
                "avg": 0.0,
                "min": 0.0,
                "max": 0.0,
                "p95": 0.0,
                "p99": 0.0
            }

        sorted_times = sorted(self.times)
        import statistics
        return {
            "count": len(self.times),
            "avg": statistics.mean(self.times),
            "min": min(self.times),
            "max": max(self.times),
            "p95": self.get_percentile(95),
            "p99": self.get_percentile(99)
        }


def measure_performance(func: Callable) -> Callable:
    """
    Decorator to measure and log performance metrics for function execution
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        with PerformanceTimer(func.__name__) as timer:
            result = func(*args, **kwargs)
            return result
    return wrapper


def measure_performance_async(func: Callable) -> Callable:
    """
    Async decorator to measure and log performance metrics for async function execution
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        with PerformanceTimer(func.__name__) as timer:
            result = await func(*args, **kwargs)
            return result
    return wrapper


@contextmanager
def performance_monitor(operation_name: str = "Operation"):
    """
    Context manager for monitoring performance of code blocks
    """
    start_time = time.time()
    try:
        yield
    finally:
        elapsed_time = time.time() - start_time
        logger.info(f"{operation_name} completed in {elapsed_time:.4f}s")

        # Log warning if operation took more than 10 seconds
        if elapsed_time > 10.0:
            logger.warning(f"{operation_name} exceeded 10-second threshold: {elapsed_time:.4f}s")


def cache_agent_response(ttl: int = 300):
    """
    Decorator to cache agent responses for performance optimization
    ttl: Time-to-live in seconds
    """
    def decorator(func: Callable) -> Callable:
        cache = {}

        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Create cache key from function arguments
            import hashlib
            import json

            # Convert args and kwargs to a hashable string
            cache_key_parts = [func.__name__]

            # Add positional arguments
            for arg in args:
                if isinstance(arg, (str, int, float, bool)):
                    cache_key_parts.append(str(arg))
                else:
                    cache_key_parts.append(hashlib.md5(str(arg).encode()).hexdigest())

            # Add keyword arguments
            for k, v in sorted(kwargs.items()):
                cache_key_parts.append(f"{k}:{v}" if isinstance(v, (str, int, float, bool))
                                      else f"{k}:{hashlib.md5(str(v).encode()).hexdigest()}")

            cache_key = hashlib.md5(":".join(cache_key_parts).encode()).hexdigest()

            # Check if result is in cache and not expired
            current_time = time.time()
            if cache_key in cache:
                result, timestamp = cache[cache_key]
                if current_time - timestamp < ttl:
                    logger.info(f"Cache HIT for {func.__name__}")
                    return result
                else:
                    # Remove expired entry
                    del cache[cache_key]

            logger.info(f"Cache MISS for {func.__name__}")
            # Execute function and cache result
            result = await func(*args, **kwargs)
            cache[cache_key] = (result, current_time)

            return result
        return wrapper
    return decorator


def optimize_concurrent_retrieval(func: Callable) -> Callable:
    """
    Decorator to optimize concurrent retrieval operations
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()

        # Set a timeout to ensure sub-10 second responses
        try:
            result = await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=8.0  # 8 seconds to leave 2 seconds for other processing
            )
        except asyncio.TimeoutError:
            logger.warning(f"{func.__name__} timed out after 8 seconds")
            # Return a default response instead of failing
            from ..api.models.response import ChatResponse
            result = ChatResponse(
                response="I'm sorry, but I'm taking too long to process your request. Please try again.",
                session_id=kwargs.get('session_id') or "unknown",
                citations=[],
                retrieved_context_count=0,
                response_time=8.0
            )

        execution_time = time.time() - start_time

        # Log performance if it took longer than expected
        if execution_time > 5.0:
            logger.warning(f"Long execution time: {func.__name__} took {execution_time:.2f}s")

        return result
    return wrapper


def apply_optimized_settings(preset: str = "balanced"):
    """
    Decorator to apply optimized settings for different response profiles
    """
    # Define optimized settings for different profiles
    optimized_settings = {
        "fast_response": {
            "top_k": 3,
            "temperature": 0.1,
            "max_tokens": 500,
            "timeout": 5.0
        },
        "balanced": {
            "top_k": 5,
            "temperature": 0.2,
            "max_tokens": 800,
            "timeout": 8.0
        },
        "detailed_response": {
            "top_k": 7,
            "temperature": 0.3,
            "max_tokens": 1200,
            "timeout": 12.0
        }
    }

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            settings = optimized_settings.get(preset, optimized_settings["balanced"])

            # Apply settings if not already set in kwargs
            for key, value in settings.items():
                if key not in kwargs:
                    kwargs[key] = value

            return func(*args, **kwargs)
        return wrapper
    return decorator


def async_timeout(seconds: float):
    """
    Decorator to add timeout to async functions
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=seconds
                )
            except asyncio.TimeoutError:
                logger.error(f"Function {func.__name__} timed out after {seconds} seconds")
                raise TimeoutError(f"{func.__name__} timed out after {seconds} seconds")
        return wrapper
    return decorator


def batch_process_requests(batch_size: int = 10, delay: float = 0.1):
    """
    Decorator to batch process requests and apply rate limiting
    """
    def decorator(func: Callable) -> Callable:
        semaphore = asyncio.Semaphore(batch_size)

        @wraps(func)
        async def wrapper(*args, **kwargs):
            async with semaphore:
                # Add small delay to prevent overwhelming downstream services
                await asyncio.sleep(delay)
                return await func(*args, **kwargs)
        return wrapper
    return decorator


class PerformanceMonitor:
    """
    Monitor and track performance metrics for the agent service
    """
    def __init__(self):
        self.response_times = deque(maxlen=10000)  # Keep last 10k measurements
        self.success_count = 0
        self.error_count = 0
        self.cache_hits = 0
        self.cache_misses = 0

    def record_response_time(self, response_time: float):
        """Record response time for performance tracking"""
        self.response_times.append(response_time)

    def record_success(self):
        """Record a successful request"""
        self.success_count += 1

    def record_error(self):
        """Record an error"""
        self.error_count += 1

    def record_cache_hit(self):
        """Record a cache hit"""
        self.cache_hits += 1

    def record_cache_miss(self):
        """Record a cache miss"""
        self.cache_misses += 1

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get current performance statistics"""
        total_requests = self.success_count + self.error_count
        stats = {
            "total_requests": total_requests,
            "success_rate": 0,
            "error_rate": 0,
            "avg_response_time": 0,
            "p95_response_time": 0,
            "p99_response_time": 0,
            "cache_hit_rate": 0,
            "under_10s_rate": 0
        }

        if total_requests > 0:
            stats["success_rate"] = self.success_count / total_requests
            stats["error_rate"] = self.error_count / total_requests

        if self.response_times:
            stats["avg_response_time"] = statistics.mean(self.response_times)

            # Calculate 95th and 99th percentiles
            sorted_times = sorted(self.response_times)
            if sorted_times:
                p95_idx = int(0.95 * len(sorted_times))
                p95_idx = min(p95_idx, len(sorted_times) - 1)
                p95_idx = max(p95_idx, 0)
                stats["p95_response_time"] = sorted_times[p95_idx]

                p99_idx = int(0.99 * len(sorted_times))
                p99_idx = min(p99_idx, len(sorted_times) - 1)
                p99_idx = max(p99_idx, 0)
                stats["p99_response_time"] = sorted_times[p99_idx]

            # Calculate percentage of requests under 10 seconds
            under_10s = sum(1 for t in self.response_times if t < 10.0)
            stats["under_10s_rate"] = under_10s / len(self.response_times) if self.response_times else 0

        total_cache_ops = self.cache_hits + self.cache_misses
        if total_cache_ops > 0:
            stats["cache_hit_rate"] = self.cache_hits / total_cache_ops

        return stats


# Global performance monitor instance
perf_monitor = PerformanceMonitor()


def log_performance_metrics(func: Callable) -> Callable:
    """
    Decorator to log detailed performance metrics for function execution
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()

        try:
            result = func(*args, **kwargs)
            perf_monitor.record_success()
            success = True
        except Exception as e:
            perf_monitor.record_error()
            success = False
            raise
        finally:
            end_time = time.time()
            response_time = end_time - start_time
            perf_monitor.record_response_time(response_time)

            # Log performance metrics
            logger.info(
                f"PERFORMANCE: {func.__name__} - "
                f"success={success}, "
                f"time={response_time:.4f}s"
            )

        return result
    return wrapper


async def log_performance_metrics_async(func: Callable) -> Callable:
    """
    Async decorator to log detailed performance metrics for function execution
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()

        try:
            result = await func(*args, **kwargs)
            perf_monitor.record_success()
            success = True
        except Exception as e:
            perf_monitor.record_error()
            success = False
            raise
        finally:
            end_time = time.time()
            response_time = end_time - start_time
            perf_monitor.record_response_time(response_time)

            # Log performance metrics
            logger.info(
                f"PERFORMANCE: {func.__name__} - "
                f"success={success}, "
                f"time={response_time:.4f}s"
            )

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