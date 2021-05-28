import copy
import hashlib
import importlib
import pickle
import tempfile

from utils.utils import flattener

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


if importlib.util.find_spec('sklearn'):
    packages_list.append('sklearn')
    from sklearn.decomposition import LatentDirichletAllocation
    from sklearn.feature_extraction.text import CountVectorizer


def hash_csr_matrix(matrix):
    return (
        str(matrix.shape) +
        hashlib.sha1(matrix.indices).hexdigest() +
        hashlib.sha1(matrix.indptr).hexdigest() +
        hashlib.sha1(matrix.data).hexdigest()
    )


def hash_numpy_array(obj):
    return hashlib.sha1(np.ascontiguousarray(obj)).hexdigest()


def serializable_lda_object(obj):
    attribute_dict = copy.deepcopy(vars(obj))
    attribute_dict['random_state_'] = obj.random_state_.get_state()
    flat_attribute_dict = flattener(attribute_dict)
    assert unique_serialization(flat_attribute_dict)[0]
    print('Warning: Attempting to uniquely serialize a '
          'LatentDirichletAllocation object')
    return flat_attribute_dict


def serializable_vectorizer_object(obj):
    attribute_dict = copy.deepcopy(vars(obj))
    assert unique_serialization(attribute_dict)[0]
    print('Warning: Attempting to uniquely serialize a CountVectorizer object')
    return attribute_dict


def complex_hasher(obj):
    hasher_count = 0
    if 'pandas' in packages_list:
        # The fix for quarter periods should hopefully be temporary?
        # something very weird about the period dtype, causing problems
        # So converting to a timestamp dtype for the hasher
        if isinstance(obj, pd.DataFrame):
            pds = obj.select_dtypes(pd.PeriodDtype)
            if pds.empty:
                out = hash_pandas_object(obj).sum()
            else:
                out = hash_pandas_object(
                    obj.assign(**{col: obj[col].dt.to_timestamp()
                                  for col in pds.columns})).sum()
            hasher_count += 1
        elif isinstance(obj, pd.Series):
            pds = pd.DataFrame(obj).select_dtypes(pd.PeriodDtype)
            if pds.empty:
                out = hash_pandas_object(obj).sum()
            else:
                out = hash_pandas_object(obj.dt.to_timestamp()).sum()
            hasher_count += 1
    if 'scipy' in packages_list:
        if isinstance(obj, sp.csr.csr_matrix):
            out = hash_csr_matrix(obj)
            hasher_count += 1
    if 'numpy' in packages_list:
        if isinstance(obj, np.ndarray):
            out = hash_numpy_array(obj)
            hasher_count += 1
    if 'sklearn' in packages_list:
        if isinstance(obj, LatentDirichletAllocation):
            if not unique_serialization(obj)[0]:
                out = serializable_lda_object(obj)
                hasher_count += 1
        if isinstance(obj, CountVectorizer):
            if not unique_serialization(obj)[0]:
                out = serializable_vectorizer_object(obj)
                hasher_count += 1
    if hasher_count == 0:
        out = obj
        hasher_count += 1
    assert hasher_count == 1
    return out


def unique_serialization(obj):
    """
    Checks whether obj is serialized in a fashion that produces a
    unique representation. If this returns false, cacher will always conclude
    that any function with obj as an argument is fresh

    Returns examples of the object in pre-and-post pickled form
    """
    with tempfile.NamedTemporaryFile() as tmp_file:
        pickle.dump(obj, tmp_file)
        tmp_file.flush()

        new_obj = pickle.load(open(tmp_file.name, 'rb'))
        cond = obj == new_obj
        return cond, obj, new_obj


def detect_problems_in_serialization(obj):
    """
    Runs through writeable attributes looking for cases
    where serialization produces a non-stable result
    """
    cond, obj1, obj2 = unique_serialization(obj)
    if not cond:
        assert vars(obj1).keys() == vars(obj2).keys()
        for key, val in vars(obj1).items():
            try:
                cond = vars(obj2)[key] != val
                assert isinstance(cond, bool)
            except AssertionError:
                cond = (vars(obj2)[key] != val).any()
            if cond:
                return key, val, vars(obj2)[key]
