import importlib
from .initialize_check import directory, registry


[globals().update(vars(importlib.import_module(module)))
 for module in registry]

globals_list = globals()
