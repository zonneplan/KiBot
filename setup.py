#!/usr/bin/python3
import io
import os
from distutils.core import setup

# Package meta-data.
NAME = 'kiplot'
DESCRIPTION = 'Plotting driver for KiCad'
URL = 'https://github.com/INTI-CMNB/kiplot/'
EMAIL = 'john.j.beard@gmail.com'
AUTHOR = 'John Beard'

here = os.path.abspath(os.path.dirname(__file__))
# Import the README and use it as the long-description.
# Note: this will only work if 'README.md' is present in your MANIFEST.in file!
with io.open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = '\n' + f.read()
about = {}
with open(os.path.join(here, NAME, '__version__.py')) as f:
    exec(f.read(), about)

setup(name=NAME,
      version=about['__version__'],
      description=DESCRIPTION,
      long_description=long_description,
      # long_description_content_type='text/markdown',
      author=AUTHOR,
      author_email=EMAIL,
      url=URL,
      packages=[NAME],
      package_dir={NAME: NAME},
      scripts=['src/kiplot'],
      # install_requires=['pyyaml'],
      classifiers=['Development Status :: 3 - Alpha',
                   'Environment :: Console',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
                   'Natural Language :: English',
                   'Operating System :: POSIX :: Linux',
                   'Programming Language :: Python :: 3',
                   'Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)',
                   ],
      platforms='POSIX',
      license='GPL-3.0',
      )
