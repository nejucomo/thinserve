#! /usr/bin/env python

from setuptools import setup, find_packages


PACKAGENAME = 'thinserve'


setup(
    name=PACKAGENAME,
    description="""
        A twisted thin server framework for JSON API + static html clients.
    """.strip(),
    url='https://github.com/nejucomo/{0}'.format(PACKAGENAME),
    license='GPLv3',
    version='0.1.dev1',
    author='Nathan Wilcox',
    author_email='nejucomo@gmail.com',

    packages=find_packages(),
    install_requires=[
        'functable == 0.2.dev1',
        'mock == 1.0.1',
        'twisted == 22.10.0',
    ],
    package_data={
        PACKAGENAME: [
            'web/static/*',
        ]
    },
)
