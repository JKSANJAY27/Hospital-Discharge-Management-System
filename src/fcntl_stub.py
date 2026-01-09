"""
fcntl stub module for Windows compatibility.

This module provides stub implementations of fcntl functions that are
required by gunicorn but not available on Windows. This allows Agent Lightning
to import and run on Windows with some limitations.

Note: File locking operations will be no-ops on Windows when using this stub.
For production deployments, use Linux/WSL.
"""

import os
import sys

# Windows-specific constants (matching Unix values for compatibility)
LOCK_SH = 1  # Shared lock
LOCK_EX = 2  # Exclusive lock
LOCK_NB = 4  # Non-blocking
LOCK_UN = 8  # Unlock

F_DUPFD = 0
F_GETFD = 1
F_SETFD = 2
F_GETFL = 3
F_SETFL = 4
F_GETLK = 5
F_SETLK = 6
F_SETLKW = 7

FD_CLOEXEC = 1


def fcntl(fd, cmd, arg=0):
    """
    Stub fcntl implementation for Windows.
    
    On Windows, this is a no-op that returns 0 for most operations.
    """
    if cmd == F_GETFD:
        return 0
    elif cmd == F_SETFD:
        return 0
    elif cmd == F_GETFL:
        return 0
    elif cmd == F_SETFL:
        return 0
    return 0


def flock(fd, operation):
    """
    Stub flock implementation for Windows.
    
    Uses Windows file locking via msvcrt if available, otherwise no-op.
    """
    try:
        import msvcrt
        
        # Get file handle
        if hasattr(fd, 'fileno'):
            fd = fd.fileno()
        
        # Determine lock type
        if operation & LOCK_UN:
            # Unlock
            try:
                msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
            except (OSError, IOError):
                pass  # Ignore unlock errors
        elif operation & LOCK_EX:
            # Exclusive lock
            try:
                if operation & LOCK_NB:
                    msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
                else:
                    msvcrt.locking(fd, msvcrt.LK_LOCK, 1)
            except (OSError, IOError):
                pass  # Ignore lock errors on Windows
        elif operation & LOCK_SH:
            # Shared lock (Windows doesn't distinguish, use exclusive)
            try:
                if operation & LOCK_NB:
                    msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
                else:
                    msvcrt.locking(fd, msvcrt.LK_LOCK, 1)
            except (OSError, IOError):
                pass
    except ImportError:
        pass  # msvcrt not available, skip locking


def lockf(fd, cmd, length=0, start=0, whence=0):
    """
    Stub lockf implementation for Windows.
    """
    return flock(fd, cmd)


def ioctl(fd, request, arg=0, mutate_flag=True):
    """
    Stub ioctl implementation for Windows.
    
    Most ioctl operations are not applicable on Windows.
    """
    return 0


# Register this module as 'fcntl' in sys.modules if on Windows
if sys.platform == 'win32':
    sys.modules['fcntl'] = sys.modules[__name__]
