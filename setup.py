from setuptools import setup, find_packages

version_parts = (0, 2, 0)
version = '.'.join(map(str, version_parts))

setup(
    name='tubbs',
    description='ebnf-based text objects',
    version=version,
    author='Torsten Schmits',
    author_email='torstenschmits@gmail.com',
    license='MIT',
    url='https://github.com/tek/tubbs',
    include_package_data=True,
    packages=find_packages(
        exclude=['unit', 'unit.*', 'integration', 'integration.*']),
    install_requires=[
        'ribosome>=10.0.3',
        'hues',
        'grako',
        'regex',
    ],
    tests_require=[
        'kallikrein',
    ],
)
