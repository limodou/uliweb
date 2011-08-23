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

        if 'unix_socket_path' in options:
            self.client = redis.Redis(unix_socket_path=options['unix_socket_path'])
        else:
            global __connection_pool__
        
            if not __connection_pool__ or __connection_pool__[0] != options['connection_pool']:
                d = {'host':'localhost', 'port':6379}
                d.update(options['connection_pool'])
                __connection_pool__ = (d, redis.ConnectionPool(**d))
            self.client = redis.Redis(connection_pool=__connection_pool__[1])
            
    def get(self, key):
        v = self.client.get(key)
        if v is not None:
            return self._load(v)
        else:
            raise KeyError, "Cache key [%s] not found" % key
    
    def set(self, key, value, expiry_time):
        v =self._dump(value)
        pipe = self.client.pipeline()
        return pipe.set(key, v).expire(key, expiry_time).execute()
    
    def delete(self, key):
        return self.client.delete(key)
        
