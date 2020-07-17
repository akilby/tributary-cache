import hashlib
import importlib

packages_list = []

if importlib.util.find_spec('numpy'):
    packages_list.append('numpy')
    import numpy as np

if importlib.util.find_spec('pandas'):
    packages_list.append('pandas')
    import pandas as pd
    from pandas.util import hash_pandas_object

if importlib.util.find_spec('scipy'):
    packages_list.append('scipy')
    import scipy.sparse as sp


def hash_csr_matrix(matrix):
    return (
        str(matrix.shape) +
        hashlib.sha1(matrix.indices).hexdigest() +
        hashlib.sha1(matrix.indptr).hexdigest() +
        hashlib.sha1(matrix.data).hexdigest()
    )


def hash_numpy_array(obj):
    return hashlib.sha1(np.ascontiguousarray(obj)).hexdigest()


def complex_hasher(obj):
    hasher_count = 0
    if 'pandas' in packages_list:
        if isinstance(obj, pd.DataFrame) or isinstance(obj, pd.Series):
            # This should hopefully be temporary? something very weird
            # about the period dtype, causing problems
            # So converting to a timestamp dtype for the hasher
            pds = obj.select_dtypes(pd.PeriodDtype)
            if pds.empty:
                out = hash_pandas_object(obj).sum()
            else:
                out = hash_pandas_object(
                    obj.assign(**{col: obj[col].dt.to_timestamp()
                                  for col in pds.columns})).sum()
            hasher_count += 1
    if 'scipy' in packages_list:
        if isinstance(obj, sp.csr.csr_matrix):
            out = hash_csr_matrix(obj)
            hasher_count += 1
    if 'numpy' in packages_list:
        if isinstance(obj, np.ndarray):
            out = hash_numpy_array(obj)
            hasher_count += 1
    if hasher_count == 0:
        out = obj
        hasher_count += 1
    assert hasher_count == 1
    return out
