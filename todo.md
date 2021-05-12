## Notes/upgrades ##

If function foo.bar calls blah.bar, name conflicts can maybe be a problem (?) need to test; may only be in old version

Could use functions themselves as the dictionary key in globals_list, to prevent any conflicts in session

And prepend module names in the cacher dictionary