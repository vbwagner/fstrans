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
complete.

Module is Unix-only. It heavily relies on hard links to quickly make
copies of big trees.

As working tree is populated with symlinks from final tree, user
should make sure that file is different in local copy before modifying
it.

For this module provides following methods:

1. **open** - works just like builtin function **open**, but makes sure
that original file would not be clobbered before commit.
2. **putfile** - safely replaces file in tree with other file
3. **clonefile**, **clonetree** - make exact copy of original file with
   link count = 1.

Installation
------------

Just drop `fstrans.py` into your `site_python` directory.
No proper setup is written yet

Testing
-------

There is unittest-based test suite in the test directory.

Run

```
python3 -m unittest discover tests
```

to run test suite.

