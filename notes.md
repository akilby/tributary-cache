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


