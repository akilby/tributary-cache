import inspect
from functools import wraps

# THIS IS WRONG, BUT TEMPORARY - need to implement some sort of
# module-based instruction... something like joblib. Also rename
# the decorator and have it take arguments
path = '/scratch/akilby/Output/Cache/temp'
exclusion_list = []


def cache_decorator(function):
    @wraps(function)
    def wrapper(*args, **kwargs):

        module_to_import = inspect.getmodule(function).__name__
        print(module_to_import)

        module_to_import = function.__module__

        from cache import cache
        c = cache.Cache(configure={'directory': path,
                                   'registry': [module_to_import],
                                   'exclusion_list': []},
                        noisily=True)
        return getattr(c, function.__code__.co_name)(*args, **kwargs)

    return wrapper
