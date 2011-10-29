#! /usr/bin/env python
#coding=utf-8
# inspired from http://code.activestate.com/recipes/496741-object-proxying/
class Global(object): pass

class LocalProxy(object):
    __slots__ = ['_env', '_obj_name']
    
    def __init__(self, environ, name, klass):
        object.__setattr__(self, "_env", environ)
        object.__setattr__(self, "_obj_name", name)
        
    def __get_instance__(self):
        return getattr(self._env, self._obj_name, None)

    def __getattr__(self, name):
        return getattr(self.__get_instance__(), name)
    
    def __setattr__(self, name, value):
        setattr(self.__get_instance__(), name, value)
        
    def __delattr__(self, name):
        delattr(self.__get_instance__(), name)

    def __nonzero__(self):
        return bool(self.__get_instance__())

    def __str__(self):
        return str(self.__get_instance__())
    
    def __repr__(self):
        return repr(self.__get_instance__())
    
    #
    # factories
    #
    _special_names = [
        '__abs__', '__add__', '__and__', '__call__', '__cmp__', '__coerce__', 
        '__contains__', '__delitem__', '__delslice__', '__div__', '__divmod__', 
        '__eq__', '__float__', '__floordiv__', '__ge__', '__getitem__', 
        '__getslice__', '__gt__', '__hash__', '__hex__', '__iadd__', '__iand__',
        '__idiv__', '__idivmod__', '__ifloordiv__', '__ilshift__', '__imod__', 
        '__imul__', '__int__', '__invert__', '__ior__', '__ipow__', '__irshift__', 
        '__isub__', '__iter__', '__itruediv__', '__ixor__', '__le__', '__len__', 
        '__long__', '__lshift__', '__lt__', '__mod__', '__mul__', '__ne__', 
        '__neg__', '__oct__', '__or__', '__pos__', '__pow__', '__radd__', 
        '__rand__', '__rdiv__', '__rdivmod__', '__reduce__', '__reduce_ex__', 
        '__repr__', '__reversed__', '__rfloorfiv__', '__rlshift__', '__rmod__', 
        '__rmul__', '__ror__', '__rpow__', '__rrshift__', '__rshift__', '__rsub__', 
        '__rtruediv__', '__rxor__', '__setitem__', '__setslice__', '__sub__', 
        '__truediv__', '__xor__', 'next',
    ]
    
    @classmethod
    def _create_class_proxy(cls, theclass):
        """creates a proxy for the given class"""
        
        def make_method(name):
            def method(self, *args, **kw):
                return getattr(self.__get_instance__(), name)(*args, **kw)
            return method
        
        namespace = {}
        for name in cls._special_names:
            if hasattr(theclass, name):
                namespace[name] = make_method(name)
        return type("%s(%s)" % (cls.__name__, theclass.__name__), (cls,), namespace)
    
    def __new__(cls, env, name, klass, *args, **kwargs):
        """
        creates an proxy instance referencing `obj`. (obj, *args, **kwargs) are
        passed to this class' __init__, so deriving classes can define an 
        __init__ method of their own.
        note: _class_proxy_cache is unique per deriving class (each deriving
        class must hold its own cache)
        """
        try:
            cache = cls.__dict__["_class_proxy_cache"]
        except KeyError:
            cls._class_proxy_cache = cache = {}
        try:
            theclass = cache[klass]
        except KeyError:
            cache[klass] = theclass = cls._create_class_proxy(klass)
        ins = object.__new__(theclass)
        return ins
