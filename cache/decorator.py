import inspect
from functools import wraps

path = '/scratch/akilby/Output/Cache/temp'
exclusion_list = []


def cache_decorator(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        from cache import cache
        # THIS IS WRONG, BUT TEMPORARY
        module_to_import = inspect.getmodule(function).__name__
        c = cache.Cache(configure={'directory': path,
                                   'registry': [module_to_import],
                                   'exclusion_list': []})
        func = getattr(c, function.__code__.co_name)(*args, **kwargs)
        return func

    return wrapper
