
import os
import glob
import time
import dill
import types
import itertools
import shutil
import pandas as pd
from pandas.util import hash_pandas_object
from project_management.helper import (pickle_dump, pickle_read, func_calls,
                                       hash_csr_matrix)
from project_management import cache_directory
import xgboost as xgb
import scipy.sparse as sp
import hashlib
import numpy as np


from project_management.marketscan.import_claims import *
from project_management.marketscan.ml_data import *
from project_management.marketscan.marketscan import *
from project_management.marketscan.process_functions import *
from project_management.marketscan.chunk_handlers import *
from project_management.marketscan.memoized import *
from project_management.marketscan.bayes_tuning import *
from project_management.marketscan.xgb import *
from project_management.stata import *
from project_management.helper import *
from jobs.job import *
from jobs.run import *
from jobs.helper import *
from jobs.canned import *
from jobs.slurm import *
from jobs.working import *


refresh = lambda x: globals().update(x)

exclusion_list = ['BayesianOptimization', 'LogisticRegression']

# also (but not using): globals().update(globals())
# Global refresh in another place:
# cache.refresh(globals())
# cache.refresh({'generic_multi_load': globals()['generic_multi_load']})


class Cache(object):
    """
    This is essentially a memoize-to-disk class.
    If you instantiate a class object, you can memoize a function as
    an attribute
    It's a bit kludgy, but very handy for one-off function runs
    First, c = cache.Cache()
    Then any func can be run: out = c.func(args)
    This does its best to search child code but it definitely
    does not work perfectly
    For example most things called inside a class like RunScript don't
    seem to stick
    """
    def __init__(self, directory=cache_directory):
        self.directory = directory
        self.counter_path = os.path.join(self.directory, 'counter.pkl')

    def __getattr__(self, attr):
        return self.__get_global_handler(attr)

    def __get_global_handler(self, name):
        handler = self.__global_handler
        handler.__func__.func_name = name
        return handler

    def __global_handler(self, *args, purge=False, file_pos=None,
                         noisily=True, recursive=True, noisy_meta=False,
                         **kwargs):
        func = self.__global_handler.__func__.func_name
        if recursive:
            child_funcs = self.get_all_children(func, args, kwargs, noisily)
            code = {f: self.getsource(f) for f in [func] + child_funcs}
        else:
            code = self.getsource(func)
        metadata = {'func': func, 'args': args, 'kwargs': kwargs, 'code': code}
        metadata = self.refactor_metadata_for_storage(metadata)
        # print(metadata)
        was_archived = False
        id = search_cache(self.directory, metadata)
        nf = ' not found;'
        counter = pickle_read(self.counter_path)
        if id:
            if purge:
                printn('Data purged with ID %s' % id, noisily)
                del counter[id]
                id = purge_id_in_cache(self.directory, id)
                nf = ''
            else:
                printn('Data found with ID %s; loading' % id, noisily)
                try:
                    output = pickle_read(os.path.join(self.directory,
                                                      'output_%s.pkl' % id))
                except EOFError:
                    print('%s: Ran out of input' % EOFError.__name__)
                    del counter[id]
                    id = purge_id_in_cache(self.directory, id)
                    nf = ''
                try:
                    t = round(time.time()*1000000)
                    counter[id] = (counter[id][0] + 1, t)
                except KeyError:
                    print('Note: Counter KeyError')
                    counter[id] = (1, round(time.time()*1000000))
                was_archived = True
        if not id:
            print('Cache not found; running and caching: %s' % func)
            output = globals()[func](*args, **kwargs)
            timestamp = '%s' % round(time.time()*1000000)
            printn('Data%s created with ID %s' % (nf, timestamp), noisily)
            dump_cache(self.directory, timestamp, metadata, output, file_pos)
            id = timestamp
            counter[id] = (1, round(time.time()*1000000))
        if not noisy_meta:
            printn('Metadata (abbreviated): '
                   '%s' % self.refactor_metadata(metadata), noisily)
        else:
            printn('Metadata: %s' % metadata, noisily)
        setattr(self, '_meta_%s' % id,  metadata)
        setattr(self, '_meta_%s_was_archived' % id,  was_archived)
        assert id in counter
        pickle_dump(counter, self.counter_path)
        if file_pos or file_pos == 0:
            # dirpath = os.path.join(self.directory, 'data_%s.dta' % id)
            dirpaths = glob.glob(
                os.path.join(self.directory, 'data_%s.*' % id))
            assert len(dirpaths) == 1
            dirpath = dirpaths[0]
            if isinstance(output, str):
                output = [output]
                isstr = True
            else:
                output = list(output)
                isstr = False
            output = output[:file_pos]+[dirpath]+output[file_pos+1:]
            if isstr:
                output = output[0]
        return output

    def getsource(self, func):
        sc = dill.source.getsource(globals()[func])
        assert (sc.startswith('def %s(' % func)
                or sc.startswith('class %s(object):' % func))
        return sc

    def get_cached_children(self, func):
        sc = dill.source.getsource(globals()[func])
        assert (sc.startswith('def %s(' % func)
                or sc.startswith('class %s(object):' % func))
        if 'cache.Cache()' in sc:
            cacher_name = [x for x in sc.splitlines() if
                           'cache.Cache()' in x][0].split('=')[0].strip() + '.'
            other_child_functions = list(
                set([x.split(cacher_name)[1].split('(')[0]
                     for x in sc.splitlines() if cacher_name in x
                     and not x.split(cacher_name)[0][-1].isalpha()]))
        else:
            other_child_functions = []
        return other_child_functions

    def get_all_children(self, func, args, kwargs, noisily):
        # print(globals().keys())
        child_funcs = func_calls(globals()[func], globals())
        arg_children = [[x.__name__] + func_calls(x, globals()) for x in args
                        if isinstance(x, types.FunctionType)]
        child_funcs = child_funcs + list(
            itertools.chain.from_iterable(arg_children))
        kwarg_children = [[x[1].__name__] + func_calls(x[1], globals())
                          for x in kwargs.items()
                          if isinstance(x[1], types.FunctionType)]
        child_funcs = child_funcs + list(
            itertools.chain.from_iterable(kwarg_children))
        child_funcs = child_funcs + self.get_cached_children(func)
        child_funcs = [x for x in child_funcs if x not in exclusion_list]
        print('List of all children functions found:', child_funcs)
        return child_funcs

    def refactor_metadata(self, metadata):
        m = metadata.copy()
        code = m['code']
        code = {k: '-code snipped-' for k, v in code.items()}
        args = m['args']
        args = [(arg[:100] + ['...', '-args snipped-']
                 if isinstance(arg, list) and len(arg) > 100 else arg)
                for arg in args]
        kwargs = m['kwargs']
        for key, val in kwargs.items():
            if isinstance(val, list) and len(val) > 100:
                kwargs[key] = val[:100] + ['...', '-kwarg snipped-']
        m2 = metadata.copy()
        m2['code'] = code
        m2['args'] = args
        m2['kwargs'] = kwargs
        return m2

    def refactor_metadata_for_storage(self, metadata):
        m = metadata.copy()
        # print('META1:', m)
        args = m['args']
        kwargs = m['kwargs']
        # This should probably reset_index first
        args = [(hash_pandas_object(arg).sum()
                 if isinstance(arg, pd.DataFrame) else arg)
                for arg in args]
        args = [(hash(arg) if isinstance(arg, xgb.core.DMatrix)
                 else arg) for arg in args]
        args = [(hash_csr_matrix(arg) if isinstance(arg, sp.csr.csr_matrix)
                 else arg) for arg in args]
        args = [(hashlib.sha1(np.ascontiguousarray(arg)).hexdigest()
                if isinstance(arg, np.ndarray)
                 else arg) for arg in args]
        args = hash_dfs(args)
        kw = kwargs.copy()
        for key, val in kw.items():
            if isinstance(val, pd.DataFrame):
                kw[key] = hash_pandas_object(val).sum()
            elif isinstance(val, list):
                val2 = [(hash_pandas_object(arg).sum()
                         if isinstance(arg, pd.DataFrame) else arg)
                        for arg in val]
                kw[key] = val2
            elif isinstance(val, dict):
                m3 = val.copy()
                for key_small, val_small in m3.items():
                    if isinstance(val_small, pd.DataFrame):
                        m3[key_small] = hash_pandas_object(
                            val_small).sum()
                kw[key] = m3
        m2 = metadata.copy()
        m2['args'] = tuple(args)
        m2['kwargs'] = kw
        # print('META2:', metadata)
        # print('META3:', m2)
        return m2


