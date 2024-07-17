#!/usr/bin/env python3
"""
Redis module
"""
import sys
from functools import wraps
from typing import Union, Optional, Callable
from uuid import uuid4

import redis

UnionOfTypes = Union[str, bytes, int, float]


def count_calls(method: Callable) -> Callable:
    """
    A decorator to count how many times methods of the Cache class are called.
    """
    key = method.__qualname__

    @wraps(method)
    def wrapper(self, *args, **kwargs):
        """
        Wrapper that increments the call count.
        """
        self._redis.incr(key)
        return method(self, *args, **kwargs)

    return wrapper


def call_history(method: Callable) -> Callable:
    """
    A decorator to store the history of inputs and outputs for a particular
    function.
    """
    key = method.__qualname__
    input_key = f"{key}:inputs"
    output_key = f"{key}:outputs"

    @wraps(method)
    def wrapper(self, *args, **kwargs):
        """
        Wrapper that stores the inputs and outputs in Redis lists.
        """
        self._redis.rpush(input_key, str(args))
        result = method(self, *args, **kwargs)
        self._redis.rpush(output_key, str(result))
        return result

    return wrapper


def replay(method: Callable):
    """
    Display the history of calls of a particular function.
    """
    r = redis.Redis()
    method_name = method.__qualname__
    input_key = f"{method_name}:inputs"
    output_key = f"{method_name}:outputs"

    inputs = r.lrange(input_key, 0, -1)
    outputs = r.lrange(output_key, 0, -1)

    call_count = len(inputs)
    print(f"{method_name} was called {call_count} times:")

    for input_args, output in zip(inputs, outputs):
        print(f"{method_name}(*{input_args.decode('utf-8')}) -> "
              f"{output.decode('utf-8')}")


class Cache:
    """
    Cache class that interfaces with Redis.
    """

    def __init__(self):
        """
        Constructor initializes the Redis connection and flushes the database.
        """
        self._redis = redis.Redis()
        self._redis.flushdb()

    @count_calls
    @call_history
    def store(self, data: UnionOfTypes) -> str:
        """
        Store data in Redis with a random key and return the key.
        """
        key = str(uuid4())
        self._redis.set(key, data)
        return key

    def get(self, key: str, fn: Optional[Callable] = None) -> UnionOfTypes:
        """
        Retrieve data from Redis and optionally apply a conversion function.
        """
        data = self._redis.get(key)
        if data is None:
            return None
        if fn:
            return fn(data)
        return data

    def get_int(self, key: str) -> Optional[int]:
        """
        Retrieve data from Redis and convert it to an integer.
        """
        data = self._redis.get(key)
        return int(data) if data else None

    def get_str(self, key: str) -> Optional[str]:
        """
        Retrieve data from Redis and convert it to a string.
        """
        data = self._redis.get(key)
        return data.decode('utf-8') if data else None
