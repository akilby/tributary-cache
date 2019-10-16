import glob
import os
import time
from .utils import pickle_read, pickle_dump
from .disk.operations import purge_id_in_cache


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
                       for x in glob.glob(directory+'/*')
                       if x.endswith('.pkl') and thing in x]
        li = list(set(li))
        purge_keys3 = [x for x in li if x not in counter.keys()]
    else:
        purge_keys3 = []
    return purge_keys1 + purge_keys2 + purge_keys3


def purge_cached_data(directory, days_thresh, access_thresh,
                      include_uncounted=False):
    purge_keys = list_keys_to_purge(
        directory, days_thresh, access_thresh, include_uncounted)
    print('purging %s items' % len(purge_keys))
    for id_ in purge_keys:
        purge_id_in_cache(directory, id_)
    counter_path = os.path.join(directory, 'counter.pkl')
    counter = pickle_read(counter_path)
    counter = {key: val for key, val in counter.items()
               if key not in purge_keys}
    pickle_dump(counter, counter_path)
