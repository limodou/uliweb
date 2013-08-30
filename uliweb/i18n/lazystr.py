def lazy(func):
    def f(message):
        return LazyString(func, message)
    return f
    
class LazyString(object):
    """
    >>> from uliweb.i18n import gettext_lazy as _
    >>> x = _('Hello')
    >>> print repr(x)
    """
    def __init__(self, func, message):
        self._func = func
        self.msg = message
        self._format = []
        
    def __unicode__(self):
        if not self.msg:
            return ''
        value = self.getvalue()
        if isinstance(value, unicode):
            return value
        else:
            return unicode(self.getvalue(), 'utf-8')
        
    def __str__(self):
        if not self.msg:
            return ''
        value = self.getvalue()
        if isinstance(value, unicode):
            return value.encode('utf-8')
        else:
            return str(value)
    
    def format(self, *args, **kwargs):
        self._format.append((args, kwargs))
        return self
        
    def getvalue(self):
        v = self._func(self.msg)
        for args, kwargs in self._format:
            v = v.format(*args, **kwargs)
        return v
    
    def __repr__(self):
        return "%s_lazy(%r)" % (self._func.__name__, self.msg)
    
    def __add__(self, obj):
        return self.getvalue() + obj
        
    def __radd__(self, obj):
        return obj + self.getvalue()
        
    def encode(self, encoding):
        return self.getvalue().encode(encoding)
    
    def split(self, *args, **kwargs):
        return self.getvalue().split(*args, **kwargs)
    
#    def __getattr__(self, name):
#        return getattr(self.getvalue(), name)
