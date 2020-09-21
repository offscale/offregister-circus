# -*- coding: utf-8 -*-

from ast import parse
from functools import partial
from os import path, listdir
from platform import python_version_tuple

from distutils.sysconfig import get_python_lib
from setuptools import setup, find_packages
from sys import version

if version[0] == "2":
    from itertools import imap as map, ifilter as filter
if python_version_tuple()[0] == "3":
    imap = map
    ifilter = filter
else:
    from itertools import imap, ifilter

if __name__ == "__main__":
    package_name = "offregister_circus"

    with open(path.join(package_name, "__init__.py")) as f:
        __author__, __version__ = imap(
            lambda buf: next(imap(lambda e: e.value.s, parse(buf).body)),
            ifilter(
                lambda line: line.startswith("__version__")
                or line.startswith("__author__"),
                f,
            ),
        )

    to_funcs = lambda *paths: (
        partial(path.join, path.dirname(__file__), package_name, *paths),
        partial(path.join, get_python_lib(prefix=""), package_name, *paths),
    )
    _data_join, _data_install_dir = to_funcs("_data")
    config_join, config_install_dir = to_funcs("configs")

    setup(
        name=package_name,
        author=__author__,
        version=__version__,
        description="This package follows the offregister specification to setup and serve circusd",
        classifiers=[
            "Intended Audience :: Developers",
            "Topic :: Software Development",
            "Topic :: Software Development :: Libraries :: Python Modules",
            "License :: OSI Approved :: MIT License",
            "License :: OSI Approved :: Apache Software License",
            "Programming Language :: Python",
        ],
        install_requires=["pyyaml", "fab-classic", "paramiko"],
        test_suite=package_name + ".tests",
        packages=find_packages(),
        package_dir={package_name: package_name},
        data_files=[
            (_data_install_dir(), list(imap(_data_join, listdir(_data_join())))),
            (config_install_dir(), list(imap(config_join, listdir(config_join())))),
        ],
    )
