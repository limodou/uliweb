#########################################################################
# session module written by limodou(limodou@gmail.com) at 2009/08/25
# this module is inspired by beaker package
#
# storage class will ensure the sync when load and save a session from 
# and to the storage.
#########################################################################
import os
import random
import time
try:
    from hashlib import md5
except ImportError:
    from md5 import md5
 
from backends.base import KeyError

class SessionException(Exception):pass
class NValue(object): pass

getpid = hasattr(os, 'getpid') and os.getpid or (lambda : '')

def _get_id():
    return md5(
                md5("%f%s%f%s" % (time.time(), id({}), random.random(),
                                  getpid())).hexdigest(), 
            ).hexdigest()

class SessionCookie(object):
    default_expiry_time = None #if None will use session expiry time
    default_domain = ''
    default_secure = False
    default_path = '/'
    default_cookie_id = 'session_cookie_id'
    
    def __init__(self, session):
        self.session = session
        self.domain = self.default_domain
        self.path = self.default_path
        self.secure = self.default_secure
        self.expiry_time = self.default_expiry_time
        self.cookie_id = self.default_cookie_id
        
    def save(self):
        self.expiry_time =  self.expiry_time or self.session.expiry_time
   
from cache import Serial

class Session(dict):
    force = False
    
    def __init__(self, key=None, storage_type='file', options=None, expiry_time=3600*24*365,
        serial_cls=None):
        """
        expiry_time is just like max_age, the unit is second
        """
        dict.__init__(self)
        self._old_value = {}
        self._storage_type = storage_type
        self._options = options or {}
        self._storage_cls = self.__get_storage()
        self._storage = None
        self._accessed_time = None
        self.expiry_time = expiry_time
        self.key = key
        self.deleted = False
        self.cookie = SessionCookie(self)
        self._serial_cls = serial_cls or Serial
        self.serial_obj = self._serial_cls()
        
        self.load(self.key)
        
    def __get_storage(self):
        modname = 'weto.backends.%s_storage' % self._storage_type
        mod = __import__(modname, fromlist=['*'])
        _class = getattr(mod, 'Storage', None)
        return _class
    
    def _set_remember(self, v):
        self['_session_remember_'] = v
        
    def _get_remember(self):
        return self.get('_session_remember_', False)
    
    remember = property(_get_remember, _set_remember)
    
    @property
    def storage(self):
        if not self._storage:
            self._storage = self._storage_cls(self, self._options)
        return self._storage
    
    def load(self, key=None):
        self.deleted = False
        self.clear()
        
        self.key = key
        if not self.key:
            return
        
        try:
            value = self.storage.get(key)
        except KeyError, e:
            value = {}
        self.update(value)
        self._old_value = self.copy()
            
    def _is_modified(self):
        return self._old_value != dict(self)
    
    def save(self, force=False):
        flag = force
        if not flag:
            if not self.deleted and self.force and (bool(self) or (not bool(self) and self._is_modified())):
                flag = True
            elif not self.deleted and not self.force and self._is_modified():
                flag = True
#        if not self.deleted and (bool(self) or (not bool(self) and self._is_modified())):
        if flag:
            self.key = self.key or _get_id()
            d = {}
            for k, value in dict(self).items():
                v, accessed_time, expiry_time = self._parse_value(value)
                if expiry_time and accessed_time:
                    if self._is_not_expiry(accessed_time, expiry_time):
                        d[k] = value
                else:
                    d[k] = v
            self.storage.set(self.key, d, self.expiry_time)
            self.cookie.save()
            return True
        else:
            return False
        
    def delete(self):
        if self.key:
            self.storage.delete(self.key)
            self.clear()
            self._old_value = self.copy()
                
        self.deleted = True
         
    def set_expiry(self, value):
        self.expiry_time = value
        self.cookie.expiry_time = value
        
    def _is_not_expiry(self, accessed_time, expiry_time):
        return time.time() < accessed_time + expiry_time
    
    def _check(f):
        def _func(self, *args, **kw):
            try:
                if self.deleted:
                    raise SessionException, "The session object has been deleted!"
                return f(self, *args, **kw)
            finally:
                self._accessed_time = time.time()
        return _func
    
    def _parse_value(self, v):
        if isinstance(v, dict) and '_v' in v and '_atime' in v and '_etime' in v:
            v, accessed_time, expiry_time = v['_v'], v['_atime'], v['_etime']
        else:
            accessed_time, expiry_time = None, None
        return v, accessed_time, expiry_time
    
    @_check
    def __getitem__(self, name):
        v = dict.get(self, name, NValue)
        if v is NValue:
            raise KeyError("Key %s can not be found" % name)
        
        v, accessed_time, expiry_time = self._parse_value(v)
        if expiry_time and accessed_time:
            if self._is_not_expiry(accessed_time, expiry_time):
                return v
            else:
                del self[name]
                raise KeyError("Key %s can not be found" % name)
        else:
            return v
    
    @_check    
    def get(self, name, default=None):
        try:
            v = self.__getitem__(name)
            return v
        except KeyError:
            return default
        
    def set(self, name, value, expiry_time=None):
        if expiry_time:
            v = {'_v':value, '_etime':expiry_time, '_atime':time.time()}
        else:
            v = value
        self.__setitem__(name, v)
        
    clear = _check(dict.clear)
    __setitem__ = _check(dict.__setitem__)
    __delitem__ = _check(dict.__delitem__)
    pop = _check(dict.pop)
    popitem = _check(dict.popitem)
    setdefault = _check(dict.setdefault)
    update = _check(dict.update)
    
    