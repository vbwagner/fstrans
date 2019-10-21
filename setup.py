# -*- encoding: utf-8 -*-
import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='fstrans',
    version='1.0.1',
    author='Victor Wagner',
    author_email='vitus@wagner.pp.ru',
    description='Performs transactional modification on directory trees',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/vbwagner/fstrans',
    packages=setuptools.find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: Unix',
        'Operating System :: POSIX'
    ],
    python_requires='>=3.5',
    test_suite="fstrans.tests.testfstrans",
    include_package_data=True,
)   
