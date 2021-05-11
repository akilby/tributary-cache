import importlib
import inspect

from cache.config import load_config
from undecorated import undecorated

_old = globals().copy()


def new_globals(config_file):

    current_globals = globals().copy()
    for item in list(current_globals.keys()):
        if item not in list(_old.keys()) + ['_old', 'new_globals',
                                            'retrieve_all_funcs']:
            globals().pop(item)

    directory, registry, exclusion_list = load_config(config_file)
    registry.append('cache.utils.universalmodules')

    for module in registry:
        allfuncs = retrieve_all_funcs(module)
        globals().update(allfuncs)

    globals_list = globals()
    # print(globals_list.keys())
    return globals_list


def retrieve_all_funcs(module):
    allfuncs = vars(importlib.import_module(module))
    allfuncs = {funcname: func for funcname, func in allfuncs.items()
                if funcname not in ["cache_decorator", "wraps"]}
    for funcname, func in allfuncs.items():
        if not funcname.startswith('__'):
            try:
                sc = inspect.getsource(func)
                if sc.startswith('@cache_decorator'):
                    allfuncs[funcname] = undecorated(allfuncs[funcname])
            except TypeError:
                pass
    return allfuncs
