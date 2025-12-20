"""
Performance optimization utilities for the RAG Agent Service
"""
import asyncio
import time
import functools
from typing import Any, Callable, Dict, Optional, List
from functools import wraps
from collections import OrderedDict
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from ..utils.logger import get_logger
from ..utils.error_handler import error_handler
from ..utils.helpers import log_error_with_context

logger = get_logger(__name__)


class LRUCache:
    """
    Simple LRU Cache implementation for caching agent responses
    """
    def __init__(self, maxsize: int = 128):
        self.maxsize = maxsize
        self.cache = OrderedDict()

    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            # Move to end to show it was recently used
            self.cache.move_to_end(key)
            return self.cache[key]
        return None

    def put(self, key: str, value: Any):
        if key in self.cache:
            # Update existing key
            self.cache.move_to_end(key)
        elif len(self.cache) >= self.maxsize:
            # Remove least recently used item
            self.cache.popitem(last=False)

        self.cache[key] = value

    def clear(self):
        self.cache.clear()


# Global cache instance for agent responses
response_cache = LRUCache(maxsize=512)  # Cache up to 512 responses


def generate_cache_key(question: str, session_id: Optional[str] = None,
                      detail_level: str = "intermediate",
                      response_format: str = "detailed") -> str:
    """
    Generate a cache key based on question and preferences
    """
    cache_input = {
        "question": question,
        "session_id": session_id or "",
        "detail_level": detail_level,
        "response_format": response_format
    }
    cache_str = json.dumps(cache_input, sort_keys=True)
    return hashlib.md5(cache_str.encode()).hexdigest()


def cached_agent_response(ttl: int = 300):  # 5 minutes default TTL
    """
    Decorator to cache agent responses based on question and preferences
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                # Extract parameters for cache key
                question = kwargs.get('question') or (args[1] if len(args) > 1 else None)
                session_id = kwargs.get('session_id') or (args[2] if len(args) > 2 else None)

                # Get user preferences if available
                user_preferences = kwargs.get('user_preferences') or (args[3] if len(args) > 3 else {})
                detail_level = user_preferences.get('detail_level', 'intermediate') if user_preferences else 'intermediate'
                response_format = user_preferences.get('response_format', 'detailed') if user_preferences else 'detailed'

                # Generate cache key
                cache_key = generate_cache_key(
                    question=question,
                    session_id=session_id,
                    detail_level=detail_level,
                    response_format=response_format
                )

                # Check cache first
                cached_result = response_cache.get(cache_key)
                if cached_result is not None:
                    logger.info(f"Cache HIT for question: {question[:50]}...")
                    perf_monitor.record_cache_hit()
                    return cached_result

                # Execute the function and cache the result
                result = await func(*args, **kwargs)

                # Store in cache
                response_cache.put(cache_key, result)
                logger.info(f"Cache MISS, cached new response for question: {question[:50]}...")
                perf_monitor.record_cache_miss()

                return result
            except Exception as e:
                error_id = log_error_with_context(e, {
                    "function": func.__name__,
                    "operation": "cached_agent_response"
                })
                logger.error(f"Error in cached_agent_response decorator: {str(e)} - Error ID: {error_id}")
                # Return original function call in case of error
                return await func(*args, **kwargs)
        return wrapper
    return decorator


def optimize_concurrent_retrieval(func: Callable) -> Callable:
    """
    Decorator to optimize concurrent retrieval operations
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()

        try:
            # Execute with a timeout to ensure sub-10 second responses
            result = await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=8.0  # 8 seconds to leave 2 seconds for other processing
            )
        except asyncio.TimeoutError:
            logger.warning(f"Function {func.__name__} timed out after 8 seconds")
            # Return a default response instead of failing
            from ..api.models.response import ChatResponse, Citation
            result = ChatResponse(
                response="I'm sorry, but I'm experiencing high demand right now. Please try your question again.",
                session_id=kwargs.get('session_id') or "unknown",
                citations=[],
                retrieved_context_count=0,
                response_time=8.0
            )
        except Exception as e:
            error_id = log_error_with_context(e, {
                "function": func.__name__,
                "operation": "optimize_concurrent_retrieval"
            })
            logger.error(f"Error in {func.__name__} during concurrent retrieval: {str(e)} - Error ID: {error_id}")
            # Return a default response in case of error
            from ..api.models.response import ChatResponse, Citation
            result = ChatResponse(
                response="I'm sorry, but I encountered an error while processing your request. Please try again.",
                session_id=kwargs.get('session_id') or "unknown",
                citations=[],
                retrieved_context_count=0,
                response_time=time.time() - start_time
            )

        execution_time = time.time() - start_time

        # Log performance if it took longer than expected
        if execution_time > 5.0:
            logger.warning(f"Long execution time: {func.__name__} took {execution_time:.2f}s")

        return result
    return wrapper


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
        self.response_times = []
        self.success_count = 0
        self.error_count = 0
        self.cache_hits = 0
        self.cache_misses = 0

    def record_response_time(self, response_time: float):
        """Record response time for performance tracking"""
        self.response_times.append(response_time)

        # Keep only last 1000 measurements to avoid memory issues
        if len(self.response_times) > 1000:
            self.response_times = self.response_times[-1000:]

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
        stats = {
            "total_requests": self.success_count + self.error_count,
            "success_rate": 0,
            "error_rate": 0,
            "avg_response_time": 0,
            "p95_response_time": 0,
            "cache_hit_rate": 0
        }

        if stats["total_requests"] > 0:
            stats["success_rate"] = self.success_count / stats["total_requests"]
            stats["error_rate"] = self.error_count / stats["total_requests"]

        if self.response_times:
            stats["avg_response_time"] = sum(self.response_times) / len(self.response_times)

            # Calculate 95th percentile
            sorted_times = sorted(self.response_times)
            p95_index = int(0.95 * len(sorted_times))
            if p95_index < len(sorted_times):
                stats["p95_response_time"] = sorted_times[p95_index]
            else:
                stats["p95_response_time"] = sorted_times[-1] if sorted_times else 0

        total_cache_ops = self.cache_hits + self.cache_misses
        if total_cache_ops > 0:
            stats["cache_hit_rate"] = self.cache_hits / total_cache_ops

        return stats


