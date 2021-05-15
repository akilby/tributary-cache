import importlib

from undecorated import undecorated

from ..config import load_config

_old = globals().copy()


def new_globals(config_file):

    current_globals = globals().copy()
    for item in list(current_globals.keys()):
        if item not in list(_old.keys()) + ['_old', 'new_globals',
                                            'retrieve_all_funcs']:
            globals().pop(item)

    directory, registry, exclusion_list = load_config(config_file)
    from tributaries import util_mod
    registry.append(util_mod)

    for module in registry:
        allfuncs = retrieve_all_funcs(module)
        globals().update(allfuncs)

    globals_list = globals()
    return globals_list


def retrieve_all_funcs(module):
    from tributaries import dec_mod
    allfuncs = vars(importlib.import_module(module))
    decorator_funcs = vars(importlib.import_module(dec_mod))
    allfuncs = {funcname: func for funcname, func in allfuncs.items()
                if funcname not in ["wraps"]
                + [key for key in decorator_funcs.keys()
                   if not key.startswith('__')]}
    for funcname, func in allfuncs.items():
        if not funcname.startswith('__'):
            if hasattr(func, "is_cacher_registered"):
                allfuncs[funcname] = undecorated(allfuncs[funcname])
    return allfuncs
