#  tributary-cache

*Complex file-based memoization and caching*

This is a complex file-based memoization package. It has two distinguishing features:

1. Memoization is written to disk, and is not in-memory, so memoization is persistent across sessions.
2. Memoization accounts for changes in the function's code, as well as the code of other user-written functions (dependencies) called from the memoized function.

It is transparent and portable, in that metadata and the outputs of the function are pickled in a readable format. It also has various optimizations to assist in work with large file sizes, like hashing pandas data frames.

It's still kludgy, but very handy, especially for data science workflows. If you have scripts that process data, you can wrap them in a function, register the function, and the cacher will save to disk and retrieve it whenever you need it, eliminating the need for many poorly-named saved files produced by intermediate steps of data cleaning or processing.

Warning: this package does its best to search for all functions called by the memoized function, but it does not yet work perfectly. To be safe, you can set the rerun flag to True at the end of the project, and it will rerun everything from scratch. (Alternatively, this can be done by pointing the cacher to a fresh cache directory with no files.)


```python
from tributaries import Cacher
cacher = Cacher(directory='/path/to/cache/directory/', verbose=0, rerun=False)


@cacher.register
def clean_my_data(df_raw):
    df_intermed1 = time_consuming_cleaning_process1(df_raw)
    df_intermed2 = time_consuming_cleaning_process2(df_intermed1)
    df_final = time_consuming_cleaning_process3(df_intermed2)
    return df_final
```
If function `clean_my_data` is registered, the first run will be time-consuming, but subsequent runs will load nearly-instantly, provided the code of the function and all dependencies have not changed.

Dependency functions such `time_consuming_cleaning_process1` can be themselves registered, to save time while working on intermediate cleaning steps. Whether or not they are not registered, changes to their code will still prompt `clean_my_data` to re-run if called.

Built-in functions, functions from system packages, and functions from other installed packages are not searched as dependencies.


