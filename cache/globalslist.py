import importlib
from .config import load_config

_old = globals().copy()


def new_globals(config_file):

    current_globals = globals().copy()
    for item in list(current_globals.keys()):
        if item not in list(_old.keys()) + ['_old', 'new_globals']:
            globals().pop(item)

    directory, registry, exclusion_list = load_config(config_file)

    [globals().update(vars(importlib.import_module(module)))
     for module in registry]

    globals_list = globals()
    return globals_list
