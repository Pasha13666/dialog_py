#!/usr/bin/env python3

import os

from setuptools import setup

with open(os.path.join(os.path.dirname(__file__), 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='dialog_py',
    version='1.0a1',
    description='Python API for cdialog/linux dialog',
    long_description=long_description,
    url='https://github.com/pasha13666/dialog_py',
    author='Pasha__kun',
    author_email='pasha2001dpa@ya.ru',
    packages=['dialog_py'],
    install_requires=[],
    include_package_data=True,
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython'
    ]
)
