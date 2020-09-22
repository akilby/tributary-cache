# cache - complex file-based memoization and caching


This is a complex file-based memoization package. It has two distinguishing features:

1. Memoization is written to disk, and is not in-memory, so memoization is persistent across sessions.
2. Memoization accounts for changes in the function's code, as well as the code of other functions called from the memoized function.


It is transparent and portable, in that metadata and the outputs of the function are pickled in a readable format. It also has various optimizations to assist in work with large file sizes, like hashing pandas data frames.

If you instantiate a Cache object, you can call any registered function as a method of the class:

```
c = cache.Cache()

out = c.myfunc(args)
```
Note that the registered function `myfunc` also remains a regular function and does not *need* to be memoized.

It's still kludgy, but very handy.

Warning: this package does its best to search for all functions called by the memoized function, but it definitely does not yet work perfectly. For example, some function called inside a class don't seem to be recognized.



## Command Line Setup ##

This package comes with a command line utility to facilitate set up:

`cache configure`

This will prompt you to:
1. Set the directory on disk where caches will be stored
2. Provide a list of user-written packages for registry with the cacher
3. Specify which submodules of the packages to register
	(on first run, specifying 'n' at "Prompt submodules?" will register all submodules)
