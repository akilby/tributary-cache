import builtins
import dis
import importlib
import inspect
import itertools
import types

import dill
from stdlib_list import stdlib_list
from undecorated import undecorated

from .globalslister import retrieve_all_funcs
from .utils import get_system_packages, ordered_unique_list


def code_tree(func, args, kwargs,
              exclusion_list, globals_list,
              old_version=False):
    (child_funcs,
        non_callables,
        updated_globals_list) = get_all_children(func, args, kwargs,
                                                 exclusion_list, globals_list,
                                                 old_version=old_version)
    code = {f: get_source(f, updated_globals_list)
            for f in [func] + child_funcs}
    return code


def get_source(func, globals_list, remove_docs=True):
    sc = dill.source.getsource(globals_list[func])
    try:
        assert (sc.startswith('def %s(' % func)
                or sc.startswith('class %s(' % func))
    except AssertionError:
        try:
            # sc = dill.source.getsource(undecorated(globals_list[func]))
            # assert sc.startswith('@cache_decorator\ndef %s(' % func)
            assert undecorated(globals_list[func]).is_cacher_registered
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


def get_all_children(func, args, kwargs,
                     exclusion_list, globals_list,
                     old_version=False):
    # Function calls from the top level function
    child_funcs, non_callable_globals, new_globals_list = func_calls(
        globals_list[func], globals_list, old_version=old_version)

    # Function calls inside the arguments list
    arg_functions = [x for x in args if isinstance(x, types.FunctionType)]
    arg_function_names = [x.__name__ for x in arg_functions]
    arg_children = [func_calls(x,
                               retrieve_all_funcs(x.__module__),
                               old_version=old_version)
                    for x in arg_functions]
    arg_children_globals = [x[2] for x in arg_children]
    arg_noncallables = [x[1] for x in arg_children]
    arg_children = [x[0] for x in arg_children]

    # Function calls inside the kwarguments list
    kwarg_functions = [val for val in kwargs.values()
                       if isinstance(val, types.FunctionType)]
    kwarg_function_names = [val.__name__ for val in kwarg_functions]
    kwarg_children = [func_calls(val,
                                 retrieve_all_funcs(val.__module__),
                                 old_version=old_version)
                      for val in kwarg_functions]
    kwarg_children_globals = [x[2] for x in kwarg_children]
    kwarg_noncallables = [x[1] for x in kwarg_children]
    kwarg_children = [x[0] for x in kwarg_children]

    # Check there are no conflicting functions in the globals lists:
    check_name_collisions(globals_list, new_globals_list)
    globals_list.update(new_globals_list)
    for new_globs in arg_children_globals + kwarg_children_globals:
        check_name_collisions(globals_list, new_globs)
        globals_list.update(new_globs)

    # Add all found child funcs to the list
    child_funcs = (child_funcs
                   + arg_function_names
                   + kwarg_function_names
                   + list(itertools.chain.from_iterable(arg_children))
                   + list(itertools.chain.from_iterable(kwarg_children)))

    child_funcs = child_funcs + get_cached_children(func, globals_list)
    child_funcs = [x for x in child_funcs if x not in exclusion_list]
    child_funcs = list(set(child_funcs))

    # Non-callable globals
    non_callables = (non_callable_globals
                     + list(itertools.chain.from_iterable(arg_noncallables))
                     + list(itertools.chain.from_iterable(kwarg_noncallables)))

    return child_funcs, non_callables, globals_list


def get_cached_children(func, globals_list,
                        cache_string_list=['cache.Cache(']):
    sc = dill.source.getsource(globals_list[func])
    try:
        assert (sc.startswith('def %s(' % func)
                or sc.startswith('class %s(object):' % func))
    except AssertionError:
        try:
            # sc = dill.source.getsource(undecorated(globals_list[func]))
            # assert sc.startswith('@cache_decorator\ndef %s(' % func)
            assert undecorated(globals_list[func]).is_cacher_registered
            # should take out the first two lines here and above
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


