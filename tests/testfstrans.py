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
    with open(filename, "r") as f:
        return f.read()
def putfile(filename, content):
    """
    Helper function - stores given string into given file
    """
    with open(filename, "w") as f:
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
if __name__ == '__main__':
    unittest.main()
