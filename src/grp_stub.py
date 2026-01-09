"""
grp stub module for Windows compatibility.

This module provides stub implementations of grp functions that are
required by gunicorn but not available on Windows.
"""


class struct_group:
    """Struct group for Windows compatibility."""
    def __init__(self, gr_name='', gr_passwd='x', gr_gid=0, gr_mem=None):
        self.gr_name = gr_name
        self.gr_passwd = gr_passwd
        self.gr_gid = gr_gid
        self.gr_mem = gr_mem or []


def getgrgid(gid):
    """Get group database entry by GID."""
    return struct_group(gr_name='Users', gr_gid=gid)


def getgrnam(name):
    """Get group database entry by name."""
    return struct_group(gr_name=name, gr_gid=0)


def getgrall():
    """Return list of all group database entries."""
    return [getgrgid(0)]
