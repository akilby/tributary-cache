import functools
import os
import tempfile


class Memorizer(object):

    def __init__(self,
                 directory=None,
                 verbose=0):

        """
        Users should be able to declare, or use default temp directory
        Or, there can be a module-based config file like NPI, like already
        exists, and can retrieve config file once the module name is known
        can bypass caching using bare_func
        """

        if not directory:
            directory = os.path.join(tempfile.gettempdir(), '_cache')

        self.directory = directory
        self.exclusion_list = []
        self.noisily = False if verbose == 0 else True

        if not os.path.isdir(self.directory):
            os.mkdir(self.directory)

    def cache(self, function):

        # TO DO: This is a workaround; should move to using only
        # an attribute on the wrapper
        function.is_cacher_registered = True

        @functools.wraps(function)
        def wrapper(*args, **kwargs):

            module_to_import = function.__module__

            from cache import cache
            c = cache.Cache(configure={'directory': self.directory,
                                       'registry': [module_to_import],
                                       'exclusion_list': self.exclusion_list},
                            noisily=self.noisily)

            return getattr(c, function.__code__.co_name)(*args, **kwargs)

        wrapper.is_cacher_registered = True
        wrapper.bare_func = function

        return wrapper
