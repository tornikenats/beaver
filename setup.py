#!/usr/bin/env python

from distutils.core import setup

setup(
    name='beaver',
    description='A module that will allow you to scrape transaction history from Canadian banks',
    version='0.1',
    author='Tornike Natsvlishvili',
    author_email='tornikenatsvlishvilideveloper@gmail.com',
    url='https://github.com/TornikeNatsvlishvili/beaver',
    license='MIT',
    packages=['beaver'],
    install_requires=['requests', 'selenium', 'chromedriver', 'lxml', 'python-dateutil'],
)
