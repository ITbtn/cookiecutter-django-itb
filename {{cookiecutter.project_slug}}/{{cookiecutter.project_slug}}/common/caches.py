from typing import Any, Optional, List, Union, Dict
from django.core.cache import caches
from django.core.cache.backends.base import BaseCache


class TenantBaseCache:
    """
    Base cache class with multi-tenancy support.

    This class provides a tenant-aware caching layer that automatically prefixes
    cache keys with the tenant code to ensure data isolation between tenants.

    Features:
    - Automatic tenant key prefixing
    - Configurable cache backend
    - Bulk operations support
    - Type-safe operations

    Usage:
        # Basic usage
        cache = TenantBaseCache(tenant_code="tenant1")
        cache.set("user_data", {"name": "John"}, cache_key="user:123")

        # Get data
        data = cache.get(cache_key="user:123")

        # Remove specific key
        cache.remove(cache_key="user:123")

        # Bulk operations
        cache.remove_many(["user:123", "user:456"])
    """

    def __init__(self, tenant_code: str = "", cache_key: str = "", cache_name: str = "default", default_timeout: int = 60 * 15):
        """
        Initialize the tenant cache.

        :param tenant_code: The tenant identifier for multi-tenancy
        :param cache_key: Default cache key for operations
        :param cache_name: Name of the Django cache backend to use
        :param default_timeout: Default cache timeout in seconds (15 minutes)
        """
        if not tenant_code:
            raise ValueError("tenant_code is required for multi-tenancy")

        self.cache: BaseCache = caches[cache_name]
        self.tenant_code: str = tenant_code
        self.default_timeout: int = default_timeout
        self.cache_key: str = self.get_cache_key(cache_key=cache_key) if cache_key else ""

    def get_cache_key(self, cache_key: str) -> str:
        """
        Generate a tenant-prefixed cache key.

        :param cache_key: The base cache key
        :return: Tenant-prefixed cache key
        :raises: ValueError: If cache_key is empty
        """
        if not cache_key:
            raise ValueError("cache_key cannot be empty")
        return f"{self.tenant_code}:{cache_key}"

    def get(self, cache_key: str = "", default: Any = None) -> Any:
        """
        Get a value from cache.

        :param cache_key: The cache key (uses instance default if not provided)
        :param default: Default value to return if key not found
        :return: Cached value or default
        """
        if not cache_key and not self.cache_key:
            raise ValueError("cache_key must be provided or set during initialization")

        cache_key = self.get_cache_key(cache_key=cache_key) if cache_key else self.cache_key
        return self.cache.get(cache_key, default)

    def set(self, cache_value: Any, cache_key: str = "", timeout: Optional[int] = None) -> None:
        """
        Set a value in cache.

        :param cache_value: Value to cache
        :param cache_key: The cache key (uses instance default if not provided)
        :param timeout: Cache timeout in seconds (uses default if not provided)
        :return: True if successful, False otherwise
        """
        if not cache_key and not self.cache_key:
            raise ValueError("cache_key must be provided or set during initialization")

        cache_key = self.get_cache_key(cache_key=cache_key) if cache_key else self.cache_key
        timeout = timeout if timeout is not None else self.default_timeout
        return self.cache.set(cache_key, cache_value, timeout)

    def clear_cache(self) -> None:
        """
        Clear all cache entries for the current tenant.

        Note: This method attempts to clear tenant-specific keys but may not
        work with all cache backends that don't support key pattern matching.

        :return: Number of keys deleted (approximate)
        """
        # This is a best-effort implementation
        # Many cache backends don't support pattern deletion
        try:
            # Try to get all keys (may not work with all backends)
            all_keys = getattr(self.cache, 'keys', lambda pattern: [])('*')
            tenant_keys = [key for key in all_keys if key.startswith(f"{self.tenant_code}:")]
            if tenant_keys:
                return self.cache.delete_many(tenant_keys)
            return
        except (AttributeError, NotImplementedError):
            # Fallback: can't clear tenant-specific keys
            return

    def remove(self, cache_key: str = "") -> None:
        """
        Remove a specific cache key.

        :param cache_key: The cache key to remove (uses instance default if not provided)
        :return: True if key was deleted, False otherwise
        """
        if not cache_key and not self.cache_key:
            raise ValueError("cache_key must be provided or set during initialization")

        cache_key = self.get_cache_key(cache_key=cache_key) if cache_key else self.cache_key
        return self.cache.delete(cache_key)

    def remove_many(self, cache_keys: List[str]) -> None:
        """
        Remove multiple cache keys.

        :param cache_keys: List of cache keys to remove
        :return:
        """
        if not cache_keys:
            return

        tenant_keys = [self.get_cache_key(cache_key=cache_key) for cache_key in cache_keys]
        return self.cache.delete_many(tenant_keys)

    def has_key(self, cache_key: str = "") -> bool:
        """
        Check if a cache key exists.

        :param cache_key: The cache key to check (uses instance default if not provided)
        :return: True if key exists, False otherwise
        """
        if not cache_key and not self.cache_key:
            raise ValueError("cache_key must be provided or set during initialization")

        cache_key = self.get_cache_key(cache_key=cache_key) if cache_key else self.cache_key
        return self.cache.has_key(cache_key)

    def get_or_set(self, cache_key: str = "", default: Any = None, timeout: Optional[int] = None) -> Any:
        """
        Get a value from cache, or set it if it doesn't exist.

        :param cache_key: The cache key (uses instance default if not provided)
        :param default: Default value to set if key doesn't exist
        :param timeout: Cache timeout in seconds (uses default if not provided)
        :return: Cached value or the default value
        """
        if not cache_key and not self.cache_key:
            raise ValueError("cache_key must be provided or set during initialization")

        cache_key = self.get_cache_key(cache_key=cache_key) if cache_key else self.cache_key
        timeout = timeout if timeout is not None else self.default_timeout
        return self.cache.get_or_set(cache_key, default, timeout)

    def get_many(self, cache_keys: List[str]) -> Dict[str, Any]:
        """
        Get multiple values from cache.

        :param cache_keys: List of cache keys to retrieve
        :return: Dictionary mapping cache keys to values
        """
        if not cache_keys:
            return {}

        tenant_keys = [self.get_cache_key(cache_key=cache_key) for cache_key in cache_keys]
        cached_data = self.cache.get_many(tenant_keys)

        # Convert back to original keys (without tenant prefix)
        result = {}
        for tenant_key, value in cached_data.items():
            original_key = tenant_key.replace(f"{self.tenant_code}:", "", 1)
            result[original_key] = value

        return result

    def set_many(self, data: Dict[str, Any], timeout: Optional[int] = None) -> List[str]:
        """
        Set multiple values in cache.

        :param data: Dictionary mapping cache keys to values
        :param timeout: Cache timeout in seconds (uses default if not provided)
        :return: List of keys that failed to be set
        """
        if not data:
            return []

        tenant_data = {self.get_cache_key(cache_key=k): v for k, v in data.items()}
        timeout = timeout if timeout is not None else self.default_timeout
        return self.cache.set_many(tenant_data, timeout)

    def incr(self, cache_key: str = "", delta: int = 1) -> int:
        """
        Increment a numeric cache value.

        :param cache_key: The cache key (uses instance default if not provided)
        :param delta: Amount to increment by
        :return: New value after increment
        :raises: ValueError: If key not set or not an integer
        """
        if not cache_key and not self.cache_key:
            raise ValueError("cache_key must be provided or set during initialization")

        cache_key = self.get_cache_key(cache_key=cache_key) if cache_key else self.cache_key
        return self.cache.incr(cache_key, delta)

    def decr(self, cache_key: str = "", delta: int = 1) -> int:
        """
        Decrement a numeric cache value.

        :param cache_key: The cache key (uses instance default if not provided)
        :param delta: Amount to decrement by
        :return: New value after decrement
        :raises: ValueError: If key not set or not an integer
        """
        if not cache_key and not self.cache_key:
            raise ValueError("cache_key must be provided or set during initialization")

        cache_key = self.get_cache_key(cache_key=cache_key) if cache_key else self.cache_key
        return self.cache.decr(cache_key, delta)
