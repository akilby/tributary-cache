import importlib
from .config import get_config
from .initialize_check import problem_funcs

print('Note: the following are potential update conflicts: ', problem_funcs)

directory, registry, exclusion_list = get_config()

[globals().update(vars(importlib.import_module(module)))
 for module in registry]

globals_list = globals()
