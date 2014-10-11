from base import BaseStorage, KeyError
import redis

#connection pool format should be: (options, connection object)
__connection_pool__ = None

class Storage(BaseStorage):
    def __init__(self, cache_manager, options):
        """
        options =
            unix_socket_path = '/tmp/redis.sock'
            or
            connection_pool = {'host':'localhost', 'port':6379, 'db':0}
        """
        BaseStorage.__init__(self, cache_manager, options)

        self._type = (int, long)
        
        if 'unix_socket_path' in options:
            self.client = redis.Redis(unix_socket_path=options['unix_socket_path'])
        else:
            global __connection_pool__
        
            if not __connection_pool__ or __connection_pool__[0] != options['connection_pool']:
                d = {'host':'localhost', 'port':6379}
                d.update(options['connection_pool'])
                __connection_pool__ = (d, redis.ConnectionPool(**d))
            self.client = redis.Redis(connection_pool=__connection_pool__[1])
    
    def _key(self, key):
        return 'session:'+key
    
    def get(self, key):
        key = self._key(key)
        v = self.client.get(key)
        if v is not None:
            if not v.isdigit():
                return self._load(v)
            else:
                return int(v)
        else:
            raise KeyError("Cache key [%s] not found" % key)
    
    def set(self, key, value, expiry_time):
        key = self._key(key)
        if not isinstance(value, self._type):
            v = self._dump(value)
        else:
            v = value
        r = self.client.setex(key, v, expiry_time)
        return r
    
    def delete(self, key):
        key = self._key(key)
        self.client.delete(key)
        return True
        
    def inc(self, key, step, expiry_time):
        key = self._key(key)
        pipe = self.client.pipeline()
        r = pipe.incr(key, step).expire(key, expiry_time).execute()
        return r[0]
    
    def dec(self, key, step, expiry_time):
        key = self._key(key)
        pipe = self.client.pipeline()
        r = pipe.decr(key, step).expire(key, expiry_time).execute()
        return r[0]
        
        