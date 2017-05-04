from setuptools import setup, find_packages

setup(
    name='xbeachtools',
    version='0.0',
    author='Bas Hoonhout',
    author_email='bas.hoonhout@deltares.nl',
    packages=find_packages(),
    description='A toolbox for XBeach modeling',
    long_description=open('README.txt').read(),
    install_requires=[
        'docopt',
        'pyproj',
        'xarray',
        'numpy',
    ],
)
