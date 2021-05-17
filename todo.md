## Notes/upgrades ##

If function foo.bar calls blah.bar, name conflicts can maybe be a problem (?) need to test; may only be in old version

Could use functions themselves as the dictionary key in globals_list, to prevent any conflicts in session

And prepend module names in the cacher dictionary... but this might make things much less portable (right now as long as code itself matches, doesn't matter where it lives)

Perhaps set a way to universally disable the cache decorator. so you install the package then disable it

Fix this: Warning: this package does its best to search for all functions called by the memoized function, but it does not yet work perfectly. For example, some functions called inside a class don't seem to be recognized.

In decorator: TO DO: This is a workaround; should move to using only
an attribute on the wrapper

Fix:
* Cache found - loading from ID None:
* Cache not found; running
