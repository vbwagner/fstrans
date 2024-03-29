# fstrans - Python  module for filesystem transactions

Description
-----------

This module allows to manipulate some directory tree in safe way,
making sure that in case of error tree would left intact, and 
no other process such as webserver would access partially modified tree
(although you can use external programs from your script to work with
tree)

It also serializes write tree access - if one program  starts transaction
with some directory, other one, if started, would wait for some time for it to
complete. This locking is cooperative. Two programs should agree on
what subdirectory should be modified transactionally.

Transaction commit is almost atomic. Anybody sees original tree
until commit, and commit itself requires just two rename operations.
Rollback is atomic to. In both cases that version of tree which should
be discarded, is first renamed to unique temporary name and then
deleted.

Module is Unix-only. It heavily relies on hard links to quickly make
copies of big trees and to save space when making minor modifications
on big trees.

As working tree is populated with hard links from final tree, user
should make sure that file is different in local copy before modifying
it. I.e. unlink it before writing. 

For this module provides following methods:

1. **open** - works just like builtin function **open**, but makes sure
that original file would not be clobbered before commit.
2. **putfile** - safely replaces file in tree with other file
3. **clonefile**, **clonetree** - make exact copy of original file or
    subdirectory  with link count = 1. This is primarily intended for
	running external programs which modify files in place. 

Installation
------------

You can install released version with `pip3 install fstrans`.
If you prefer cutting age software, recommended way is

```
python3 setup.py sdist
pip3 install ./dist/fstrans-1.0.tar.gz
```

Of course, you can install system-wide build your OS packages and so on.
But if you are planning to do so, you probably don't need special
instructions.

Testing
-------

There is unittest-based test suite in the test directory.


Run

```
python3 setup.py test
```

to run test suite.

