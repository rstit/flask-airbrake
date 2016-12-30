from setuptools import setup
from codecs import open
from os import path

__version__ = '0.0.2'

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# get the dependencies and installs
with open(path.join(here, 'requirements.txt'), encoding='utf-8') as f:
    all_reqs = f.read().split('\n')

dependency_links = [x.strip().replace('git+', '') for x in all_reqs if x.startswith('git+')]

setup(
    name='Flask-Airbrake',
    version=__version__,
    description='Flask extension for Airbrake',
    long_description=long_description,
    url='https://github.com/rstit/flask-airbrake',
    download_url='https://github.com/rstit/flask-airbrake/tarball/' + __version__,
    license='BSD',
    classifiers=[
      'Development Status :: 3 - Alpha',
      'Intended Audience :: Developers',
      'Programming Language :: Python :: 3',
    ],
    keywords='',
    py_modules=['flask_airbrake'],
    install_requires=['Flask', 'airbrake'],
    include_package_data=True,
    author='RST-IT',
    dependency_links=dependency_links,
    author_email='piotr.poteralski@rst-it.com'
)
