import copy
import importlib
import os
import pickle
import subprocess
from collections import OrderedDict

import numpy as np
from stdlib_list import stdlib_list


def pickle_dump(thing, writefile):
    with open(writefile, 'wb') as picklefile:
        # pickle.dump(thing, picklefile)
        pickle.dump(thing, picklefile, protocol=4)


def pickle_read(readfile):
    with open(readfile, 'rb') as picklefile:
        thing = pickle.load(picklefile)
    return thing


def single_item(elements):
    assert len(set(elements)) == 1
    return list(elements)[0]


def listr(item):
    return [item] if isinstance(item, str) else item


def printn(string, noisily):
    if noisily:
        print(string)


def get_system_packages():
    p = subprocess.Popen(['pip', 'list'], stdout=subprocess.PIPE)
    out, err = p.communicate()
    li = [[x for x in x.strip().split(' ') if x != '']
          for x in out.decode('utf-8').splitlines()]
    li2 = [x[0] for x in li if len(x) == 2]
    return li2


def terminal_width():
    try:
        return os.get_terminal_size().columns
    except OSError:
        return 200


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


def ordered_unique_list(list_to_set):
    return list(OrderedDict.fromkeys(list_to_set))


def flattener(d):
    """
    Expands and flattens a dictionary into a list of tuples, and
    chains/flattens lists and arrays together into one flat list
    Do this in order to make comparisons of serialized objects
    Then returned as a flattened dictionary
    """
    flattened = []
    stack = list(copy.deepcopy(d).items())
    while stack:
        k, v = stack.pop()
        if isinstance(v, dict):
            stack.extend(v.iteritems())
        elif isinstance(v, list) or isinstance(v, tuple):
            v = flatten(v)
            flattened.append((k, v))
        elif isinstance(v, np.ndarray):
            v = flatten(v)
            flattened.append((k, v))
        else:
            flattened.append((k, v))
    return dict(flattened)


def flatten(A):
    """
    Generator that flattens a list
    """
    rt = []
    for i in A:
        if isinstance(i, list) or isinstance(i, np.ndarray):
            rt.extend(flatten(i))
        else:
            rt.append(i)
    return rt
