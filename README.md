#  tributary-cache - complex file-based memoization and caching

This is a complex file-based memoization package. It has two distinguishing features:

1. Memoization is written to disk, and is not in-memory, so memoization is persistent across sessions.
2. Memoization accounts for changes in the function's code, as well as the code of other functions (dependencies) called from the memoized function.

It is transparent and portable, in that metadata and the outputs of the function are pickled in a readable format. It also has various optimizations to assist in work with large file sizes, like hashing pandas data frames.

It's still kludgy, but very handy, especially for data science workflows. If you have scripts that process data, you can wrap them in a function, register the function, and the cacher will save to disk and retrieve it whenever you need it, eliminating the need for many poorly-named saved files produced by intermediate steps of data cleaning or processing.

Warning: this package does its best to search for all functions called by the memoized function, but it does not yet work perfectly. For example, some functions called inside a class don't seem to be recognized.


```
from tributaries import Cacher
cacher = Cacher(directory='/scratch/akilby/Output/Cache/temp', verbose=0)

@cacher.register
def clean_my_data(df_raw):
  df_intermed1 = time_consuming_cleaning_process1(df_raw)
  df_intermed2 = time_consuming_cleaning_process2(df_intermed1)
  df_final = time_consuming_cleaning_process3(df_intermed2)
  return df_final
```
If clean_my_data is registered, the first run will be time-consuming, but subsequent runs will load nearly-instantly, provided the code of the function and dependencies has not changed.

Dependency functions such time_consuming_cleaning_process1 can be themselves registered, to save time while working on intermediate cleaning steps.



## Command Line Setup - Deprecated version of package ##

This package comes with a command line utility to facilitate set up:

`cache configure`

This will prompt you to:
1. Set the directory on disk where caches will be stored
2. Provide a list of user-written packages for registry with the cacher
3. Specify which submodules of the packages to register
	(on first run, specifying 'n' at "Prompt submodules?" will register all submodules)


If you instantiate a Cache object, you can call any registered function as a method of the cache instance:

```
c = cache.Cache()

out = c.foo(args)
```
Note that the registered function `foo` also remains a regular function and does not *need* to be memoized.


