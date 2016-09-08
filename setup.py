import os
from setuptools import setup

path = os.path.abspath(os.path.dirname(__file__))

# Get the long description from the README file
with open(os.path.join(path, 'README.rst'), encoding='utf-8') as f:
  long_description = f.read()

# Get requirements from file
with open(os.path.join(path, 'requirements.txt')) as f:
  requirements = f.read().splitlines()

setup(name='clear',
      version='1.0.0',
      description='CLEAR: Command-line extract and rename utility',
      long_description=long_description,
      url='http://github.com/davgeo/clear',
      author='David George',
      author_email='dcg.git@gmail.com',
      license='MIT',
      packages=["clear"],
      install_requires=requirements)
