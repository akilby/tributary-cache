from setuptools import find_packages, setup

setup(name='tributaries',
      version='0.2',
      description='Complex file-based memoization, '
      'with function code and dependency function code awareness',
      url='http://github.com/akilby/tributary-cache',
      author='Angela E. Kilby',
      author_email='a.kilby@northeastern.edu',
      license='MIT',
      packages=find_packages('src'),
      include_package_data=True,
      package_dir={'': 'src'},
      install_requires=['stdlib_list', 'dill', 'undecorated', 'pandas'],
      zip_safe=False,
      entry_points={
        'console_scripts': [
            'cache = cache.__main__:main',
        ],
      }
      )
