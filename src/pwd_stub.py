"""
pwd stub module for Windows compatibility.

This module provides stub implementations of pwd functions that are
required by gunicorn but not available on Windows.
"""

import os


class struct_passwd:
    """Struct passwd for Windows compatibility."""
    def __init__(self, pw_name='', pw_passwd='x', pw_uid=0, pw_gid=0, 
                 pw_gecos='', pw_dir='', pw_shell=''):
        self.pw_name = pw_name
        self.pw_passwd = pw_passwd
        self.pw_uid = pw_uid
        self.pw_gid = pw_gid
        self.pw_gecos = pw_gecos
        self.pw_dir = pw_dir
        self.pw_shell = pw_shell


def getpwuid(uid):
    """Get password database entry by UID."""
    return struct_passwd(
        pw_name=os.environ.get('USERNAME', 'user'),
        pw_uid=uid,
        pw_gid=0,
        pw_dir=os.environ.get('USERPROFILE', 'C:\\Users\\User'),
        pw_shell='cmd.exe'
    )


def getpwnam(name):
    """Get password database entry by name."""
    return struct_passwd(
        pw_name=name,
        pw_uid=os.getuid() if hasattr(os, 'getuid') else 0,
        pw_gid=0,
        pw_dir=os.environ.get('USERPROFILE', 'C:\\Users\\User'),
        pw_shell='cmd.exe'
    )


def getpwall():
    """Return list of all password database entries."""
    return [getpwuid(0)]
