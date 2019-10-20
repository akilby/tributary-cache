import importlib
from .config import get_config, load_config

directory, registry, exclusion_list = get_config()

[globals().update(vars(importlib.import_module(module)))
 for module in registry]

globals_list = globals()


def return_alternative_globals(config_file):
    directory, registry, exclusion_list = load_config(config_file)

    [globals().update(vars(importlib.import_module(module)))
     for module in registry]

    globals_list = globals()
    return globals_list
