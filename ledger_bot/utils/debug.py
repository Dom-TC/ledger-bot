"""Decorator for returning the function signature and return value."""

import functools
import logging

log = logging.getLogger(__name__)


def debug(func):
    """Decorator for returning the function signature and return value."""

    @functools.wraps(func)
    def wrapper_debug(*args, **kwargs):
        args_repr = [repr(a) for a in args]
        kwargs_repr = [f"{k}={repr(v)}" for k, v in kwargs.items()]
        signature = ", ".join(args_repr + kwargs_repr)
        log.debug(f"Calling {func.__name__}({signature})")
        value = func(*args, **kwargs)
        log.debug(f"{func.__name__}() returned {repr(value)}")
        return value

    return wrapper_debug
