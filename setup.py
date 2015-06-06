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
    version='0.1.dev0',
    author='Nathan Wilcox',
    author_email='nejucomo@gmail.com',

    packages=find_packages(),
    install_requires=[],
    package_data={
        PACKAGENAME: [
            'web/static/*',
        ]
    },
)
