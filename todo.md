## Notes/upgrades ##

If function foo.bar calls blah.bar, function name conflicts will throw an error. Could use functions themselves as the dictionary key in globals_list, to prevent any conflicts in session.

Also could prepend module names in the cacher dictionary... but this might make things much less portable (right now as long as code itself matches, doesn't matter where it lives)

Perhaps set a way to universally disable the cache decorator. so you install the package then disable it. Could use a "dummy cacher" module that is imported instead of tributaries.

Warning: this package does its best to search for all functions called by the memoized function, but it does not yet work perfectly. Major improvements have been made. Some functions called inside a class may not be recognized - this need to be checked.

*To Do:*

* In decorator modudule: "TO DO: This is a workaround; should move to using only an attribute on the wrapper

* Remove warnings text and print statements directly from cacher visibility?

* A dictionary read in as a non-callable global can have functions inside that are not included in the code
like PD_FUNCT in utils

* Unclear how functions in the other_globals will work, whether it will mess up the comparison

* Should have a way to track/collect all cached files in a single run