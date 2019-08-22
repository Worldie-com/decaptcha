#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open("README.rst") as readme_file:
    readme = readme_file.read()

with open("CHANGELOG") as changelog_file:
    changelog = changelog_file.read()

with open("requirements.in") as reqts_file:
    reqs = reqts_file.read()
requirements = [_ for _ in reqs.split("\n") if len(_) > 0]

setup_requirements = ["pytest-runner"]

test_requirements = ["pytest"]

setup(
    author="John Harrison",
    author_email="balanceofprobability@gmail.com",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    description="A GUI automation Python module for solving Google reCAPTCHA v2",
    install_requires=requirements,
    license="MIT license",
    # long_description=readme + '\n\n' + changelog,
    long_description=readme,
    include_package_data=True,
    keywords="decaptcha",
    name="decaptcha",
    packages=find_packages(include=["decaptcha"]),
    setup_requires=setup_requirements,
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/balanceofprobability/decaptcha",
    version="0.1.2",
    zip_safe=False,
)
