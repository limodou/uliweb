import os
import inspect
from uliweb.utils.common import log

class ReservedKeyError(Exception):pass

__exposes__ = {}
__no_need_exposed__ = []
__class_methods__ = {}
__app_rules__ = {}
__url_names__ = {}
static_views = []

reserved_keys = ['settings', 'redirect', 'application', 'request', 'response', 'error',
    'json']

def add_rule(map, url, endpoint=None, **kwargs):
    from werkzeug.routing import Rule
    kwargs['endpoint'] = endpoint
    try:
        map.add(Rule(url, **kwargs))
    except ValueError as e:
        log.info("Wrong url is %s, endpoint=%s" % (url, endpoint))
        raise
            
def merge_rules():
    s = []
    index = {}
    for v in __exposes__.itervalues():
        for x in v:
            appname, endpoint, url, kw = x
            methods = [y.upper() for y in kw.get('methods', [])]
            methods.sort()
            i = index.get((url, tuple(methods)), None)
            if i is not None:
                s[i] = x
            else:
                s.append(x)
                index[(url, tuple(methods))] = len(s)-1
    return __no_need_exposed__ + s

def clear_rules():
    global __exposes__, __no_need_exposed__
    __exposes__ = {}
    __no_need_exposed__ = []

def set_app_rules(rules):
    global __app_rules__
    __app_rules__.update(rules)
    
def expose(rule=None, **kwargs):
    e = Expose(rule, **kwargs)
    if e.parse_level == 1:
        return rule
    else:
        return e
    
class Expose(object):
    def __init__(self, rule=None, restful=False, **kwargs):
        self.restful = restful
        if inspect.isfunction(rule) or inspect.isclass(rule):
            self.parse_level = 1
            self.rule = None
            self.kwargs = {}
            self.parse(rule)
        else:
            self.parse_level = 2
            self.rule = rule
            self.kwargs = kwargs
            
    def _fix_url(self, appname, rule):
        if rule.startswith('/') and appname in __app_rules__:
            suffix = __app_rules__[appname]
            url = os.path.join(suffix, rule.lstrip('/')).replace('\\', '/')
        else:
            if rule.startswith('!'):
                url = rule[1:]
            else:
                url = rule
        return url.rstrip('/') or '/'
            
    def _get_path(self, f):
        m = f.__module__.split('.')
        s = []
        for i in m:
            if not i.startswith('views'):
                s.append(i)
        appname = '.'.join(s)
        return appname, '/'.join(s)
    
    def parse(self, f):
        if inspect.isfunction(f) or inspect.ismethod(f):
            func, result = self.parse_function(f)
            a = __exposes__.setdefault(func, [])
            a.append(result)
        else:
            result = list(self.parse_class(f))
            __no_need_exposed__.extend(result)
            
    def parse_class(self, f):
        appname, path = self._get_path(f)
        clsname = f.__name__
        if self.rule:
            prefix = self.rule
        else:
            prefix = '/' + '/'.join([path, clsname])
        f.__exposed_url__ = prefix
        for name in dir(f):
            func = getattr(f, name)
            if (inspect.ismethod(func) or inspect.isfunction(func)) and not name.startswith('_'):
                if hasattr(func, '__exposed__') and func.__exposed__:
                    new_endpoint = '.'.join([func.__module__, f.__name__, name])
                    if func.im_func in __exposes__:
                        for v in __exposes__.pop(func.im_func):
                            #__no_rule__ used to distinct if the view function has used
                            #expose to decorator, if not then __no_rule__ will be True
                            #then it'll use default url route regular to make url
                            if func.__no_rule__:
                                rule = self._get_url(appname, prefix, func)
                            else:
                                _old = func.__old_rule__.get(v[2])
                                keep = _old.startswith('!')
                                if keep:
                                    _old = _old[1:]
                                if _old:
                                    rule = os.path.join(prefix, _old).replace('\\', '/')
                                else:
                                    rule = prefix
                                #if rule has perfix of appname, then fix it, otherwise
                                #maybe it's root url, e.g. /register
                                if not keep and rule.startswith(prefix):
                                    rule = self._fix_url(appname, rule)
                            __no_need_exposed__.append((v[0], new_endpoint, rule, v[3]))
                            for k in __url_names__.iterkeys():
                                if __url_names__[k] == v[1]:
                                    __url_names__[k] = new_endpoint
                else:
                    rule = self._get_url(appname, prefix, func)
                    endpoint = '.'.join([f.__module__, clsname, func.__name__])
                    yield appname, endpoint, rule, {}
    
    def _get_url(self, appname, prefix, f):
        args = inspect.getargspec(f)[0]
        if args:
            if inspect.ismethod(f):
                args = args[1:]
            args = ['<%s>' % x for x in args]
        if f.__name__ in reserved_keys:
            raise ReservedKeyError, 'The name "%s" is a reversed key, so please change another one' % f.__name__
        prefix = prefix.rstrip('/')
        if self.restful:
            rule = self._fix_url(appname, '/'.join([prefix] + args[:1] + [f.__name__] +args[1:]))
        else:
            rule = self._fix_url(appname, '/'.join([prefix, f.__name__] +args))
        return rule
    
    def parse_function(self, f):
        args = inspect.getargspec(f)[0]
        if args:
            args = ['<%s>' % x for x in args]
        if f.__name__ in reserved_keys:
            raise ReservedKeyError, 'The name "%s" is a reversed key, so please change another one' % f.__name__
        appname, path = self._get_path(f)
        if self.rule is None:
            if self.restful:
                rule = '/' + '/'.join([path] + args[:1] + [f.__name__] + args[1:])
            else:
                rule = '/' + '/'.join([path, f.__name__] + args)
        else:
            rule = self.rule
        rule = self._fix_url(appname, rule)
        if inspect.ismethod(f):
            endpoint = '.'.join([f.im_class.__module__, f.im_class.__name__, f.__name__])
        else:
            endpoint = '.'.join([f.__module__, f.__name__])
        f.func_dict['__exposed__'] = True
        f.func_dict['__no_rule__'] = (self.parse_level == 1) or (self.parse_level == 2 and (self.rule is None))
        if not hasattr(f, '__old_rule__'):
            f.func_dict['__old_rule__'] = {}
    
        f.func_dict['__old_rule__'][rule] = self.rule
        #add name parameter process
        if 'name' in self.kwargs:
            url_name = self.kwargs.pop('name')
            __url_names__[url_name] = endpoint
        return f, (appname, endpoint, rule, self.kwargs.copy())
    
    def __call__(self, f):
        from uliweb.utils.common import safe_import
        
        if isinstance(f, (str, unicode)):
            try:
                _, f = safe_import(f)
            except:
                log.error('Import error: rule=%s' % f)
                raise
        self.parse(f)
        return f
    
