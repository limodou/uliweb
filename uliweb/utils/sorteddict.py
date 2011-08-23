class SortedDict(object):
    def __init__(self):
        self._dict = {}
        self._fields = []
            
    def __getitem__(self, key):
        return self._dict[key]
    
    def __getattr__(self, key): 
        try: 
            return self.__getitem__(key)
        except KeyError, k: 
            return None
        
    def __setitem__(self, key, value):
        self._dict[key] = value
        if key not in self._fields:
            self._fields.append(key)
        
    def __setattr__(self, key, value):
        if key.startswith('_'):
            self.__dict__[key] = value
        else:
            self.__setitem__(key, value)
            
    def __delitem__(self, key):
        if key.startswith('_'):
            del self.__dict__[key]
        else:
            del self._dict[key]
            self._fields.remove(key)
            
    def __delattr__(self, key):
        try: 
            self.__delitem__(key)
        except KeyError, k: 
            raise AttributeError, k
        
    def __contains__(self, key):
        return key in self._dict
    
    def keys(self):
        return self._fields
    
    def values(self):
        return [self._dict[k] for k in self._fields]
    
    def iterkeys(self):
        return iter(self.keys)
    
    def itemvalues(self):
        return (self._dict[k] for k in self._fields)
        
    def update(self, value):
        for k, v in value.iteritems():
            self.__setitem__(k, v)
        
    def items(self):
        return [(k, self._dict[k]) for k in self._fields]
    
    def iteritems(self):
        return ((k, self._dict[k]) for k in self._fields)
    
    def get(self, key, default=None):
        return self._dict.get(key, default)
    
    def pop(self, key, default=None):
        v = self._dict.pop(key, default)
        if key in self._fields:
            self._fields.remove(key)
        return v
    
    def __repr__(self):
        return '<%s {%s}>' % (self.__class__.__name__, ', '.join(['%r:%r' % (k, v) for k, v in sorted(self.items())]))

    def dict(self):
        return self._dict.copy()
    
    def copy(self):
        return self._dict.copy()