# Global performance monitor instance
perf_monitor = PerformanceMonitor()


def measure_performance(func: Callable) -> Callable:
    """
    Decorator to measure and log performance metrics
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        success = False

        try:
            result = await func(*args, **kwargs)
            perf_monitor.record_success()
            success = True
            return result
        except Exception as e:
            perf_monitor.record_error()
            success = False
            error_id = log_error_with_context(e, {
                "function": func.__name__,
                "operation": "measure_performance"
            })
            logger.error(f"Error in {func.__name__}: {str(e)} - Error ID: {error_id}")
            raise
        finally:
            end_time = time.time()
            response_time = end_time - start_time
            perf_monitor.record_response_time(response_time)

            # Log performance metrics
            try:
                stats = perf_monitor.get_performance_stats()
                logger.info(
                    f"PERFORMANCE: {func.__name__} - "
                    f"success={success}, "
                    f"time={response_time:.3f}s, "
                    f"p95_time={stats['p95_response_time']:.3f}s"
                )
            except Exception as e:
                logger.warning(f"Could not log detailed performance stats: {str(e)}")

    return wrapper


def optimize_retrieval_params(top_k: int = 5, min_similarity: float = 0.5):
    """
    Decorator to optimize retrieval parameters for faster responses
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Override top_k if it's too high (slower retrieval)
            if 'top_k' in kwargs:
                kwargs['top_k'] = min(kwargs['top_k'], top_k)
            else:
                # If top_k is passed as a positional argument, we need to handle it differently
                # This is a simplified approach - in practice you'd need to inspect the function signature
                pass

            # Add min_similarity filter if not present
            if 'min_similarity' not in kwargs:
                kwargs['min_similarity'] = min_similarity

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


# Predefined optimized settings for different use cases
OPTIMIZED_SETTINGS = {
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


def apply_optimized_settings(preset: str = "balanced"):
    """
    Decorator to apply optimized settings for different response profiles
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            settings = OPTIMIZED_SETTINGS.get(preset, OPTIMIZED_SETTINGS["balanced"])

            # Apply settings if not already set
            for key, value in settings.items():
                if key not in kwargs:
                    kwargs[key] = value

            return func(*args, **kwargs)
        return wrapper
    return decorator