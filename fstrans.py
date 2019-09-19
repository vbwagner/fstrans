# -*- encoding: utf-8 -*-
"""
Filesystem transaction.

This module defines transaction object, which allows make modifications
in the temorary copy of directory tree and then either replace
original tree with new atomically or discard changes, living old version
intact

Transaction object works as context manager and rolls back if exception
is raised inside transaction.

"""
# For Transaction
import os
import select
import time
import sys
from tempfile import mkdtemp
import shutil

TIMEOUT = 30

#
# Atomic directory updates
#
def copy_tree(old, new):
    """
    Creates new directory tree similar to old one by creating
    directories and hardlinking files.
    If top of new tree exists, rises FileExistsError
    """
    os.mkdir(new, 0o755)
    os.chmod(new, os.stat(old).st_mode)
    for (root, _, files) in os.walk(old):
        newdir = new + root[len(old):]
        if newdir != new:
            os.mkdir(newdir, os.stat(root).st_mode)
        for f in files: #pylint: disable=invalid-name
            os.link(os.path.join(root, f), os.path.join(newdir, f))

class Transaction:
    """
    Atomic modification for directory tree.
    Creates working copy and lets modify it.
    Upon finish of modificaion either replaces old one with new
    via semi-atomic pair or renames or discards temporary tree
    if exception was raised.

    If it sees that other process already created copy, waits for
    timeout second periodically retrying. So, two processes cannot
    simulteneously modify same tree, because mkdir is atomic.

    Transaction object has instance variables:

    - opened which is True if transaction currently active.

    When entered transaction, current directory is changed to top
    of working tree.

    Files in the copy of working tree are hard links to origintal,
    so if you want to modify them, you should disconnect them from
    original.

    Transaction provides following methods to do this:

    - open - to open file inside python
    - clone - to make modifiable copy for further in-place modification
    - putfile - to replace with another file content

    It is also safe to os.unlink file before creating new one

    Transaction is commited if control leaves with block without error
    and rolled back if exception occur.
    """
    def __init__(self, path, timeout=30, leave_snapshot=None):
        """
        Initializes transaction object storing path to modify and
        some other properties.

        Arguments

        path - path to modify atomically
        timeout - number of seconds to retry acquiring lock if
               path is hold by other Transaction (in other process)
        leave_snapshot - if not none, strftime format,
               previous copy would be retained in the name with
               date of fishing modification formatted using this format
        """
        if not os.path.isdir(path):
            raise ValueError("Not a directory")
        if leave_snapshot is not None and leave_snapshot.find("/") != -1:
            raise ValueError("Snapshot name couldn't contain slashes")
        self.parent, self.commited = os.path.split(os.path.realpath(path))
        self.workdir = "." + self.commited
        self.timeout = timeout
        self.leave_snapshot = leave_snapshot
        self.opened = False
        self.cwd = None

    def __enter__(self):
        """
        Tries to acquire lock on the directory tree by creating
        tree with name of top directory prepended by dot alongside.

        If this tree exists assumes that directory is locked by another
        copy of same process and retries until TIMEOUT secound passes.
        If it passes, raises TimeoutError. On first attempt to lock writes
        message to stdout if lock unsuccessful

        If successefully starts transaction, returns self.
        """
        tree = os.path.join(self.parent, self.commited)
        msg = "directory %s already locked. Waiting" % tree
        newtree = os.path.join(self.parent, self.workdir)
        finish = time.time() + self.timeout
        self.cwd = os.getcwd()
        while time.time() < finish:
            try:
                copy_tree(tree, newtree)
                os.chdir(newtree)
                print("", file=sys.stderr, flush=True)
                self.opened = True
                return self
            except FileExistsError:
                print(msg, file=sys.stderr, end='', flush=True)
                msg = "."
                # Wait for a while
                select.select([sys.stdin], [], [sys.stdin], 0.5)
        # We get here only if timeout expired
        raise TimeoutError("Cannot lock directory %s" % tree)


    def __exit__(self, exch_type, exch_value, exch_traceback):
        """
        Unlocks tree by removing either old tree (and replacing it by
        temporary working tree) if normal exit from context occurs,
        or temporary tree if exception was raised.
        """
        tempdir = mkdtemp(dir=self.parent)
        os.chdir(self.cwd)
        self.opened = False
        if exch_type is None:
            if self.leave_snapshot is not None:
                os.rename(os.path.join(self.parent, self.commited),
                          os.path.join(self.parent,
                                       time.strftime(self.leave_snapshot)))
            else:
                os.rename(os.path.join(self.parent, self.commited),
                          os.path.join(tempdir, self.commited))
            os.rename(os.path.join(self.parent, self.workdir),
                      os.path.join(self.parent, self.commited))
        else:
            os.rename(os.path.join(self.parent, self.workdir),
                      os.path.join(tempdir, self.commited))
    # Remove temporary directory tree
        for root, dirs, files in os.walk(tempdir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(tempdir)
        # Should return false for exception to be reraised
        return exch_type is None
    def check_opened(self, should=True):
        """ Check for valid transaction state.
        By default, raises exception if transaction is closed
        """
        states = {False:'closed', True:'opened'}
        #check if file is inside temporary tree
        if self.opened != should:
            raise RuntimeError("This Transaction object is not " +
                               "currenly in %s state" % states[should])
    def check_inside(self, name):
        """
        Checks if given filename is inside working tree.
        If not, raises ValueError
        """
        fullname = os.path.realpath(name)
        mydir = self.root
        if fullname != mydir and not fullname.startswith(mydir + "/"):
            raise ValueError("path '%s' should be inside working tree" % name)
        return fullname
    @property
    def root(self):
        """
        Return top of directory tree. If transaction is opened,
        it is temporary working tree to be commited.

        Otherwise it is directory which is passed to constructor
        """
        if self.opened:
            return os.path.join(self.parent, self.workdir)
        return os.path.join(self.parent, self.commited)

    def open(self, name, mode='r', **kwargs):
        """
        Opens file inside transaction tree.
        Makes sure that old file is not corrupted and can
        be rolled back
        """
        self.check_opened()
        fullname = self.check_inside(name)
        if 'w' in mode:
            # unlink file before opening with truncation
            try:
                os.unlink(fullname)
            except FileNotFoundError:
                pass
        elif '+' in mode or 'a' in mode:
            # Need a copy
            inf = open(fullname, "r")
            os.unlink(fullname)
            if "r" in mode:
                # Need to touch file first
                open(fullname, "w").close()
            outf = open(fullname, mode)
            shutil.copyfileobj(inf, outf)
            inf.close()
            if mode.startswith("r+"):
                outf.seek(0, 0)
            return outf
        return open(fullname, mode, **kwargs)
    def putfile(self, dest, source):
        """
        Puts file source which can be either inside or outside working
        tree to file dest, which should be inside working tree
        """
        self.check_opened()
        fullname = self.check_inside(dest)
        try:
            os.unlink(dest)
        except FileNotFoundError:
            pass
        os.makedirs(os.path.dirname(fullname), exist_ok=True)
        shutil.copyfile(source, fullname)
        shutil.copystat(source, fullname)
    def clonefile(self, path):
        """
        Prepares file in temporary transaction directory
        for in-place modification
        """
        self.check_opened()
        fullname = self.check_inside(path)
        if os.stat(fullname).st_nlink == 1:
            # Already cloned
            return
        os.unlink(fullname)
        prefixlen = len(os.path.join(self.parent, self.workdir))
        oldcopy = os.path.join(self.parent, self.commited) + fullname[prefixlen:]
        shutil.copyfile(oldcopy, fullname)
        shutil.copystat(oldcopy, fullname)
    def clonetree(self, path):
        """
        Prepares entire directory in temporary transaction directory
        for in-place modification
        """
        self.check_opened()
        fullname = self.check_inside(path)
        for (root, _, files) in os.walk(fullname):
            for filename in files:
                self.clonefile(os.path.join(root, filename))
