import glob
import os
import shutil
import warnings

from ..utils.codeparsers import remove_all_docstrings_from_metadata
from ..utils.utils import pickle_dump, pickle_read


def cache_to_disk(directory,
                  id_,
                  metadata,
                  output,
                  move_file_in_position=None):
    """
    Memoizes all output of function, and all its relevant metadata, to
    disk using pickling

    Move-file-in-position allows the system to cache a file already
    saved elsewhere to disk. This is useful if you wrote output already
    but wanted it saved, readable, and findable within the cache management
    system
    """
    try:
        pickle_dump(output,
                    os.path.join(directory, 'output_%s.pkl' % id_))
        pickle_dump(metadata,
                    os.path.join(directory, 'metadata_%s.pkl' % id_))
    except OverflowError:
        print('%s: cannot serialize a bytes object larger than 4 GiB'
              % OverflowError.__name__)
        warnings.warn('NOT SAVING, BYPASSING CACHE PROCESS')
        purge_id_in_cache(directory, id_)

    if move_file_in_position or move_file_in_position == 0:
        if isinstance(output, list) or isinstance(output, tuple):
            sc = output[move_file_in_position]
        elif isinstance(output, str) and move_file_in_position == 0:
            sc = output
        ex = os.path.splitext(sc)[1]
        ds = os.path.join(directory, 'data_%s%s' % (id_, ex))
        print('Moving data file from', sc, 'to', ds)
        shutil.move(sc, ds)
        if isinstance(output, list) or isinstance(output, tuple):
            o = list(output)
            output = o[:move_file_in_position]+[ds]+o[move_file_in_position+1:]
        elif isinstance(output, str) and move_file_in_position == 0:
            output = ds

    return output


def refactor_output(output, desti, move_file_in_position):
    return output


def search_cache(directory, metadata):
    for item in glob.glob(os.path.join(directory, 'metadata_*.pkl')):
        try:
            meta = pickle_read(item)
        except AttributeError as a:
            print('%s has created some problem' % item)
            raise Exception(AttributeError.__name__, ": ", a.args[0])
        except ModuleNotFoundError as m:
            print('%s has created some problem' % item)
            raise Exception(ModuleNotFoundError.__name__, ": ", m.args[0])
        except EOFError as eof:
            print('%s has created some problem' % item)
            raise Exception(EOFError.__name__, ": ", eof.args[0])
        try:
            if remove_all_docstrings_from_metadata(meta) == metadata:
                id_ = os.path.basename(item)
                id_ = id_.split('metadata_')[1].replace('.pkl', '')
                return id_
                break
        except ValueError as v:
            print('%s has created some problem' % item)
            print('meta: ', meta)
            print('metadata: ', metadata)
            print('Item creating problem: ', item)
            raise Exception(ValueError.__name__, ": ", v.args[0])
    return None


def purge_id_in_cache(directory, id_):
    meta_file = os.path.join(directory, 'metadata_%s.pkl' % id_)
    out_file = os.path.join(directory, 'output_%s.pkl' % id_)
    dta_file = os.path.join(directory, 'data_%s.dta' % id_)
    if os.path.isfile(meta_file):
        os.remove(meta_file)
    if os.path.isfile(out_file):
        os.remove(out_file)
    if os.path.isfile(dta_file):
        os.remove(dta_file)
    datapaths = glob.glob(os.path.join(directory, 'data_%s.*' % id_))
    if len(datapaths) == 1:
        datapath = datapaths[0]
        os.remove(datapath)
