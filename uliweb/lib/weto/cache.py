#########################################################################
# cache module written by limodou(limodou@gmail.com) at 2009/11/03
#
# storage class will ensure the sync when load and save a session from 
# and to the storage.
#########################################################################
import cPickle
from backends.base import KeyError

__modules__ = {}

def wrap_func(des, src):
    des.__name__ = src.__name__
    des.func_globals.update(src.func_globals)
    des.__doc__ = src.__doc__
    des.__module__ = src.__module__
    des.__dict__.update(src.__dict__)
    return des

class NoSerial(object):
    def load(self, s):
        return s
    
    def dump(self, v):
        return v
    
class Serial(NoSerial):
    def load(self, s):
        return cPickle.loads(s)
    
    def dump(self, v):
        return cPickle.dumps(v, cPickle.HIGHEST_PROTOCOL)
    
class Empty(object):
    pass

class Cache(object):
    def __init__(self, storage_type='file', options=None, expiry_time=3600*24*365,
        serial_cls=Serial):
        self._storage_type = storage_type
        self._options = options or {}
        self._storage_cls = self.__get_storage()
        self._storage = None
        self._serial_cls = serial_cls
        self.serial_obj = serial_cls()
        self.expiry_time = expiry_time
     
    def __get_storage(self):
        modname = 'weto.backends.%s_storage' % self._storage_type
        if modname in __modules__:
            return __modules__[modname]
        else:
            mod = __import__(modname, {}, {}, [''])
            _class = getattr(mod, 'Storage', None)
            __modules__[modname] = _class
        return _class
    
    @property
    def storage(self):
        if not self._storage:
            self._storage = self._storage_cls(self, self._options)
        return self._storage
    
    def get(self, key, default=Empty):
        try:
            return self.storage.get(key)
        except KeyError, e:
            if default is not Empty:
                return default
            else:
                raise
            
    def set(self, key, value=None, expire=None):
        return self.storage.set(key, value, expire or self.expiry_time)
        
    def delete(self, key):
        return self.storage.delete(key)
             
    def __getitem__(self, key):
        return self.get(key)
    
    def __setitem__(self, key, value):
        return self.set(key, value)
    
    def __delitem__(self, key):
        self.delete(key)
        
    def setdefault(self, key, defaultvalue, expire=None):
        try:
            v = self.get(key)
            return v
        except KeyError:
            self.set(key, defaultvalue, expire)
            return defaultvalue
        
    def cache(self, k=None, expire=None):
        def _f(func):
            def f(*args, **kwargs):
                if not k:
                    r = repr(args) + repr(sorted(kwargs.items()))
                    key = func.__module__ + '.' + func.__name__ + r
                else:
                    key = k
                try:
                    ret = self.get(key)
                    return ret
                except KeyError:
                    ret = func(*args, **kwargs)
                    self.set(key, ret, expire=expire)
                    return ret
            
            wrap_func(f, func)
            return f
        return _f
    
    
