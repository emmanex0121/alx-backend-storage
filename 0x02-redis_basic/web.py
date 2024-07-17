import requests
import redis
import time
from functools import wraps

# Redis connection
redis_client = redis.Redis()


def count_accesses(func):
    """
    Decorator to count accesses to each URL.
    """
    @wraps(func)
    def wrapper(url):
        count_key = f"count:{url}"
        redis_client.incr(count_key)
        return func(url)
    return wrapper


def cache_result(duration):
    """
    Decorator to cache the result of a function for a specified duration.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(url):
            cache_key = f"cache:{url}"
            cached_result = redis_client.get(cache_key)
            if cached_result:
                return cached_result.decode('utf-8')
            else:
                result = func(url)
                redis_client.setex(cache_key, duration, result)
                return result
        return wrapper
    return decorator


@count_accesses
@cache_result(duration=10)
def get_page(url: str) -> str:
    """
    Fetches the HTML content of the given URL and returns it.
    """
    response = requests.get(url)
    return response.text
