import builtins
import dis
import importlib
import inspect
import itertools
import types

import dill
from cache.utils.globalslister import retrieve_all_funcs
from cache.utils.utils import get_system_packages
from stdlib_list import stdlib_list
from undecorated import undecorated

# import warnings

old_version = True


def code_tree(func, args, kwargs, exclusion_list, globals_list):
    child_funcs = get_all_children(func, args, kwargs,
                                   exclusion_list, globals_list)
    code = {f: get_source(f, globals_list) for f in [func] + child_funcs}
    return code


def get_source(func, globals_list, remove_docs=True):
    sc = dill.source.getsource(globals_list[func])
    try:
        assert (sc.startswith('def %s(' % func)
                or sc.startswith('class %s(' % func))
    except AssertionError:
        try:
            sc = dill.source.getsource(undecorated(globals_list[func]))
            assert sc.startswith('@cache_decorator\ndef %s(' % func)
            # warnings.warn(
            # 'Trying out a cache decorator: still in development')
        except AssertionError:
            print('func: ', func)
            print('sc: ', sc)
            raise Exception(AssertionError)
    if remove_docs:
        return remove_docstring(sc)
    return sc


def remove_docstring(code):
    if len(code.split("'''")) == 3:
        c = code.split("'''")
    elif len(code.split('"""')) == 3:
        c = code.split('"""')
    else:
        return code
    left = c[0][:c[0].rfind('\n')] + '\n'
    right = c[2][c[2].find('\n')+1:]
    new_code = left + right
    return new_code


def remove_all_docstrings_from_metadata(m):
    for key, val in m['code'].items():
        m['code'][key] = remove_docstring(val)
    return m


def get_all_children(func, args, kwargs, exclusion_list, globals_list):
    child_funcs = func_calls(globals_list[func], globals_list)
    arg_children = [[x.__name__] + func_calls(x, globals_list) for x in args
                    if isinstance(x, types.FunctionType)]
    child_funcs = child_funcs + list(
        itertools.chain.from_iterable(arg_children))
    kwarg_children = [[x[1].__name__] + func_calls(x[1], globals_list)
                      for x in kwargs.items()
                      if isinstance(x[1], types.FunctionType)]
    child_funcs = child_funcs + list(
        itertools.chain.from_iterable(kwarg_children))
    child_funcs = child_funcs + get_cached_children(func, globals_list)
    child_funcs = [x for x in child_funcs if x not in exclusion_list]
    child_funcs = list(set(child_funcs))
    return child_funcs


def get_cached_children(func, globals_list,
                        cache_string_list=['cache.Cache(']):
    sc = dill.source.getsource(globals_list[func])
    try:
        assert (sc.startswith('def %s(' % func)
                or sc.startswith('class %s(object):' % func))
    except AssertionError:
        try:
            sc = dill.source.getsource(undecorated(globals_list[func]))
            assert sc.startswith('@cache_decorator\ndef %s(' % func)
            # warnings.warn(
            # 'Trying out a cache decorator: still in development')

        except AssertionError:
            raise AssertionError('Unknown code type')
    for cache_string in cache_string_list:
        if cache_string in sc:
            cacher_name = [x for x in sc.splitlines() if
                           cache_string in x][0].split('=')[0].strip() + '.'
            other_child_functions = list(
                set([x.split(cacher_name)[1].split('(')[0]
                     for x in sc.splitlines() if cacher_name in x
                     and not x.split(cacher_name)[0][-1].isalpha()]))
        else:
            other_child_functions = []
    import_list = [x.split('import')[1].strip()
                   for x in sc.splitlines()
                   if x.strip().startswith('from') and 'import' in x]
    for potential_cacher_name in import_list:
        cacher_name = potential_cacher_name + '.'
        other_child_functions2 = list(
            set([x.split(cacher_name)[1].split('(')[0]
                 for x in sc.splitlines() if cacher_name in x
                 and not x.split(cacher_name)[0][-1].isalpha()
                 and not x.split(cacher_name)[1].split('(')[0] == 'Cache']))
        other_child_functions = other_child_functions + other_child_functions2
    return other_child_functions


def func_calls(fct, globals_list, recursive=True):
    sys_packages = get_system_packages()
    new_list = get_function_calls(fct)
    try:
        new_list = [x for x in new_list if globals_list[x].__name__
                    not in sys_packages]
    except AttributeError:
        print('NEW LIST: ', new_list)
        print([globals_list[x] for x in new_list])
        raise Exception('weird func calls error')
    old_list = new_list
    old_list = functionize(old_list, globals_list)
    big_old_list = old_list
    while old_list != []:
        mod = old_list[0].__module__
        n = new_func_calls(old_list[0], big_old_list)
        if old_version:
            # This is where a non-registered function gets dropped
            n = [x for x in n if x in globals_list.keys()
                 and globals_list[x].__name__
                 not in sys_packages]
        else:
            # update to allow full recursion
            n_get = [x for x in n if x not in globals_list.keys()]
            if n_get:
                print('adding to globals_list by recursion')
                all_funcs = retrieve_all_funcs(mod)
                globals_list.update(all_funcs)

            n = [x for x in n if x in globals_list.keys()]
            n = [x for x in n if globals_list[x].__name__ not in sys_packages]

        new_list = new_list + n
        old_list = old_list[1:] + functionize(n, globals_list)
        big_old_list = old_list + big_old_list
    return new_list


def new_func_calls(fct, old_list):
    old_list = [x.__name__ for x in old_list]
    gfc = get_function_calls(fct)
    return [x for x in gfc if x not in old_list]


def get_function_calls(fct, built_ins=False):
    funcs = []
    bytecode = dis.Bytecode(fct)
    instrs = list(reversed([instr for instr in bytecode]))
    for (i, inst) in enumerate(instrs):
        if inst.opname[:13] == "CALL_FUNCTION":
            if not inst.opname[13:16] == "_EX":
                if inst.opname[13:16] == "_KW":
                    ep = i + inst.arg + 2
                elif inst.opname[13:16] == "_EX":
                    pass
                else:
                    ep = i + inst.arg + 1
                entry = instrs[ep]
                name = str(entry.argval)
                if ("." not in name and entry.opname == "LOAD_GLOBAL" and
                        (built_ins or not hasattr(builtins, name))):
                    funcs.append(name)
    c = 0
    for (i, inst) in enumerate(instrs):
        if inst.opname == "CALL_FUNCTION_EX":
            c = 1
        if c == 1:
            name = str(inst.argval)
            if ("." not in name and inst.opname == "LOAD_GLOBAL" and
                    (built_ins or not hasattr(builtins, name))):
                funcs.append(name)
                c = 0
    funcs = [name for name in funcs if not check_external(name)]
    funcs = [name for name in funcs if not check_more_builtins(name)]
    return funcs


def functionize(li, g):
    globals_list = g.copy()
    return_list = []
    for item in li:
        it = globals_list[item]
        if inspect.isclass(it):
            return_list = return_list + get_class_calls(it)
        elif inspect.isfunction(it) or inspect.ismodule(it):
            return_list = return_list + [it]
        else:
            raise Exception('passed a non-class, non-function, confused')
    return return_list


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


def get_class_calls(cla):
    assert inspect.isclass(cla)
    return [getattr(cla, i)
            for i in dir(cla)
            if inspect.isfunction(getattr(cla, i))]
