#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  setup.py
#
#  Copyright 2020 Bruce Schubert <bruce@emxsys.com>
#  Copyright 2022-2025 Ted Hess <thess@kitschensync.net>

import setuptools

# load the long_description from the README
with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="callattendant",   # Product name on PyPi (Callattendant2)
    version="2.3.0",        # Ensure this is in-sync with VERSION in config.py
    author="Ted Hess",
    author_email="thess@kitschensync.net",
    description="An automated call attendant and call blocker using a USR5637 or CX930xx modem",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://thess.github.io/callattendant/",
    packages=setuptools.find_packages(exclude=["tests"]),
    include_package_data=True,      # Includes files from MANIFEST.in
    install_requires=[
        "Flask>=3.0.1",
        "waitress>=3.0.2",
        "flask-paginate>=2023.10.24",
        "beautifulsoup4>=4.12.3",
        "requests>=2.32.4",
        "lxml>=5.3.0",
        "bs4>=0.0.2",
        "soupsieve>=2.5",
        "Werkzeug>=3.0.1",
        "Jinja2>=3.1.3",
        "itsdangerous>=2.1.2",
        "MarkupSafe>=2.1.4",
        "PyYAML>=6.0.1",
        "blinker>=1.7.0",
        "click>=8.1.7",
        "pygments>=2.17.2",
        "pyserial>=3.5",
    ],
    entry_points={
        "console_scripts": [
            "callattendant = callattendant.__main__:main",
        ]
    },
    scripts=[
        "bin/start-callattendant",
        "bin/stop-callattendant",
        "bin/restart-callattendant",
        "bin/monitor-callattendant",
    ],
    data_files=[
        ('share/applications', [
            'bin/configure-callattendant.desktop',
            'bin/monitor-callattendant.desktop',
            'bin/restart-callattendant.desktop',
            'bin/stop-callattendant.desktop',
        ]),
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Environment :: Other Environment",
        "Development Status :: 5 - Production/Stable",
        "Framework :: Flask",
        "Topic :: Communications :: Telephony",
        "Topic :: Home Automation",
    ],
    python_requires='>=3.5',

)
