import inspect
from functools import wraps

from django.core.cache import cache


def cache_fn(key, timeout=5, condition=None, prefix="cf"):
    """

    :param key: 缓存 key
    :param timeout: 超时时间
    :param condition: 是否需要缓存
    :param prefix: 缓存前缀
    """

    def decorate(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if callable(key):
                call_args = inspect.getcallargs(fn, *args, **kwargs)
                _key = key(*call_args.values())
            elif isinstance(key, str):
                _key = key
            else:
                raise RuntimeError("key is not a string or callable object")

            ck = ":".join([prefix, _key])

            value = cache.get(ck)
            if value is not None:
                return value

            value = fn(*args, **kwargs)

            if condition is None:
                _condition = True if value else False
            elif callable(condition):
                _condition = bool(condition(value))
            elif isinstance(condition, bool):
                _condition = condition
            else:
                raise RuntimeError("Not support")

            if _condition:
                cache.set(ck, value, timeout=timeout)
            return value

        return wrapper

    return decorate


class AcquireLockError(Exception):
    """
    获取锁失败

    """


class CurrencyLock:
    def __init__(self, key, timeout=3600, fixed=False):
        """
        :param key:
        :param timeout:

        """
        self.locked = False
        self.timeout = timeout
        self.key = key
        self.fixed = fixed

    def _acquire_lock(self):
        return cache.add(self.key, 1, self.timeout)

    def _release_lock(self):
        if not self.fixed:
            cache.delete(self.key)

    def __enter__(self):
        self.locked = self._acquire_lock()
        if self.locked:
            # 获取锁成功
            return

        raise AcquireLockError

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._release_lock()


def currency_lock(
    key,
    timeout=3600,
    raise_exception=False,
    fixed=False,
    default_return=None,
    prefix="cl",
):
    """
    :param key: 字符串或者可调用的函数
    :param timeout:
    :param raise_exception: 是否直接报错
    :param default_return: 获取锁失败时返回
    :param fixed: 结束后是否保留锁
    :param prefix: 获取锁失败时返回

    """

    def decorate(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if callable(key):
                call_args = inspect.getcallargs(fn, *args, **kwargs)
                _key = key(*call_args.values())
            elif isinstance(key, str):
                _key = key
            else:
                raise RuntimeError("Not support")

            ck = ":".join([prefix, _key])
            try:
                with CurrencyLock(key=ck, timeout=timeout, fixed=fixed):
                    return fn(*args, **kwargs)
            except AcquireLockError:
                if raise_exception:
                    raise

                return default_return

        return wrapper

    return decorate


def incr(key, delta, timeout):
    cnt = cache.incr(key, delta, ignore_key_check=True)
    if cnt == delta:
        cache.touch(key, timeout)
    return cnt


def decr(key, delta):
    try:
        return cache.decr(key, delta)
    except ValueError:
        return


class RateLimitException(Exception):
    """
    频率限制

    """


class RateLimit:
    def __init__(self, key, limit=1, timeout=3600, delta=1, prefix="rl"):
        """
        :param key:
        :param timeout:

        """
        self.locked = False
        self.timeout = timeout
        self.key = ":".join([prefix, key])
        self.delta = delta
        self.limit = limit

    def __enter__(self):
        cnt = incr(key=self.key, delta=self.delta, timeout=self.timeout)
        if cnt > self.limit:
            raise RateLimitException

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
