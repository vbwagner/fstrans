#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
"""
Test suite for fstrans module
"""
import unittest
import os
import os.path
import shutil
from fstrans import Transaction

def getfile(filename):
    """
    Helper function - returns content of given file
    """
    with open(filename, "r") as f: #pylint: disable=invalid-name
        return f.read()
def putfile(filename, content):
    """
    Helper function - stores given string into given file
    """
    with open(filename, "w") as f: #pylint: disable=invalid-name

        f.write(content)
class FsTransTestCase(unittest.TestCase):
    """
    Tests for fstrans module
    """
    def setUp(self):
        """
        Test case setup - creates directory to play with
        """
        self.root = "testdata"
        if os.path.isdir(self.root):
            shutil.rmtree(self.root)
        self.cwd = os.getcwd()
        os.mkdir(self.root)
        os.chdir(self.root)
    def tearDown(self):
        """
        Test case teardown - removes playground directory
        """
        os.chdir(self.cwd)
        shutil.rmtree(self.root)
    def test_curdir_commit(self):
        """
        Tests if Transaction changes directory into top of working
        tree and restores on commit
        """
        olddir = os.getcwd()
        os.mkdir("workdir")
        with Transaction("workdir"):
            self.assertEqual(os.getcwd(), os.path.join(olddir, ".workdir"))
        self.assertEqual(os.getcwd(), olddir)
        self.assertEqual(os.listdir("."), ["workdir"])
    def test_curdir_rollback(self):
        """
        Tests if Transaction changes directory into top of working
        tree and restores on rollback
        """
        olddir = os.getcwd()
        os.mkdir("workdir")
        try:
            with Transaction("workdir"):
                self.assertEqual(os.getcwd(), os.path.join(olddir, ".workdir"))
                raise RuntimeError("Aborting Transaction")
        except RuntimeError:
            pass
        self.assertEqual(os.getcwd(), olddir)
        self.assertEqual(os.listdir("."), ["workdir"])
    def test_commit(self):
        """"
        Create test directory, create file in it
        Start transaction, modify file using open

        Commit. See file changed
        See no temporary files left
        """
        os.mkdir("workdir")
        putfile("workdir/testfile.txt", "This is test file content\n")
        with Transaction("workdir") as txn:
            #pylint: disable=invalid-name
            with txn.open("testfile.txt", "w") as f:
                f.write("This is changed content\n")
        # Transaction is commited
        self.assertEqual(getfile("workdir/testfile.txt"),
                         "This is changed content\n")
        self.assertEqual(os.listdir("."), ["workdir"])
    def test_commit_rplus(self):
        """"
        Create test directory, create file in it
        Start transaction, modify file using open

        Commit. See file changed
        See no temporary files left
        """
        os.mkdir("workdir")
        putfile("workdir/testfile.txt", "This is test file content\n")
        with Transaction("workdir") as txn:
            #pylint: disable=invalid-name
            with txn.open("testfile.txt", "r+") as f:
                f.seek(0, 0)
                f.write("That")
        # Transaction is commited
        self.assertEqual(getfile("workdir/testfile.txt"),
                         "That is test file content\n")
        self.assertEqual(os.listdir("."), ["workdir"])
    def test_commit_a(self):
        """"
        create test directory, create file in it
        start transaction, modify file using open

        commit. see file changed
        see no temporary files left
        """
        os.mkdir("workdir")
        putfile("workdir/testfile.txt", "This is test file content\n")
        with Transaction("workdir") as txn:
            # pylint: disable=invalid-name
            with txn.open("testfile.txt", "a") as f:
                f.write("This is changed content\n")
        # transaction is commited
        self.assertEqual(getfile("workdir/testfile.txt"),
                         "This is test file content\nThis is changed content\n")
        self.assertEqual(os.listdir("."), ["workdir"])
    def test_rollback(self):
        """
        Create test directory, create file in it
        Start transaction, modify file using open

        Rollback, see file unchanged
        See no temporary files left
        """
        os.mkdir("workdir")
        putfile("workdir/testfile.txt", "This is test file content\n")
        try:
            with Transaction("workdir") as txn:
                # pylint: disable=invalid-name
                with txn.open("testfile.txt", "w") as f:
                    self.assertEqual(os.stat(f.fileno()).st_nlink, 1)
                    f.write("This is changed content\n")
                raise RuntimeError("Rollback transaction")
        except RuntimeError:
            pass
        # Transaction is rolled back
        self.assertEqual(getfile("workdir/testfile.txt"),
                         "This is test file content\n")
        self.assertEqual(os.listdir("."), ["workdir"])
    def test_rollback_rplus(self):
        """
        Create test directory, create file in it
        Start transaction, modify file using open

        Rollback, see file unchanged
        See no temporary files left
        """
        os.mkdir("workdir")
        putfile("workdir/testfile.txt", "This is test file content\n")
        try:
            with Transaction("workdir") as txn:
                with txn.open("testfile.txt", "r+") as workfile:
                    workfile.seek(0, 0)
                    workfile.write("That")
                raise RuntimeError("Rollback transaction")
        except RuntimeError:
            pass
        # Transaction is rolled back
        self.assertEqual(getfile("workdir/testfile.txt"),
                         "This is test file content\n")
        self.assertEqual(os.listdir("."), ["workdir"])
    def test_rollback_a(self):
        """
        Create test directory, create file in it
        Start transaction, modify file using open

        Rollback, see file unchanged
        See no temporary files left
        """
        os.mkdir("workdir")
        putfile("workdir/testfile.txt", "This is test file content\n")
        try:
            with Transaction("workdir") as txn:
                with txn.open("testfile.txt", "a") as workfile:
                    workfile.write("This is changed content\n")
                raise RuntimeError("Rollback transaction")
        except RuntimeError:
            pass
        # Transaction is rolled back
        self.assertEqual(getfile("workdir/testfile.txt"),
                         "This is test file content\n")
        self.assertEqual(os.listdir("."), ["workdir"])
    def test_commit_putfile(self):
        """
        Create test directory, create file in it
        Start transaction, modify file using putfile

        Commit. See file changed
        See no temporary files left
        """
        os.mkdir("workdir")
        putfile("workdir/testfile.txt", "This is test file content\n")
        putfile("newfile.txt", "This is updated file content\n")
        fullpath = os.path.realpath("newfile.txt")
        with Transaction("workdir") as txn:
            txn.putfile("testfile.txt", fullpath)
        # transaction commited
        self.assertEqual(getfile("workdir/testfile.txt"),
                         "This is updated file content\n")
        self.assertEqual(sorted(os.listdir(".")), ["newfile.txt", "workdir"])
    def test_rollback_putfile(self):
        """
        Create test directory, create file in it
        Start transaction, modify file using putfile

        Rollback, see file unchanged
        See no temporary files left
        """
        os.mkdir("workdir")
        putfile("workdir/testfile.txt", "This is test file content\n")
        putfile("newfile.txt", "This is updated file content\n")
        fullpath = os.path.realpath("newfile.txt")
        try:
            with Transaction("workdir") as txn:
                txn.putfile("testfile.txt", fullpath)
                raise RuntimeError("Aborting transaction")
        except RuntimeError:
            pass
        self.assertEqual(getfile("workdir/testfile.txt"),
                         "This is test file content\n")
        self.assertEqual(sorted(os.listdir(".")), ["newfile.txt", "workdir"])
    def test_commit_unlink(self):
        """
        Create test directory, create two files in it
        Start transaction, remove one file

        Commit, See only one file left
        See no temporary files left
        """
        os.mkdir("workdir")
        putfile("workdir/testfile.txt", "This is test file content\n")
        putfile("workdir/testfile2.txt",
                "This is second testfile content\n")
        putfile("testfile2.txt", "This is file outside transaction tree\n")
        with Transaction("workdir"):
            os.unlink("testfile2.txt")
        # commit transaction
        self.assertEqual(sorted(os.listdir("workdir")), ["testfile.txt"])
        self.assertEqual(sorted(os.listdir(".")), ["testfile2.txt", "workdir"])
    def test_rollback_unlink(self):
        """
        Create test directory, create two files in it
        Start transaction, remove one file

        Commit, See only one file left
        See no temporary files left
        """
        os.mkdir("workdir")
        putfile("workdir/testfile.txt", "This is test file content\n")
        putfile("workdir/testfile2.txt",
                "This is second testfile content\n")
        putfile("testfile2.txt", "This is file outside transaction tree\n")
        try:
            with Transaction("workdir"):
                os.unlink("testfile2.txt")
                raise RuntimeError("Abort transaction")
        except RuntimeError:
            pass
        self.assertEqual(sorted(os.listdir("workdir")),
                         ["testfile.txt", "testfile2.txt"])
        self.assertEqual(sorted(os.listdir(".")), ["testfile2.txt", "workdir"])

    def test_commit_clone(self):
        """"
        Create test directory, create file in it
        Start transaction, clone file and modify in-place

        Commit. See file changed
        See no temporary files left
        """
        os.mkdir("workdir")
        putfile("workdir/testfile.txt", "This is test file content\n")
        putfile("testfile.txt", "This is file outside transaction\n")
        with Transaction("workdir") as txn:
            txn.clonefile("testfile.txt")
            with open("testfile.txt", "r+") as workfile:
                workfile.seek(0, 0)
                workfile.write("That")

        # Transaction is commited
        self.assertEqual(getfile("workdir/testfile.txt"),
                         "That is test file content\n")
        self.assertEqual(getfile("testfile.txt"),
                         "This is file outside transaction\n")
        self.assertEqual(sorted(os.listdir(".")), ["testfile.txt", "workdir"])
        self.assertEqual(sorted(os.listdir("workdir")), ["testfile.txt"])
    def test_rollback_clone(self):
        """"
        Create test directory, create file in it
        Start transaction, clone file and modify in-place

        Rollback. See file unchanged
        See no temporary files left
        """
        os.mkdir("workdir")
        putfile("workdir/testfile.txt", "This is test file content\n")
        putfile("testfile.txt", "This is file outside transaction\n")
        try:
            with Transaction("workdir") as txn:
                txn.clonefile("testfile.txt")
                with open("testfile.txt", "r+") as workfile:
                    workfile.seek(0, 0)
                    workfile.write("That")
                raise RuntimeError("Abort transaction")
        except RuntimeError:
            pass
        self.assertEqual(getfile("workdir/testfile.txt"),
                         "This is test file content\n")
        self.assertEqual(getfile("testfile.txt"),
                         "This is file outside transaction\n")
        self.assertEqual(sorted(os.listdir(".")), ["testfile.txt", "workdir"])
        self.assertEqual(sorted(os.listdir("workdir")), ["testfile.txt"])
    def test_clonetree(self):
        """
        Create some directory hierarchy start transaction and
        clone it.

        See if all files in the cloned tree has one link
        """
        os.mkdir("workdir")
        os.mkdir("workdir/subdir")
        putfile("workdir/subdir/file1", "file1 content\n")
        putfile("workdir/subdir/file2", "file2 content\n")
        with Transaction("workdir") as txn:
            self.assertEqual(os.stat("subdir/file1").st_nlink, 2)
            self.assertEqual(os.stat("subdir/file1").st_nlink, 2)
            txn.clonetree('subdir')
            self.assertEqual(os.stat("subdir/file1").st_nlink, 1)
            self.assertEqual(os.stat("subdir/file1").st_nlink, 1)
    def test_root(self):
        """
        Test if root property outside  transaction context points to
        commited tree and instide into temporary tree

        Check if entering transaction context changed directory
        into root of temporary tree and leaving restores it
        """
        os.mkdir("workdir")
        parent = os.getcwd()
        txn = Transaction("workdir")
        self.assertEqual(txn.root, os.path.join(parent, "workdir"))
        with txn:
            self.assertEqual(txn.root, os.path.join(parent, ".workdir"))
            self.assertEqual(txn.root, os.getcwd())
        self.assertEqual(txn.root, os.path.join(parent, "workdir"))
        self.assertEqual(os.getcwd(), parent)
    def test_checkopened(self):
        """
        Test internal method check_opened which raises a runtime
        error when called in untexpeded state
        """
        os.mkdir("workdir")
        txn = Transaction("workdir")
        with self.assertRaises(RuntimeError):
            txn.check_opened()
        # No exception should be raised
        txn.check_opened(False)
        with txn:
            txn.check_opened()
            with self.assertRaises(RuntimeError):
                txn.check_opened(False)
    def test_checkinside(self):
        """
        Test check_inside method, which checks whether path is inside
        a transaction, and raises ValueError if not.
        """
        os.mkdir("workdir")
        os.mkdir("workdir/subdir")
        os.mkdir("outsidedir")
        txn = Transaction("workdir")
        parent = os.getcwd()
        outsider = os.path.realpath("outsidedir")
        with self.assertRaises(ValueError):
            txn.check_inside(parent)
        with self.assertRaises(ValueError):
            txn.check_inside(".")
        self.assertEqual(txn.check_inside(os.path.realpath("workdir")),
                         os.path.join(parent, "workdir"))
        self.assertEqual(txn.check_inside("workdir"),
                         os.path.join(parent, "workdir"))
        self.assertEqual(txn.check_inside("workdir/subdir"),
                         os.path.join(parent, "workdir", "subdir"))
        with txn:
            with self.assertRaises(ValueError):
                txn.check_inside(parent)
            self.assertEqual(txn.check_inside("."), txn.root)
            self.assertEqual(txn.check_inside("subdir"),
                             os.path.join(txn.root, "subdir"))
            with self.assertRaises(ValueError):
                txn.check_inside(outsider)
            with self.assertRaises(ValueError):
                txn.check_inside(os.path.join(parent, "workdir"))

if __name__ == '__main__':
    unittest.main()
