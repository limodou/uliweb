import inspect
from functools import partial

__xmlrpc_functions__ = {}

class Rule(object):
    pass

def xmlrpc(func, name=None):
    global __xmlrpc_functions__
    
    if isinstance(func, str):
        return partial(xmlrpc, name=func)
            
    if inspect.isfunction(func):
        f_name = func.__name__
        if name:
            f_name = name
        rule = Rule()
        rule.endpoint = '.'.join([func.__module__, func.__name__])
        rule.rule = rule.endpoint
        __xmlrpc_functions__[f_name] = rule
        func.xmlrpc_endpoint = (f_name, rule.endpoint)
    elif inspect.isclass(func):
        if not name:
            name = func.__name__
        for _name in dir(func):
            f = getattr(func, _name)
            if (inspect.ismethod(f) or inspect.isfunction(f)) and not _name.startswith('_'):
                f_name = name + '.' + f.__name__
                endpoint = '.'.join([func.__module__, func.__name__, _name])
                rule = Rule()
                rule.endpoint = rule.rule = endpoint
                if hasattr(f, 'xmlrpc_endpoint'):
                    #the method has already been decorate by xmlrpc 
                    _n, _e = f.xmlrpc_endpoint
                    __xmlrpc_functions__[name + '.' + _n] = rule
                    del __xmlrpc_functions__[_n]
                else:
                    __xmlrpc_functions__[f_name] = rule
    else:
        raise Exception("Can't support this type [%r]" % func)
    return func
    
if __name__ == '__main__':
    @xmlrpc
    def f(name):
        print (name)
        
    print (__xmlrpc_functions__)
    
    @xmlrpc('B')
    class A(object):
        def p(self):
            print ('ppp')
            
        @xmlrpc('test')
        def t(self):
            print ('ttt')
            
    print (__xmlrpc_functions__)
    