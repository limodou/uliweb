#####################################################################
# COPY FROM http://www.gnome.org/~jdub/bzr/planet/2.0/planet/htmltmpl.py
# and inspired from http://www.python.org/pypi/zc.lockfile
# LICENSE: BSD
# Modified by: Limodou(limodou@gmail.com)
#####################################################################

__all__ = ['LOCK_EX', 'LOCK_SH', 'LOCK_UN', 'lock_file', 'unlock_file',
    'LockFile', 'LockError']

import os

class LockError(Exception):
    """Couldn't get a lock
    """
    
LOCKTYPE_FCNTL = 1
LOCKTYPE_MSVCRT = 2
LOCKTYPE = None

try:
    import fcntl
except:
    try:
        import msvcrt
    except:
        LOCKTYPE = None
    else:
        LOCKTYPE = LOCKTYPE_MSVCRT
else:
    LOCKTYPE = LOCKTYPE_FCNTL
LOCK_EX = 1
LOCK_SH = 2
LOCK_UN = 3

def lock_file(f, lock=LOCK_SH):
    try:
        fd = f.fileno()
        if LOCKTYPE == LOCKTYPE_FCNTL:
            if lock == LOCK_SH:
                fcntl.flock(fd, fcntl.LOCK_SH)
            elif lock == LOCK_EX:
                fcntl.flock(fd, fcntl.LOCK_EX)
            elif lock == LOCK_UN:
                fcntl.flock(fd, fcntl.LOCK_UN)
            else:
                raise LockError, "BUG: bad lock in lock_file"
        elif LOCKTYPE == LOCKTYPE_MSVCRT:
            if lock == LOCK_SH:
                # msvcrt does not support shared locks :-(
                msvcrt.locking(fd, msvcrt.LK_LOCK, 1)
            elif lock == LOCK_EX:
                msvcrt.locking(fd, msvcrt.LK_LOCK, 1)
            elif lock == LOCK_UN:
                msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
            else:
                raise LockError, "BUG: bad lock in lock_file"
        else:
            raise LockError, "BUG: bad locktype in lock_file"
    except IOError:
        raise LockError("Couldn't lock %r" % f.name)
            
def unlock_file(f):
    lock_file(f, LOCK_UN)
    
class LockFile(object):
    def __init__(self, lockfilename):
        self._f = lockfilename
        self._create_flag = False
        self._checkfile()
        
    def _checkfile(self):
        if os.path.exists(self._f):
            self._fd = open(self._f, 'rb')
        else:
            dir = os.path.dirname(self._f)
            if dir and not os.path.exists(dir):
                os.makedirs(dir)
            self._fd = open(self._f, 'wb')
            self._create_flag = True
        
    def lock(self, lock_flag=LOCK_SH):
        lock_file(self._fd, lock_flag)
        
    def close(self):
        unlock_file(self._fd)
        self._fd.close()
        
    def delete(self):
        self._fd.close()
        os.unlink(self._f)