def hash_dfs(arglist):
    if isinstance(arglist, list) or isinstance(arglist, tuple):
        arglist = hash_df_in_list(arglist)
        argsnew = []
        for arg in arglist:
            if isinstance(arg, list) or isinstance(arg, tuple):
                arg = hash_df_in_list(arg)
            argsnew.append(arg)
    if isinstance(arglist, tuple):
        return tuple(argsnew)
    return arglist


def hash_df_in_list(arglist):
    argsnew = []
    for arg in arglist:
        if isinstance(arg, list) or isinstance(arg, tuple):
            arg2 = [(hash_pandas_object(a).sum()
                    if isinstance(a, pd.DataFrame) else a)
                    for a in arg]
            arg2 = hash_df_in_list(arg2)
            if isinstance(arg, tuple):
                arg2 = tuple(arg2)
        else:
            arg2 = arg
        argsnew.append(arg2)
    if isinstance(arglist, tuple):
        return tuple(argsnew)
    return argsnew


def dump_cache(directory, id, metadata, output, file_pos=None):
    try:
        pickle_dump(output,
                    os.path.join(directory, 'output_%s.pkl' % id))
        pickle_dump(metadata,
                    os.path.join(directory, 'metadata_%s.pkl' % id))
    except OverflowError:
        print('%s: cannot serialize a bytes object larger than 4 GiB'
              % OverflowError.__name__)
        print('NOT SAVING, BYPASSING CACHE')
        filepath = os.path.join(directory, 'output_%s.pkl' % id)
        metapath = os.path.join(directory, 'metadata_%s.pkl' % id)
        if os.path.exists(filepath):
            print('removing partially saved file', filepath)
            os.remove(filepath)
        if os.path.exists(metapath):
            print('removing metadata', filepath)
            os.remove(metapath)
    if file_pos or file_pos == 0:
        if isinstance(output, list) or isinstance(output, tuple):
            sc = output[file_pos]
        elif isinstance(output, str):
            sc = output
        ex = os.path.splitext(sc)[1]
        desti = os.path.join(directory, 'data_%s%s' % (id, ex))
        print('Moving from', sc, 'to', desti)
        shutil.move(sc, desti)


