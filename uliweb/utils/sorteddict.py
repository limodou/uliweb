__all__ = ['SortedDict']

from itertools import imap as _imap

class SortedDict(dict):
    def __init__(self, value=None, kvio=False):
        """
        SortedDict will implement Key Insertion Order (KIO: updates of values
        do not affect the position of the key), Key Value Insertion Order (KVIO,
        an existing key's position is removed and put at the back)
        """
        self._kvio = kvio
        self._fields = []
        self.update(value or {})
            
    def __setitem__(self, key, value, append=False, dict_setitem=dict.__setitem__):
        if not key in self:
            self._fields.append(key)
        elif self._kvio or append:
            self._fields.remove(key)
            self._fields.append(key)
        return dict_setitem(self, key, value)
        
    def __delitem__(self, key, dict_delitem=dict.__delitem__):
        if key.startswith('_'):
            del self.__dict__[key]
        else:
            dict_delitem(self, key)
            self._fields.remove(key)

    def __iter__(self):
        'od.__iter__() <==> iter(od)'
        for k in self._fields:
            yield k

    def __reversed__(self):
        'od.__reversed__() <==> reversed(od)'
        for k in reversed(self._fields):
            yield k

    def __getattr__(self, key):
        try:
            return self.__getitem__(key)
        except KeyError as k:
            return None

    def __setattr__(self, key, value):
        if key.startswith('_'):
            self.__dict__[key] = value
        else:
            self.__setitem__(key, value)

    def __delattr__(self, key):
        try:
            self.__delitem__(key)
        except KeyError as k:
            raise AttributeError(k)

    def keys(self):
        return self._fields
    
    def values(self):
        return [self[k] for k in self._fields]
    
    def iterkeys(self):
        return iter(self)
    
    def itervalues(self):
        for k in self:
            yield self[k]
        
    def update(self, value):
        for k, v in value.items():
            self.__setitem__(k, v)
        
    def items(self):
        return [(k, self[k]) for k in self._fields]
    
    def iteritems(self):
        for k in self:
            yield (k, self[k])

    def pop(self, key, default=None):
        v = dict.pop(self, key, default)
        if key in self._fields:
            self._fields.remove(key)
        return v
    
    def __repr__(self):
        return '<%s {%s}>' % (self.__class__.__name__, ', '.join(['%r:%r' % (k, v) for k, v in sorted(self.items())]))

    def dict(self):
        return self
    
    def copy(self):
        return self.__class__(self)
    
    # def sort(self, cmp=None, key=None, reverse=False):
    #     self._fields = [x for x, y in sorted(self.items(), cmp, key, reverse)]
    #
    def setdefault(self, key, value=None):
        if key in self:
            return self[key]
        else:
            self[key] = value
            return value

    def clear(self):
        dict.clear(self)
        self._fields = []

    def __eq__(self, other):
        '''od.__eq__(y) <==> od==y.  Comparison to another OD is order-sensitive
        while comparison to a regular mapping is order-insensitive.

        '''
        if isinstance(other, SortedDict):
            return dict.__eq__(self, other) and all(_imap(_eq, self, other))
        return dict.__eq__(self, other)

    def __ne__(self, other):
        'od.__ne__(y) <==> od!=y'
        return not self == other

