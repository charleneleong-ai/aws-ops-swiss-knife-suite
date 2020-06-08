#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Created Date: Monday, June 8th 2020, 12:53:50 pm
# Author: Charlene Leong charleneleong84@gmail.com
# Last Modified: Monday, June 8th 2020, 1:18:13 pm
###


""" Setup for Ops Swiss Knife Suite

The setup script defines the modules required to build this app
"""

import setuptools

with open("README.md") as fp:
    long_description = fp.read()

requirements = [
    "pandas",
    "openpyxl",
    "boto3",
    "argparse",
    "awsume"
]

dev_requirements = [
    "autopep8",
    "pylint",
    "pytest",
    "pytest-dotenv",
    "pytest-cov"
]

setuptools.setup(
    name="ops-swiss-knife-suite",
    version="0.0.1",

    description="Suite of tools for easier management customer accounts",
    long_description=long_description,
    long_description_content_type="text/markdown",

    author="Charlene Leong",

    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),

    install_requires=requirements,
    extras_require={"dev": dev_requirements},

    python_requires=">=3.7.5",

    classifiers=[
        "Development Status :: Development",

        "Intended Audience :: Public",

        "Programming Language :: Python :: 3.7.5",

        "Topic :: Utilities",

        "Typing :: Typed",
    ],
)