def search_cache(directory, metadata):
    for item in glob.glob(os.path.join(directory, 'metadata_*.pkl')):
        # print(item)
        meta = pickle_read(item)
        if meta == metadata:
            id = os.path.basename(item)
            id = id.split('metadata_')[1].replace('.pkl', '')
            return id
            break
    return None


def list_keys_to_purge(directory, days_thresh, access_thresh,
                       include_uncounted=False):
    counter_path = os.path.join(directory, 'counter.pkl')
    counter = pickle_read(counter_path)
    purge_keys1 = [key for key, x in counter.items()
                   if isinstance(x[1], str) and x[0] <= access_thresh]
    purge_keys2 = [key for key, x in counter.items()
                   if not isinstance(x[1], str) and x[0] <= access_thresh
                   and (time.time()-x[1]/1000000)/(60*60*24) > days_thresh]
    if include_uncounted:
        li = []
        for thing in ('output_', 'metadata_', 'data_'):
            li = li + [x.split('.pkl')[0].split(thing)[1]
                       for x in glob.glob(cache_directory+'/*')
                       if x.endswith('.pkl') and thing in x]
        li = list(set(li))
        purge_keys3 = [x for x in li if x not in counter.keys()]
    else:
        purge_keys3 = []
    return purge_keys1 + purge_keys2 + purge_keys3


def purge_id_in_cache(directory, id):
    meta_file = os.path.join(directory, 'metadata_%s.pkl' % id)
    out_file = os.path.join(directory, 'output_%s.pkl' % id)
    dta_file = os.path.join(directory, 'data_%s.dta' % id)
    if os.path.isfile(meta_file):
        os.remove(meta_file)
    if os.path.isfile(out_file):
        os.remove(out_file)
    if os.path.isfile(dta_file):
        os.remove(dta_file)
    datapaths = glob.glob(os.path.join(directory, 'data_%s.*' % id))
    if len(datapaths) == 1:
        datapath = datapaths[0]
        os.remove(datapath)


def purge_cached_data(directory, days_thresh, access_thresh,
                      include_uncounted=False):
    purge_keys = list_keys_to_purge(
        directory, days_thresh, access_thresh, include_uncounted)
    print('purging %s items' % len(purge_keys))
    for id in purge_keys:
        purge_id_in_cache(directory, id)
    counter_path = os.path.join(directory, 'counter.pkl')
    counter = pickle_read(counter_path)
    counter = {key: val for key, val in counter.items()
               if key not in purge_keys}
    pickle_dump(counter, counter_path)


def printn(string, noisily):
    if noisily:
        print(string)
