from setuptools import setup, find_packages

version_parts = (0, 1, 0)
version = '.'.join(map(str, version_parts))

setup(
    name='tubbs',
    description='ebnf-based text objects',
    version=version,
    author='Torsten Schmits',
    author_email='torstenschmits@gmail.com',
    license='MIT',
    url='https://github.com/tek/tubbs',
    packages=find_packages(
        exclude=['unit', 'unit.*', 'integration', 'integration.*']),
    install_requires=[
        'ribosome',
        'hues',
    ],
    tests_require=[
        'kallikrein',
    ],
)
