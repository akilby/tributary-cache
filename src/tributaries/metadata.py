from .utils.codeparsers import code_tree
from .utils.objecthashers import complex_hasher


def determine_metadata(func, args, kwargs,
                       exclusion_list, globals_list,
                       old_version=False):
    metadata = dict()
    metadata['func'] = func
    metadata['args'] = args
    metadata['kwargs'] = kwargs
    (metadata['code'],
        metadata['other_globals']) = code_tree(func, args, kwargs,
                                               exclusion_list, globals_list,
                                               old_version=old_version)
    if old_version:
        metadata.pop('other_globals')
    return refactor_metadata_for_storage(metadata)


def refactor_metadata_for_readability(metadata):
    m = metadata.copy()
    code = m['code']
    code = {k: '-code snipped-' for k, v in code.items()}
    args = m['args']
    args = [(arg[:20] + ['...', '-args snipped-']
             if isinstance(arg, list) and len(arg) > 20 else arg)
            for arg in args]
    args = [(set(list(arg)[:20]).union(set(['...', '-args snipped-']))
             if isinstance(arg, set) and len(arg) > 20 else arg)
            for arg in args]
    args = [dict_refactor(arg) if isinstance(arg, dict) else arg
            for arg in args]
    kwargs = m['kwargs']
    kwargs = dict_refactor(kwargs)
    other_globals = m['other_globals']
    for key, val in other_globals.items():
        if isinstance(val, list) and len(val) > 20:
            other_globals[key] = val[:20] + ['...', '-other_globals snipped-']
    m2 = metadata.copy()
    m2['code'] = code
    m2['args'] = args
    m2['kwargs'] = kwargs
    m2['other_globals'] = other_globals
    return m2


def dict_refactor(kwargs):
    for key, val in kwargs.items():
        if isinstance(val, list) and len(val) > 20:
            kwargs[key] = val[:20] + ['...', '-snipped-']
        elif isinstance(val, set) and len(val) > 20:
            kwargs[key] = set(list(val)[:20]).union(
                set(['...', '-snipped-']))
        elif isinstance(val, dict):
            for key1, val1 in val.items():
                if isinstance(val1, list) and len(val1) > 20:
                    val[key1] = val1[:20] + ['...', '-snipped-']
                    kwargs[key] = val
    return kwargs


def refactor_metadata_for_storage(metadata):
    m, m2 = metadata.copy(), metadata.copy()
    args, kwargs = m['args'], m['kwargs']
    args = [complex_hasher(arg) for arg in args]
    args = hash_arglist(args)
    kw = dict_hasher(kwargs.copy())
    m2['args'] = tuple(args)
    m2['kwargs'] = kw
    return m2


def hash_arglist(arglist):
    if isinstance(arglist, list) or isinstance(arglist, tuple):
        arglist = hash_all_in_arglist(arglist)
        argsnew = []
        for arg in arglist:
            if isinstance(arg, list) or isinstance(arg, tuple):
                arg = hash_all_in_arglist(arg)
            elif isinstance(arg, dict):
                arg = dict_hasher(arg.copy())
            argsnew.append(arg)
    if isinstance(arglist, tuple):
        return tuple(argsnew)
    elif isinstance(arglist, list):
        return argsnew
    return arglist


def hash_all_in_arglist(arglist):
    argsnew = []
    for arg in arglist:
        if isinstance(arg, list) or isinstance(arg, tuple):
            arg2 = [complex_hasher(a) for a in arg]
            arg2 = hash_all_in_arglist(arg2)
            if isinstance(arg, tuple):
                arg2 = tuple(arg2)
        else:
            arg2 = arg
        argsnew.append(arg2)
    if isinstance(arglist, tuple):
        return tuple(argsnew)
    return argsnew


def dict_hasher(kw):
    kw = kw.copy()
    for key, val in kw.items():
        kw[key] = complex_hasher(val)
        if isinstance(val, list):
            kw[key] = [complex_hasher(arg) for arg in val]
        elif isinstance(val, dict):
            m3 = val.copy()
            for key_small, val_small in m3.items():
                m3[key_small] = complex_hasher(val_small)
            kw[key] = m3
    return kw
