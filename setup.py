#! /usr/bin/env python

from setuptools import setup, find_packages


PACKAGENAME = 'thinserve'
INSTALL_REQUIRES = [
    #'preconditions >= 0.1',
    #'twisted >= 14.0',
    #'mock >= 1.0.1',
    ]


setup(
    name=PACKAGENAME,
    description='A thin server library for RESTful api protocol with a static js+html client.',
    url='https://github.com/nejucomo/{0}'.format(PACKAGENAME),
    license='GPLv3',
    version='0.1.dev0',
    author='Nathan Wilcox',
    author_email='nejucomo@gmail.com',

    packages=find_packages(),
    install_requires=INSTALL_REQUIRES,
    package_data = {
        PACKAGENAME: [
            'web/static/*',
        ]
    },
)
