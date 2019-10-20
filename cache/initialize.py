import importlib
from .config import get_config

directory, registry, exclusion_list = get_config()

[globals().update(vars(importlib.import_module(module)))
 for module in registry]

globals_list = globals()
