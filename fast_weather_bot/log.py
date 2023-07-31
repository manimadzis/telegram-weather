import inspect
import sys
from functools import wraps
from typing import TypeVar, Callable, Any

from loguru import logger


def arglist(*args, **kwargs):
    s = ""
    for a in args:
        if hasattr(a, "__len__") and len(a) > 80:
            s += f"{type(a)} length={len(a)}, "
        else:
            s += repr(a) + ", "
    for k, v in kwargs.items():
        s += "{k}={v}, ".format(k=k, v=repr(v))
    return "({s})".format(s=s[:-2])


F = TypeVar("F", bound=Callable[..., Any])

logger.remove()
logger.add(sys.stdout, colorize=True, enqueue=True, format="{time} | {level} | {message}", level="TRACE")


def log(level, msg, depth=1):
    logger.opt(depth=depth).log(level, msg)


def logit(level: str = "TRACE") -> Callable[[F], F]:
    def decorate(func: F) -> F:
        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                log(level, f"START AWAIT {func.__module__}.{func.__name__}" + arglist(*args, **kwargs))
                ret = await func(*args, **kwargs)
                log(level, f"END AWAIT {func.__module__}.{func.__name__}" + arglist(*args, **kwargs))
                return ret

            return wrapper
        else:
            @wraps(func)
            def wrapper(*args, **kwargs):
                log(level, f"CALL {func.__module__}.{func.__name__}" + arglist(*args, **kwargs))
                try:
                    ret = func(*args, **kwargs)
                except Exception as e:
                    log(level, f"EXCEPTION {e} FROM {func.__module__}.{func.__name__}" + arglist(*args, **kwargs))
                    raise e
                log(level, f"RET FROM {func.__module__}.{func.__name__}" + arglist(*args, **kwargs) + f"VALUE {ret}")
                return ret

            return wrapper

    return decorate
