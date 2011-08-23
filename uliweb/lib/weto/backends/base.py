__all__ = ['BaseStorage', 'KeyError']

import os

class KeyError(Exception):pass

class BaseStorage(object):
    def __init__(self, cache_manager, options):
        self.cache_manager = cache_manager
        self.options = options
        
    def get(self, key):
        raise NotImplementedError()
    
    def set(self, key, value):
        raise NotImplementedError()
    
    def delete(self, key):
        raise NotImplementedError()
    
    def _load(self, v):
        return self.cache_manager.serial_obj.load(v)
    
    def _dump(self, v):
        return self.cache_manager.serial_obj.dump(v)