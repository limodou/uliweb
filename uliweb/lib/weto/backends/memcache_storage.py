from base import BaseStorage, KeyError

class Error(Exception):pass

class Storage(BaseStorage):
    def __init__(self, cache_manager, options):
        """
        options =
            connection = ['localhost:11211']
            module = None
        """
        BaseStorage.__init__(self, cache_manager, options)
        if not options.get('connection'):
            options['connection'] = ['localhost:11211']

        self.client = self.import_preferred_memcache_lib(options)
        if self.client is None:
            raise Error('no memcache module found')
            
    def get(self, key):
        """
        because memcached does not provide a function to check if a key is existed
        so here is a heck way, if the value is None, then raise Exception
        """
        if isinstance(key, unicode):
            key = key.encode('utf-8')
        v = self.client.get(key)
        if v is None:
            raise KeyError("Cache key [%s] not found" % key)
        else:
            return v
    
    def set(self, key, value, expiry_time):
        if isinstance(key, unicode):
            key = key.encode('utf-8')
        return self.client.set(key, value, expiry_time)
    
    def delete(self, key):
        return bool(self.client.delete(key))
        
    def inc(self, key, step, expiry_time):
        try:
            v = self.get(key)
        except KeyError:
            v = None
        if v and isinstance(v, (int, long)):
            return self.client.incr(key, step)
        else:
            self.set(key, step, expiry_time)
            return step
    
    def dec(self, key, step, expiry_time):
        try:
            v = self.get(key)
        except KeyError:
            v = None
        if v and isinstance(v, (int, long)):
            return self.client.decr(key, step)
        else:
            self.set(key, 0, expiry_time)
            return 0
        
    def import_preferred_memcache_lib(self, options):
        servers = options['connection']
        modname = options.get('module')
        if modname:
            mod_path, cls_name = modname.rsplit('.', 1)
            mod = __import__(mod_path, fromlist=['*'])
            cls = getattr(mod, cls_name)
            return cls(servers)
        
        try:
            import pylibmc
        except ImportError:
            pass
        else:
            return pylibmc.Client(servers)
    
        try:
            from google.appengine.api import memcache
        except ImportError:
            pass
        else:
            return memcache.Client()
    
        try:
            import memcache
        except ImportError:
            pass
        else:
            return memcache.Client(servers)
    