from stdlib_list import stdlib_list
import builtins
import warnings

import importlib
from .config import get_config

directory, registry, exclusion_list = get_config()


def check_external(name):
    if importlib.util.find_spec(name):
        if ('python' in importlib.util.find_spec(name).origin
            and ('base' in importlib.util.find_spec(name).origin
                 or 'site-packages' in importlib.util.find_spec(name).origin)):
            return True
    return False


def check_more_builtins(name):
    libraries = stdlib_list("3.7")
    if name in libraries:
        return True
    return False


def clean_funcs(funcs):
    funcs = [name for name in funcs if not hasattr(builtins, name)]
    funcs = [name for name in funcs if not check_external(name)]
    funcs = [name for name in funcs if not check_more_builtins(name)]
    funcs = [name for name in funcs if not name.startswith('__')]
    return funcs


for module in registry:
    problem_funcs = []
    new_funcs = vars(importlib.import_module(module))
    funcs = clean_funcs(list(new_funcs.keys()))
    for fct in funcs:
        if new_funcs[fct] != globals()[fct]:
            warnings.warn('Warning: updating function %s using module %s '
                          'created conflict' % (fct, module))
            problem_funcs.append(fct)
    globals().update(vars(importlib.import_module(module)))

globals_list = globals()
