# cache

Complex file-based memoization and caching

## Command Line Setup ##

* This package comes with a command line utility for set up:

`cache configure` 

This will prompt you to:
1. Set the directory on disk where caches will be stored
2. Provide a list of user-written packages for registry with the cacher
3. Specify which submodules of the packages to register
	(on first run, specifying 'n' at "Prompt to include all submodules" will register all submodules)