def func_calls(fct, globals_list, old_version=False):
    """
    This is the function where most of the management and searching
    action happens. get_function_calls actually parses the code itself
    """
    sys_packages = get_system_packages()
    new_list = get_function_calls(fct, old_version=old_version)
    if not old_version:
        new_list = [globals_list[x].__package__
                    if hasattr(globals_list[x], '__package__')
                    else x for x in new_list]
        package_aliases = {globals_list[key].__package__: val
                           for key, val in globals_list.items()
                           if hasattr(globals_list[key], '__package__')
                           and globals_list[key].__package__
                           not in [key, ''] + list(globals_list.keys())}
        globals_list.update(package_aliases)
    try:
        new_list = [x for x in new_list if globals_list[x].__name__
                    not in sys_packages]
    except AttributeError:
        print('NEW LIST: ', new_list)
        print([globals_list[x] for x in new_list])
        raise Exception('weird func calls error')
    non_callable_globals = []
    old_list = new_list
    old_list = functionize(old_list, globals_list)
    big_old_list = old_list
    while old_list != []:
        mod = old_list[0].__module__

        if old_version:
            # This is where a non-registered function gets dropped
            n = new_func_calls(
                old_list[0], big_old_list, old_version=old_version)
            n = [x for x in n if x in globals_list.keys()
                 and globals_list[x].__name__
                 not in sys_packages]
        else:
            # update to allow full recursion
            n = get_function_calls(old_list[0], old_version=old_version)
            all_new_funcs = retrieve_all_funcs(mod)
            all_new_funcs = {key: val for key, val in all_new_funcs.items()
                             if key in n}
            check_name_collisions(globals_list, all_new_funcs)
            globals_list.update(all_new_funcs)

            n = [globals_list[x].__package__
                 if hasattr(globals_list[x], '__package__')
                 else x for x in n]
            package_aliases = {globals_list[key].__package__: val
                               for key, val in globals_list.items()
                               if hasattr(globals_list[key], '__package__')
                               and globals_list[key].__package__
                               not in [key, ''] + list(globals_list.keys())}
            globals_list.update(package_aliases)

            n = [x for x in n if x in globals_list.keys()]
            non_callable = [x for x in n
                            if not callable(globals_list[x])
                            and not hasattr(globals_list[x], '__package__')]
            n = [x for x in n if x not in non_callable]
            n = [x for x in n if globals_list[x].__name__ not in sys_packages]
            non_callable_globals = non_callable_globals + non_callable

        new_list = new_list + n
        old_list = old_list[1:] + functionize(n, globals_list)
        big_old_list = old_list + big_old_list
        new_list = ordered_unique_list(new_list)
        non_callable_globals = ordered_unique_list(non_callable_globals)
    new_globals_list = {key: val for key, val in globals_list.items()
                        if key in new_list}
    return new_list, non_callable_globals, new_globals_list


def check_name_collisions(globals_dict1, globals_dict2):
    name_collisions = [key for key, val in globals_dict2.items()
                       if key in globals_dict1
                       and val != globals_dict1[key]]
    if name_collisions:
        raise Exception('You have two functions with a name'
                        ' collision that are not from the same module.'
                        ' Functions in modules: ',
                        {key: val.__module__ for key, val
                         in globals_dict2.items()},
                        'and',
                        {key: val.__module__ for key, val
                         in globals_dict1.items()
                         if key in globals_dict2})


def new_func_calls(fct, old_list, old_version):
    old_list = [x.__name__ for x in old_list]
    gfc = get_function_calls(fct, old_version=old_version)
    return [x for x in gfc if x not in old_list]


def get_function_calls(fct, built_ins=False, old_version=False):
    bytecode = dis.Bytecode(fct)
    instrs = list(reversed([instr for instr in bytecode]))
    if old_version:
        funcs = get_function_calls_old_version(
            instrs, built_ins=built_ins, old_version=old_version)
    else:
        funcs = []
        for (i, inst) in enumerate(instrs):
            if inst.opname == "LOAD_GLOBAL":
                funcs.append(str(inst.argval))

    funcs = [name for name in funcs if not hasattr(builtins, name)]
    funcs = [name for name in funcs if not check_more_builtins(name)]
    funcs = [name for name in funcs if not check_external(name)]
    funcs = ordered_unique_list(funcs)
    return funcs


def get_function_calls_old_version(instrs, built_ins=False, old_version=False):
    funcs = []
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
                print(i, inst, ep, entry)
                name = str(entry.argval)
                if ("." not in name and
                        entry.opname == "LOAD_GLOBAL" and
                        (built_ins or
                            not hasattr(builtins, name))):
                    funcs.append(name)
                else:
                    if not old_version and inst.opname[13:16] == "_KW":
                        # Check next line... possibly only for _KW?
                        # Doing that for now
                        ep = ep + 1
                        entry = instrs[ep]
                        print(i, inst, ep, entry)
                        name = str(entry.argval)
                        if ("." not in name and
                                entry.opname == "LOAD_GLOBAL" and
                                (built_ins or
                                    not hasattr(builtins, name))):
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


# def check_external(name, globals_list):
#     def ce(name):
#         if importlib.util.find_spec(name):
#             if ('python' in importlib.util.find_spec(name).origin
#                 and ('base' in importlib.util.find_spec(name).origin
#                      or 'site-packages' in importlib.util.find_spec(name).origin)):
#                 return True
#         return False
#     if ce(name):
#         return True
#     elif name in globals_list:
#         name = globals_list[name].__name__
#         return ce(name)
#     else:
#         return False

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
