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
        
    def __setitem__(self, key, value, append=False):
        """
        If append == True, then force existed key append to the end
        """
        self._dict[key] = value
        try:
            index = self._fields.index(key)
        except ValueError:
            index = -1
        if index > -1:
            if append:
                del self._fields[index]
                self._fields.append(key)
        else:
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
        
    def __len__(self):
        return len(self._dict)
        
    def __contains__(self, key):
        return key in self._dict
    
    def keys(self):
        return self._fields
    
    def values(self):
        return [self._dict[k] for k in self._fields]
    
    def iterkeys(self):
        return self.keys()
    
    def itervalues(self):
        return self.values()
        
    def update(self, value):
        for k, v in value.items():
            self.__setitem__(k, v)
        
    def items(self):
        return [(k, self[k]) for k in self._fields]
    
    def iteritems(self):
        return self.items()
    
    def get(self, key, default=None):
        try: 
            return self.__getitem__(key)
        except KeyError, k: 
            return default
    
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
    
    def sort(self, cmp=None, key=None, reverse=False):
        self._fields = [x for x, y in sorted(self.items(), cmp, key, reverse)]
        
    def setdefault(self, key, value):
        if key in self._dict:
            return self._dict[key]
        else:
            self._dict[key] = value
            self._fields.append(key)
            return value

    def clear(self):
        self._dict.clear()
        self._fields = []
    