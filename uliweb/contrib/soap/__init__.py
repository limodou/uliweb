import inspect
from functools import partial
from pysimplesoap.simplexml import (Date, DateTime, Decimal, byte, short, 
    double, integer, Time, TYPE_MAP)

__soap_functions__ = {'SOAP':{}}

def _fix_soap_kwargs(kwargs):
    def _f(args):
        s = list(args)[:]
        for i, v in enumerate(args):
            if not isinstance(v, dict):
                #this should be a single type, .e.g [str]
                if v in TYPE_MAP.keys():
                    s[i] = {TYPE_MAP[v]:v}
                else:
                    raise Exception, "Unsupport type %r" % v
        return s
    
    if kwargs is None:
        return None
    for k, v in kwargs.items():
        if isinstance(v, (tuple, list)):
            kwargs[k] = _f(v)
    return kwargs

def soap(func=None, name=None, returns=None, args=None, doc=None, target='SOAP'):
    """
    soap supports multiple SOAP function collections, it'll save functions to 
    target dict, and you can give other target, but it should be keep up with
    SoapView.target definition.
    """
    global __soap_functions__
    
    returns = _fix_soap_kwargs(returns)
    args = _fix_soap_kwargs(args)
    
    if isinstance(func, str) and not name:
        return partial(soap, name=func, returns=returns, args=args, doc=doc, target=target)
    
    if not func:
        return partial(soap, name=name, returns=returns, args=args, doc=doc, target=target)

    target_functions = __soap_functions__.setdefault(target, {})
    if inspect.isfunction(func):
        f_name = func.__name__
        if name:
            f_name = name
        target_functions[f_name] = endpoint = ('.'.join([func.__module__, func.__name__]), returns, args, doc)
        func.soap_endpoint = (f_name, endpoint)
    elif inspect.isclass(func):
        if not name:
            name = func.__name__
        for _name in dir(func):
            f = getattr(func, _name)
            if (inspect.ismethod(f) or inspect.isfunction(f)) and not _name.startswith('_'):
                f_name = name + '.' + f.__name__
                endpoint = ('.'.join([func.__module__, func.__name__, _name]), returns, args, doc)
                if hasattr(f, 'soap_endpoint'):
                    #the method has already been decorate by soap 
                    _n, _e = f.soap_endpoint
                    target_functions[name + '.' + _n] = endpoint
                    del target_functions[_n]
                else:
                    target_functions[f_name] = endpoint
    else:
        raise Exception("Can't support this type [%r]" % func)
    return func
    
if __name__ == '__main__':
    @soap
    def f(name):
        print (name)
        
    @soap('GetName', returns={'Int':int}, args={'a':int})
    def p(a):
        print (a)
        
    @soap(returns={'Int':int}, args={'a':int})
    def d(a):
        print (a)
    
    print (__soap_functions__)
    
    @soap('B')
    class A(object):
        def p(self):
            print ('ppp')
            
        @soap('test')
        def t(self):
            print ('ttt')
            
    print (__soap_functions__)
    
