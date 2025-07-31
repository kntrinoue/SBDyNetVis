from setuptools import setup, find_packages

setup(
    name='PackageTest',
    version='0.5.2',
    description='For distributing a package',
    author='Kentaro Inoue',
    author_email='inoue@cs.miyazaki-u.ac.jp',
    url='https://github.com/inoue170201/packagetest',
    packages=find_packages(),
    python_requires='>=3.6',
    install_requires=[
    'pandas',
    'copasi-basico',
    ] ,
    package_data={
        'SBDyNetVis': ['*.json'],
    }
)