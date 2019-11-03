import pickle
import subprocess
import os
import importlib
from stdlib_list import stdlib_list


def pickle_dump(thing, writefile):
    with open(writefile, 'wb') as picklefile:
        pickle.dump(thing, picklefile)


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
    print(name)
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
