import importlib
from .config import get_config
from .utils.utils import check_external, check_more_builtins
import builtins
import warnings

directory, registry, exclusion_list = get_config()


def clean_funcs(funcs):
    funcs = [name for name in funcs if not hasattr(builtins, name)]
    funcs = [name for name in funcs if not check_more_builtins(name)]
    funcs = [name for name in funcs if not check_external(name)]
    funcs = [name for name in funcs if not name.startswith('__')]
    return funcs


for module in registry:
    new_funcs = vars(importlib.import_module(module))
    funcs = clean_funcs(list(new_funcs.keys()))
    for fct in funcs:
        if fct in globals():
            if new_funcs[fct] != globals()[fct]:
                warnings.warn('Warning: updating function %s using module %s '
                              'created conflict' % (fct, module))
    globals().update(vars(importlib.import_module(module)))

globals_list = globals()
