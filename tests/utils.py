import contextlib
import logging
import os
import shutil
import tempfile

import decorator


class MockParser:
    """
    Small class that contains the necessary functions in order to test custom
    validation functions used with the argparse module
    """

    def __init__(self):
        self.error_msg = None

    def error(self, value=None):
        self.error_msg = value

    def get_error(self):
        return self.error_msg


def relpath(*path):
    """Make a path relative to the project root folder"""
    project_root_folder = os.path.dirname(os.path.dirname(__file__))
    return os.path.join(project_root_folder, *path)


def tmpdir(path, teardown=True):
    """Decorator based on the  `tmp` context"""

    def real_decorator(function):
        def wrapper(function, *args, **kwargs):
            with tmp(path, teardown=teardown):
                return function(*args, **kwargs)

        return decorator.decorator(wrapper, function)

    return real_decorator


@contextlib.contextmanager
def tmp(path=None, teardown=True):
    """Create and go into tmp directory, returns the path.

    This function creates a temporary directory and enters that directory.  The
    returned object is the path to the created directory.

    If @path is not specified, we create an empty directory, otherwise, it must
    be a path to an existing directory.  In that case, the directory will be
    copied into the temporary directory.

    If @teardown is True (defaults to True), the directory is (attempted)
    deleted after context, otherwise it is kept as is.

    """
    cwd = os.getcwd()
    fname = tempfile.NamedTemporaryFile().name

    if path:
        if not os.path.isdir(path):
            logging.debug("tmp:raise no such path")
            raise IOError("No such directory: %s" % path)
        shutil.copytree(path, fname)
    else:
        # no path to copy, create empty dir
        os.mkdir(fname)

    os.chdir(fname)

    yield fname  # give control to caller scope

    os.chdir(cwd)

    if teardown:
        try:
            shutil.rmtree(fname)
        except OSError as oserr:
            logging.debug("tmp:rmtree failed %s (%s)" % (fname, oserr))
            shutil.rmtree(fname, ignore_errors=True)