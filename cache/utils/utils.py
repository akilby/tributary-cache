import pickle
import subprocess


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
