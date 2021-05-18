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


Consider what to do:

```python
print_statement = 'fghij'
m = 3


@cacher.register
def try_a_print_statement():
    print(print_statement)


@cacher.register
def try_a_print_multiplier(foo):
    return foo * m
```

Changing print_statement and m will *not* cause the cacher to re-run. That is handy in the first case but very bad in the second. What should I do?

Remove warnings text and print statements directly?

Finish adding non-callable globals to storage

Make sure to go back and verify name conflicts throw an error

a dictionary read in as a non-callable global can have functions inside that are not included in the code
like PD_FUNCT in utils

unclear how functions in the other_globals will work, whether it will mess up the comparison