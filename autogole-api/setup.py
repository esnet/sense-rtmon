#!/usr/bin/env python3
"""
Setup tools script for SENSE RT Mon.
Authors:
  Justas Balcas jbalcas (at) es.net

Date: 2024/05/15
"""
import os
import sys
from setuptools import setup

VERSION = '0.0.1'


def get_path_to_root(appendLocation=None):
    """Work out the path to the root from where the script is being run.
    Allows for calling setup.py env from sub directories and directories
    outside the main dir
    """
    fullPath = os.path.dirname(os.path.abspath(os.path.join(os.getcwd(), sys.argv[0])))
    if appendLocation:
        return f"{fullPath}/{appendLocation}"
    return fullPath


def list_packages(packageDirs=None, recurse=True, ignoreThese=None, pyFiles=False):
    """Take a list of directories and return a list of all packages under those
    directories, Skipping 'CVS', '.svn', 'svn', '.git', '', 'sitermagent.egg-
    info' files."""
    if not packageDirs:
        packageDirs = []
    if not ignoreThese:
        ignoreThese = set(['CVS', '.svn', 'svn', '.git', '', 'sitermagent.egg-info'])
    else:
        ignoreThese = set(ignoreThese)
    packages = []
    modules = []
    # Skip the following files
    for aDir in packageDirs:
        if recurse:
            # Recurse the sub-directories
            for dirpath, dummyDirnames, dummyFilenames in os.walk(aDir, topdown=True):
                pathelements = dirpath.split('/')
                # If any part of pathelements is in the ignore_these set skip the path
                if not list(set(pathelements) & ignoreThese):
                    relPath = os.path.relpath(dirpath, get_path_to_root())
                    relPath = relPath.split('/')[2:]
                    if not pyFiles:
                        packages.append('.'.join(relPath))
                    else:
                        for fileName in dummyFilenames:
                            if fileName.startswith('__init__.') or \
                               fileName.endswith('.pyc') or \
                               not fileName.endswith('.py'):
                                continue
                            relName = fileName.rsplit('.', 1)
                            modules.append(f"{'.'.join(relPath)}.{relName[0]}")
                else:
                    continue
        else:
            relPath = os.path.relpath(aDir, get_path_to_root())
            relPath = relPath.split('/')[2:]
            packages.append('.'.join(relPath))
    if pyFiles:
        return modules
    return packages


def get_py_modules(modulesDirs):
    """Get py modules for setup.py."""
    return list_packages(modulesDirs, pyFiles=True)


setup(
    name='RTMon',
    version=f"{VERSION}",
    long_description="RTMon installation",
    author="Justas Balcas",
    author_email="jbalcas@es.net",
    url="https://www.es.net/network-r-and-d/sense/",
    download_url=f"https://github.com/esnet/sense-rtmon/archive/refs/tags/{VERSION}.tar.gz",
    keywords=['RTMon', 'system', 'monitor', 'SDN', 'end-to-end'],
    package_dir={'': 'src/python/'},
    packages=['RTMonLibs', 'RTMon'] + list_packages(['src/python/RTMonLibs/', 'src/python/RTMon/']),
    install_requires=[],
    data_files=[],
    py_modules=get_py_modules(['src/python/RTMonLibs']),
    scripts=["packaging/RTMon-Daemon"]
)

