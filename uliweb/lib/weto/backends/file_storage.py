import os
import time
from base import BaseStorage, KeyError
import weto.lockfile as lockfile

try:
    from hashlib import md5
except ImportError:
    from md5 import md5
    
def _get_key(key):
    if isinstance(key, unicode):
        key = key.encode('ascii', 'backslashreplace')
    
    return md5(key).hexdigest()

def verify_path(path):
    dir = os.path.dirname(path)
    if dir and not os.path.exists(dir):
        os.makedirs(dir)
    
def encoded_path(root, key, extension = ".enc", depth = 2):
    ident = key
    tokens = []
    for d in range(0, depth):
        tokens.append(ident[d])
    
    dir = os.path.join(root, *tokens)
    
    return os.path.join(dir, ident + extension)

class Storage(BaseStorage):
    def __init__(self, cache_manager, options, file_dir_name='session_files', lock_dir_name='session_files_lock'):
        BaseStorage.__init__(self, cache_manager, options)
        self.data_dir = options.get('data_dir', './sessions')
        self.file_dir = options.get('file_dir') or os.path.join(self.data_dir, file_dir_name)
        self.lock_dir = options.get('lock_dir') or os.path.join(self.data_dir, lock_dir_name)
        
    def get(self, _key):
        key = _get_key(_key)
        _file = self._get_file(key)
        if not os.path.exists(_file):
            raise KeyError("Cache key [%s] not found" % _key)
            
        lock = self._get_lock(key)
        try:
            lock.lock()
            ret = self.load(_file)
            if ret:
                stored_time, expiry_time, value = ret
                if self._is_not_expiry(stored_time, expiry_time):
                    return value
            raise KeyError("Cache key [%s] not found" % _key)
        finally:
            lock.close()
    
    def set(self, _key, value, expire):
        key = _get_key(_key)
        now = time.time()
    
        lock = self._get_lock(key)
        try:
            lock.lock(lockfile.LOCK_EX)
            self.save(key, now, expire, value)
            return True
        finally:
            lock.close()

    def delete(self, _key):
        key = _get_key(_key)
        lock = self._get_lock(key)
        flag = False
        try:
            lock.lock(lockfile.LOCK_EX)
            _file = self._get_file(key)
            if os.path.exists(_file):
                os.unlink(_file)
            flag = True
            return flag
        finally:
            lock.close()
            if flag:
                lock.delete()
                
    def inc(self, _key, step=1, expire=None):
        key = _get_key(_key)
        _file = self._get_file(key)
        now = time.time()
        
        value = 0
        
        lock = self._get_lock(key)
        try:
            lock.lock(lockfile.LOCK_EX)
            if os.path.exists(_file):
                ret = self.load(_file)
                if ret:
                    stored_time, expiry_time, value = ret
                    if self._is_not_expiry(stored_time, expiry_time):
                        pass
                    else:
                        value = 0
            v = value + step
            self.save(key, now, expire, v)
            return v
        finally:
            lock.close()
        
    def dec(self, _key, step=1, expire=None):
        key = _get_key(_key)
        _file = self._get_file(key)
        now = time.time()
        
        value = 0
        
        lock = self._get_lock(key)
        try:
            lock.lock(lockfile.LOCK_EX)
            if os.path.exists(_file):
                ret = self.load(_file)
                if ret:
                    stored_time, expiry_time, value = ret
                    if self._is_not_expiry(stored_time, expiry_time):
                        pass
                    else:
                        value = 0
            v = min(0, value - step)
            self.save(key, now, expire, v)
            return v
        finally:
            lock.close()
    
    def _get_file(self, key):
        return encoded_path(self.file_dir, key, '.ses')
    
    def _get_lock(self, key):
        lfile = encoded_path(self.lock_dir, key, '.lock')
        return lockfile.LockFile(lfile)
    
    def load(self, filename):
        f = open(filename, 'rb')
        error = False
        try:
            text = f.read()
            if not text:
                return None
            try:
                v = self._load(text)
                return v
            except:
                error = True
                return None
        finally:
            f.close()
            if error:
                try:
                    os.unlink(filename)
                except:
                    pass
    
    def save(self, key, stored_time, expiry_time, value):
        _file = self._get_file(key)
        verify_path(_file)
        f = open(_file, 'wb')
        ok = False
        try:
            v = self._dump((stored_time, expiry_time, value))
            f.write(v)
            ok = True
        finally:
            f.close()
            if not ok:
                os.unlink(_file)
    
    def _is_not_expiry(self, accessed_time, expiry_time):
        return time.time() < accessed_time + expiry_time
    