import functools
import os
import tempfile
import warnings

from .config import get_config_package


class Cacher(object):

    def __init__(self,
                 configure_disk=None,
                 directory=None,
                 exclusion_list=[],
                 verbose=0):

        """
        Users should be able to declare, or use default temp directory
        Or, there can be a module-based config file like NPI, like already
        exists, and can retrieve config file once the module name is known
        can bypass caching using bare_func
        """

        if configure_disk:
            directory, noisily, rerun = get_config_package(configure_disk)

        if not directory:
            directory = os.path.join(tempfile.gettempdir(), '_cache')
            warnings.warn(
                'You are saving caches to your tmp directory, %s. '
                'This may fill quickly. Set directory at the package level, '
                'or at each instantiation of the Cacher class' % directory)

        self.directory = directory
        self.exclusion_list = exclusion_list
        self.noisily = False if verbose == 0 else True

        if not os.path.isdir(self.directory):
            os.mkdir(self.directory)

    def register(self, function):

        # TO DO: This is a workaround; should move to using only
        # an attribute on the wrapper
        function.is_cacher_registered = True

        @functools.wraps(function)
        def wrapper(*args, **kwargs):

            module_to_import = function.__module__

            from . import cache
            c = cache.Cache(configure={'directory': self.directory,
                                       'registry': [module_to_import],
                                       'exclusion_list': self.exclusion_list},
                            noisily=self.noisily,
                            old_version=False)

            return getattr(c, function.__code__.co_name)(*args, **kwargs)

        wrapper.is_cacher_registered = True
        wrapper.bare_func = function
        wrapper.current_cacher_directory = self.directory

        return wrapper
