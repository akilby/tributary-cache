import os
import sys
import time


def hash_id():
    return str(hash(time.time()) % ((sys.maxsize + 1) * 2))


def hash_write_to_dta(df, tempdir, write_index=True):
    filepath = os.path.join(tempdir, 'dtafile_%s.dta' % hash_id())
    df.to_stata(df, filepath, write_index=write_index)
    return filepath
