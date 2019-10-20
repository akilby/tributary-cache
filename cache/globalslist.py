import importlib
from .config import load_config

old_globals = globals().copy()


def new_globals(config_file):
    directory, registry, exclusion_list = load_config(config_file)

    [globals().update(vars(importlib.import_module(module)))
     for module in registry]

    globals_list = globals()
    return globals_list
