#!/usr/bin/env python
from setuptools import setup, find_packages


setup(
    name='stenographer',
    description='An HTTP interaction recorder for Twisted Web',
    version='0.1.3',
    author='Kevin Xiwei Zheng',
    author_email='kxz+stenographer@room208.org',
    url='https://github.com/kxz/stenographer',
    license='X11',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Framework :: Twisted',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 2 :: Only',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Testing'],
    packages=find_packages(),
    package_data={
        'stenographer': [
            'test/fixtures/cassettes/*']},
    install_requires=[
        'Twisted>=14.0.0'])
