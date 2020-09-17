from setuptools import find_packages, setup

setup(name='cache',
      version='0.1',
      description='Complex memoization to file',
      url='http://github.com/akilby/cache',
      author='Angela E. Kilby',
      author_email='a.kilby@northeastern.edu',
      license='MIT',
      packages=find_packages('cache'),
      install_requires=['stdlib_list', 'dill'],
      zip_safe=False,
      entry_points={
        'console_scripts': [
            'cache = cache.__main__:main',
        ],
      }
      )
