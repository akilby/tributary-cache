from functools import wraps


def cache_decorator(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        # THIS IS WRONG, BUT TEMPORARY
        from claims_data.utils.globalcache import c
        func = getattr(c, function.__code__.co_name)(*args, **kwargs)
        return func

    return wrapper
