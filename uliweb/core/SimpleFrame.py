####################################################################
# Author: Limodou@gmail.com
# License: BSD
####################################################################

import os, sys
import cgi
import inspect
import re
import types
from werkzeug import Request as OriginalRequest, Response as OriginalResponse
from werkzeug import ClosingIterator, Local, LocalManager, BaseResponse
from werkzeug.exceptions import HTTPException, NotFound, BadRequest
from werkzeug.routing import Map

import template
from js import json_dumps
import dispatch
from uliweb.utils.storage import Storage
from uliweb.utils.common import (pkg, log, import_attr, 
    myimport, wraps, norm_path)
import uliweb.utils.pyini as pyini
from uliweb.i18n import gettext_lazy, i18n_ini_convertor
from uliweb.utils.localproxy import LocalProxy, Global
from uliweb import UliwebError

#from rules import Mapping, add_rule
import rules

try:
    set
except:
    from sets import Set as set

local = Local()
__global__ = Global()
local_manager = LocalManager([local])
url_map = Map()
static_views = []
use_urls = False
url_adapters = {}
__app_dirs__ = {}
__app_alias__ = {}
_xhr_redirect_json = True

r_callback = re.compile(r'^[\w_]+$')
#Initialize pyini env
pyini.set_env({
    'env':{'_':gettext_lazy, 'gettext_lazy':gettext_lazy},
    'convertors':i18n_ini_convertor,
})
__global__.settings = pyini.Ini(lazy=True)

#User can defined decorator functions in settings DECORATORS
#and user can user @decorators.function_name in views
#and this usage need settings be initialized before decorator invoking

class Finder(object):
    def __init__(self, section):
        self.__objects = {}
        self.__section = section
    
    def __contains__(self, name):
        if name in self.__objects:
            return True
        if name not in settings[self.__section]:
            return False
        else:
            return True
        
    def __getattr__(self, name):
        if name in self.__objects:
            return self.__objects[name]
        if name not in settings[self.__section]:
            raise UliwebError("Object %s is not existed!" % name)
        obj = import_attr(settings[self.__section].get(name))
        self.__objects[name] = obj
        return obj
    
    def __setitem__(self, name, value):
        if isinstance(value, (str, unicode)):
            value = import_attr(value)
        self.__objects[name] = value

decorators = Finder('DECORATORS')
functions = Finder('FUNCTIONS')

class Request(OriginalRequest):
    GET = OriginalRequest.args
    POST = OriginalRequest.form
    params = OriginalRequest.values
    FILES = OriginalRequest.files
    
class Response(OriginalResponse):
    def write(self, value):
        self.stream.write(value)
    
class HTTPError(Exception):
    def __init__(self, errorpage=None, **kwargs):
        self.errorpage = errorpage or settings.GLOBAL.ERROR_PAGE
        self.errors = kwargs

    def __str__(self):
        return repr(self.errors)
   
def redirect(location, code=302):
    global _xhr_redirect_json, request
    
    if _xhr_redirect_json and request.is_xhr:
        response = json({'success':False, 'redirect':location}, status=500)
    else:
        response = Response(
            '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">\n'
            '<title>Redirecting...</title>\n'
            '<h1>Redirecting...</h1>\n'
            '<p>You should be redirected automatically to target URL: '
            '<a href="%s">%s</a>.  If not click the link.' %
            (cgi.escape(location), cgi.escape(location)), status=code, content_type='text/html')
        response.headers['Location'] = location
    return response

class RedirectException(Exception):
    """
    This is an exception, which can be raised in view function
    """
    def __init__(self, location, code=302):
        self.response = redirect(location, code)
        
    def get_response(self):
        return self.response
    
def Redirect(url):
    raise RedirectException(url)

def error(message='', errorpage=None, request=None, appname=None, **kwargs):
    kwargs.setdefault('message', message)
    if request:
        kwargs.setdefault('link', functions.request_url())
    raise HTTPError(errorpage, **kwargs)

def function(fname, *args, **kwargs):
    func = settings.get_var('FUNCTIONS/'+fname)
    if func:
        if args or kwargs:
            return import_attr(func)(*args, **kwargs)
        else:
            return import_attr(func)
    else:
        raise UliwebError("Can't find the function [%s] in settings" % fname)
 
def json(data, **json_kwargs):
    if 'content_type' not in json_kwargs:
        json_kwargs['content_type'] = 'application/json; charset=utf-8'
        
    if callable(data):
        @wraps(data)
        def f(*arg, **kwargs):
            ret = data(*arg, **kwargs)
            return Response(json_dumps(ret), **json_kwargs)
        return f
    else:
        return Response(json_dumps(data), **json_kwargs)
    
def jsonp(data, **json_kwargs):
    """
    jsonp is callback key name
    """
    from uliweb import request
    
    if 'jsonp' in json_kwargs:
        cb = json_kwargs.pop('jsonp')
    else:
        cb = 'callback'
        
    begin = str(request.GET.get(cb))
    if not begin:
        raise BadRequest("Can't found %s parameter in request's query_string" % cb)
    if not r_callback.match(begin):
        raise BadRequest("The callback name is not right, it can be alphabetic, number and underscore only")
    
    if callable(data):
        @wraps(data)
        def f(*arg, **kwargs):
            ret = data(*arg, **kwargs)
            return Response(begin + '(' + json_dumps(ret) + ');', **json_kwargs)
        return f
    else:
        return Response(begin + '(' + json_dumps(data) + ');', **json_kwargs)

def expose(rule=None, **kwargs):
    e = rules.Expose(rule, **kwargs)
    if e.parse_level == 1:
        return rule
    else:
        return e

def POST(rule, **kw):
    kw['methods'] = ['POST']
    return expose(rule, **kw)

def GET(rule, **kw):
    kw['methods'] = ['GET']
    return expose(rule, **kw)

def get_url_adapter(_domain_name):
    """
    Fetch a domain url_adapter object, and bind it to according domain
    """
    domain = application.domains.get(_domain_name, {})
    if domain.get('domain', ''):
        adapter = url_map.bind(domain['host'], url_scheme=domain.get('scheme', 'http'))
    else:
        adapter = url_map.bind_to_environ(request.environ)
    return adapter

def url_for(endpoint, **values):
    point = rules.get_endpoint(endpoint)
    
    #if the endpoint is string format, then find and replace
    #the module prefix with app alias which matched
    for k, v in __app_alias__.items():
        if point.startswith(k):
            point = v + point[len(k):]
            break
        
    if point in rules.__url_names__:
        point = rules.__url_names__[point]
        
    _domain_name = values.pop('_domain_name', 'default')
    _external = values.pop('_external', False)
    domain = application.domains.get(_domain_name, {})
    if not _external:
        _external = domain.get('display', False)
    adapter = get_url_adapter(_domain_name)
    return adapter.build(point, values, force_external=_external)

def get_app_dir(app):
    """
    Get an app's directory
    """
    path = __app_dirs__.get(app)
    if path is not None:
        return path
    else:
        p = app.split('.')
        try:
            path = pkg.resource_filename(p[0], '')
        except ImportError, e:
            log.error("Can't import app %s" % p[0])
            log.exception(e)
            path = ''
        if len(p) > 1:
            path = os.path.join(path, *p[1:])
        
        __app_dirs__[app] = path
        return path

def get_app_depends(app, existed_apps=None, installed_apps=None):
    installed_apps = installed_apps or []
    if existed_apps is None:
        s = set()
    else:
        s = existed_apps

    if app in s:
        raise StopIteration

    if isinstance(app, (tuple, list)):
        app, name = app
        __app_alias__[name+'.'] = app + '.'

    configfile = os.path.join(get_app_dir(app), 'config.ini')
    if os.path.exists(configfile):
        x = pyini.Ini(configfile)
        apps = x.get_var('DEPENDS/REQUIRED_APPS', [])
        for i in apps:
            if i not in s and i not in installed_apps:
                for j in get_app_depends(i, s, installed_apps):
                    yield j
    s.add(app)
    yield app
    
def set_var(key, value):
    """
    Default set_var function
    """
    from uliweb import settings
    
    settings.set_var(key, value)
    
def get_var(key, default=None):
    """
    Default get_var function
    """
    from uliweb import settings
    
    return settings.get_var(key, default)

def get_local_cache(key, creator=None):
    global local
    
    if not hasattr(local, 'local_cache'):
        local.local_cache = {}
    value = local.local_cache.get(key)
    if value:
        return value
    if callable(creator):
        value = creator()
    else:
        value = creator
    if value:
        local.local_cache[key] = value
    return value
    
def get_apps(apps_dir, include_apps=None, settings_file='settings.ini', local_settings_file='local_settings.ini'):
    include_apps = include_apps or []
    inifile = norm_path(os.path.join(apps_dir, settings_file))
    apps = []
    visited = set()
    installed_apps = []
    if not os.path.exists(apps_dir):
        return apps
    if os.path.exists(inifile):
        x = pyini.Ini(inifile)
        if x:
            installed_apps.extend(x.GLOBAL.get('INSTALLED_APPS', []))

    local_inifile = norm_path(os.path.join(apps_dir, local_settings_file))
    if os.path.exists(local_inifile):
        x = pyini.Ini(local_inifile)
        if x:
            installed_apps.extend(x.GLOBAL.get('INSTALLED_APPS', []))

    installed_apps.extend(include_apps)

    for app in installed_apps:
        apps.extend(list(get_app_depends(app, visited, installed_apps)))

    if not apps and os.path.exists(apps_dir):
        for p in os.listdir(apps_dir):
            if os.path.isdir(os.path.join(apps_dir, p)) and p not in ['.svn', 'CVS', '.git'] and not p.startswith('.') and not p.startswith('_'):
                apps.append(p)

    return apps

def collect_settings(project_dir, include_apps=None, settings_file='settings.ini', 
    local_settings_file='local_settings.ini', default_settings=None):
    
    apps_dir = os.path.join(project_dir, 'apps')
    apps = get_apps(apps_dir, None, settings_file=settings_file, local_settings_file=local_settings_file)
    settings_file = os.path.join(apps_dir, settings_file)
    local_settings_file = os.path.join(apps_dir, local_settings_file)
    settings = []
    inifile = pkg.resource_filename('uliweb.core', 'default_settings.ini')
    settings.insert(0, inifile)
    for p in apps:
        path = get_app_dir(p)
        #deal with settings
        inifile =os.path.join(get_app_dir(p), 'settings.ini')
        if os.path.exists(inifile):
            settings.append(inifile)
    
    if os.path.exists(settings_file):
        settings.append(settings_file)
    
    if os.path.exists(local_settings_file):
        settings.append(local_settings_file)
    return settings

def get_settings(project_dir, include_apps=None, settings_file='settings.ini', 
    local_settings_file='local_settings.ini', default_settings=None):
        
    settings = collect_settings(project_dir, include_apps, settings_file,
        local_settings_file, default_settings)

    x = pyini.Ini(lazy=True)
    for v in settings:
        x.read(v)
    x.update(default_settings or {})
    x.freeze()
    
    #process FILESYSTEM_ENCODING
    if not x.GLOBAL.FILESYSTEM_ENCODING:
        x.GLOBAL.FILESYSTEM_ENCODING = sys.getfilesystemencoding() or x.GLOBAL.DEFAULT_ENCODING
    return x

def is_in_web():
    return getattr(local, 'in_web', False)

class Loader(object):
    def __init__(self, tmpfilename, vars, env, dirs, notest=False):
        self.tmpfilename = tmpfilename
        self.dirs = dirs
        self.vars = vars
        self.env = env
        self.notest = notest
        
    def get_source(self, exc_type, exc_value, exc_info, tb):
        from uliweb.core.template import Template
        t = Template('', self.vars, self.env, self.dirs)
        t.set_filename(self.tmpfilename)
        use_temp_flag, filename, text = t.get_parsed_code()
        
        if exc_type is SyntaxError:
            import re
            r = re.search(r'line (\d+)', str(exc_value))
            lineno = int(r.group(1))
        else:
            lineno = tb.tb_frame.f_lineno
        return self.tmpfilename, lineno, text 
    
    def test(self, filename):
        if self.notest:
            return True
        return filename.endswith('.html')
    
class Dispatcher(object):
    installed = False
    def __init__(self, apps_dir='apps', project_dir=None, include_apps=None, 
        start=True, default_settings=None, settings_file='settings.ini', 
        local_settings_file='local_settings.ini', xhr_redirect_json=True):
            
        global _xhr_redirect_json
        
        _xhr_redirect_json = xhr_redirect_json
        __global__.application = self
        self.debug = False
        self.include_apps = include_apps or []
        self.default_settings = default_settings or {}
        self.settings_file = settings_file
        self.local_settings_file = local_settings_file
        if not Dispatcher.installed:
            self.init(project_dir, apps_dir)
            dispatch.call(self, 'startup_installed')
            self.init_urls()
            
        if start:
            dispatch.call(self, 'startup')
    
    def init(self, project_dir, apps_dir):
        if not project_dir:
            project_dir = norm_path(os.path.join(apps_dir, '..'))
        
        Dispatcher.project_dir = project_dir
        Dispatcher.apps_dir = norm_path(os.path.join(project_dir, 'apps'))
        Dispatcher.apps = get_apps(self.apps_dir, self.include_apps, self.settings_file, self.local_settings_file)
        Dispatcher.modules = self.collect_modules()
        
        self.install_settings(self.modules['settings'])
        
        #process global_objects
        self.install_global_objects()
        
        #process binds
        self.install_binds()
        
        dispatch.call(self, 'after_init_settings')
        
        Dispatcher.settings = settings
        
        #process domains
        self.process_domains(settings)
        
        #setup log
        self.set_log()
        
        #set app rules
        rules.set_app_rules(dict(settings.get('URL', {})))
        
        Dispatcher.env = self._prepare_env()
        Dispatcher.template_dirs = self.get_template_dirs()
        Dispatcher.template_processors = {}
        self.install_template_processors()
        
        #begin to start apps
        self.install_apps()
        dispatch.call(self, 'after_init_apps')
        #process views
        self.install_views(self.modules['views'])
        #process exposes
        self.install_exposes()
        #process middlewares
        Dispatcher.middlewares = self.install_middlewares()
        
        self.debug = settings.GLOBAL.get('DEBUG', False)
        dispatch.call(self, 'prepare_default_env', Dispatcher.env)
        Dispatcher.default_template = pkg.resource_filename('uliweb.core', 'default.html')
        
        Dispatcher.installed = True
        
    def _prepare_env(self):
        env = Storage({})
        env['url_for'] = url_for
        env['redirect'] = redirect
        env['Redirect'] = Redirect
        env['error'] = error
        env['application'] = self
        env['settings'] = settings
        env['json'] = json
        env['jsonp'] = jsonp
        return env
    
    def set_log(self):
        import logging
        
        s = self.settings
        
        def _get_level(level):
            return getattr(logging, level.upper())
        
        #get basic configuration
        config = {}
        for k, v in s.LOG.items():
            if k in ['format', 'datefmt', 'filename', 'filemode']:
                config[k] = v
                
        if s.get_var('LOG/level'):
            config['level'] = _get_level(s.get_var('LOG/level'))
        logging.basicConfig(**config)
        
        if config.get('filename'):
            Handler = 'logging.FileHandler'
            if config.get('filemode'):
                _args =(config.get('filename'), config.get('filemode'))
            else:
                _args = (config.get('filename'),)
        else:
            Handler = 'logging.StreamHandler'
            _args = ()
        
        #process formatters
        formatters = {}
        for f, v in s.get_var('LOG.Formatters', {}).items():
            formatters[f] = logging.Formatter(v)
            
        #process handlers
        handlers = {}
        for h, v in s.get_var('LOG.Handlers', {}).items():
            handler_cls = v.get('class', Handler)
            handler_args = v.get('args', _args)
            
            handler = import_attr(handler_cls)(*handler_args)
            if v.get('level'):
                handler.setLevel(_get_level(v.get('level')))
            
            format = v.get('format')
            if format in formatters:
                handler.setFormatter(formatters[format])
            elif format:
                fmt = logging.Formatter(format)
                handler.setFormatter(fmt)
                
            handlers[h] = handler
            
        #process loggers
        for logger_name, v in s.get_var('LOG.Loggers', {}).items():
            if logger_name == 'ROOT':
                log = logging.getLogger('')
            else:
                log = logging.getLogger(logger_name)
                
            if v.get('level'):
                log.setLevel(_get_level(v.get('level')))
            if 'propagate' in v:
                log.propagate = v.get('propagate')
            if 'handlers' in v:
                for h in v['handlers']:
                    if h in handlers:
                        log.addHandler(handlers[h])
                    else:
                        raise UliwebError("Log Handler %s is not defined yet!")
                        sys.exit(1)
            elif 'format' in v:
                if v['format'] not in formatters:
                    fmt = logging.Formatter(v['format'])
                else:
                    fmt = formatters[v['format']]
                _handler = import_attr(Handler)(*_args)
                _handler.setFormatter(fmt)
                log.addHandler(_handler)
                
    def process_domains(self, settings):
        from urlparse import urlparse

        Dispatcher.domains = {}
        
        for k, v in settings.DOMAINS.items():
            _domain = urlparse(v['domain'])
            self.domains[k] = {'domain':v.get('domain'), 'domain_parse':_domain, 
                'host':_domain.netloc,
                'scheme':_domain.scheme or 'http', 'display':v.get('display', False)}
        
    def get_file(self, filename, dir='static'):
        """
        get_file will search from apps directory
        """
        if os.path.exists(filename):
            return filename
        dirs = self.apps
        if dir:
            fname = os.path.join(dir, filename)
        else:
            fname = filename
        for d in reversed(dirs):
            path = pkg.resource_filename(d, fname)
            if os.path.exists(path):
                return path
        return None
    
    def get_template_processor(self, filename):
        ext = os.path.splitext(filename)[1]
        if ext in self.template_processors:
            return self.template_processors[ext]['func'], self.template_processors[ext]['args']
        else:
            return template.template_file, {}

    def template(self, filename, vars=None, env=None, dirs=None, default_template=None):
        vars = vars or {}
        dirs = dirs or self.template_dirs
        env = env or self.get_view_env()
        
        func, kwargs = self.get_template_processor(filename)
        
        if self.debug:
            def _compile(code, filename, action, env, Loader=Loader):
                env['__loader__'] = Loader(filename, vars, env, dirs, notest=True)
                try:
                    return compile(code, filename, 'exec')
                except:
#                    file('out.html', 'w').write(code)
                    raise
            
            return func(filename, vars, env, dirs, default_template, compile=_compile, **kwargs)
        else:
            return func(filename, vars, env, dirs, default_template, **kwargs)
    
    def render_text(self, text, vars=None, env=None, dirs=None, default_template=None):
        vars = vars or {}
        env = env or self.get_view_env()
        dirs = dirs or self.template_dirs
        
        return template.template(text, vars, env, dirs, default_template)
    
    def render(self, templatefile, vars, env=None, dirs=None, default_template=None, content_type='text/html', status=200):
        return Response(self.template(templatefile, vars, env, dirs, default_template=default_template), status=status, content_type=content_type)
    
    def _page_not_found(self, description=None, **kwargs):
        description = 'The requested URL "{{=url}}" was not found on the server.'
        text = """<h1>Page Not Found</h1>
    <p>%s</p>
    <h3>Current URL Mapping is</h3>
    <table border="1">
    <tr><th>#</th><th>URL</th><th>View Functions</th></tr>
    {{for i, (url, methods, endpoint) in enumerate(urls):}}
    <tr><td>{{=i+1}}</td><td>{{=url}} {{=methods}}</td><td>{{=endpoint}}</td></tr>
    {{pass}}
    </table>
    """ % description
        return Response(template.template(text, kwargs), status=404, content_type='text/html')
        
    def not_found(self, e):
        if self.debug:
            urls = []
            for r in url_map.iter_rules():
                if r.methods:
                    methods = ' '.join(list(r.methods))
                else:
                    methods = ''
                urls.append((r.rule, methods, r.endpoint))
            urls.sort()
            return self._page_not_found(url=local.request.path, urls=urls)
        tmp_file = template.get_templatefile('404'+settings.GLOBAL.TEMPLATE_SUFFIX, self.template_dirs)
        if tmp_file:
            response = self.render(tmp_file, {'url':local.request.path}, status=404)
        else:
            response = e
        return response
    
    def internal_error(self, e):
        tmp_file = template.get_templatefile('500'+settings.GLOBAL.TEMPLATE_SUFFIX, self.template_dirs)
        if tmp_file:
            response = self.render(tmp_file, {'url':local.request.path}, status=500)
        else:
            response = e
        log.exception(e)
        return response
    
    def get_env(self, env=None):
        e = Storage(self.env.copy())
        if env:
            e.update(env)
        return e
    
    def prepare_request(self, request, rule):
        from uliweb.utils.common import safe_import

        endpoint = rule.endpoint
        #bind endpoint to request
        request.rule = rule
        #get handler
        _klass = None
        if isinstance(endpoint, (str, unicode)):
            mod, handler = safe_import(endpoint)
            if inspect.ismethod(handler):
                if not handler.im_self:    #instance method
                    _klass = handler.im_class()
                else:                       #class method
                    _klass = handler.im_self()
                #if _klass is class method, then the mod should be Class
                #so the real mod should be mod.__module__
                mod = sys.modules[mod.__module__]
                
#            module, func = endpoint.rsplit('.', 1)
#            #if the module contains a class name, then import the class
#            #it set by expose()
#            x, last = module.rsplit('.', 1)
#            if last.startswith('views'):
#                mod = __import__(module, {}, {}, [''])
#                handler = getattr(mod, func)
#            else:
#                module = x
#                mod = __import__(module, {}, {}, [''])
#                _klass = getattr(mod, last)()
#                handler = getattr(_klass, func)
        elif callable(endpoint):
            handler = endpoint
            mod = sys.modules[handler.__module__]
        
        request.appname = ''
        for p in self.apps:
            t = p + '.'
            if handler.__module__.startswith(t):
                request.appname = p
                break
        request.function = handler.__name__
        if _klass:
            request.view_class = _klass.__class__.__name__
            handler = getattr(_klass, handler.__name__)
        else:
            request.view_class = None
        return mod, _klass, handler
    
    def call_view(self, mod, cls, handler, request, response=None, wrap_result=None, args=None, kwargs=None):
        #get env
        wrap = wrap_result or self.wrap_result
        env = self.get_view_env()
        
        #if there is __begin__ then invoke it, if __begin__ return None, it'll
        #continue running
        
        #there is a problem about soap view, because soap view will invoke
        #call_view again, so that it may cause the __begin__ or __end__ be called
        #twice, so I'll remember the function in cache, so that they'll not be invoke
        #twice
        
        def _get_name(mod, name):
            if isinstance(mod, types.ModuleType):
                return mod.__name__ + '.' + name
            else:
                return cls.__module__ + '.' + cls.__class__.__name__ + '.' + name
            
        def _process_begin(mod):
            name = '__begin__'
            if hasattr(mod, name):
                _name = _get_name(mod, name)
                if _name not in request._invokes['begin']:
                    request._invokes['begin'].append(_name)
                    f = getattr(mod, name)
                    return self._call_function(f, request, response, env)
                    
        def _prepare_end(mod):
            name = '__end__'
            if hasattr(mod, name):
                _name = _get_name(mod, name)
                if _name not in request._invokes['end']:
                    request._invokes['end'].append(_name)
                    return True
            
        def _process_end(mod):
            f = getattr(mod, '__end__')
            return self._call_function(f, request, response, env)
            
                
        if not hasattr(request, '_invokes'):
            request._invokes = {'begin':[], 'end':[]}
            
        result = _process_begin(mod)
        if result is not None:
            return wrap(handler, result, request, response, env)
        
        result = _process_begin(cls)
        if result is not None:
            return wrap(handler, result, request, response, env)
        
        #preprocess __end__
        mod_end = _prepare_end(mod)
        cls_end = _prepare_end(cls)
        
        result = self.call_handler(handler, request, response, env, wrap, args, kwargs)

        if mod_end:
            result1 = _process_end(mod)
            if result1 is not None:
                return wrap(handler, result1, request, response, env)
        
        if cls_end:
            result1 = _process_end(cls)
            if result1 is not None:
                return wrap(handler, result1, request, response, env)

        return result
        
    def wrap_result(self, handler, result, request, response, env):
#        #process ajax invoke, return a json response
#        if request.is_xhr and isinstance(result, dict):
#            result = json(result)

        if isinstance(result, dict):
            result = Storage(result)
            if hasattr(response, 'template'):
                tmpfile = response.template
            else:
                args = handler.func_dict.get('__template__')
                if not args:
                    args = {'function':request.function, 'view_class':request.view_class, 'appname':request.appname}
                    
                if isinstance(args, dict):
                    #TEMPLATE_TEMPLATE should be two elements tuple or list, the first one will be used for view_class is not empty
                    #and the second one will be used for common functions
                    if request.view_class:
                        tmpfile = settings.GLOBAL.TEMPLATE_TEMPLATE[0] % args + settings.GLOBAL.TEMPLATE_SUFFIX
                    else:
                        tmpfile = settings.GLOBAL.TEMPLATE_TEMPLATE[1] % args + settings.GLOBAL.TEMPLATE_SUFFIX
                else:
                    tmpfile = args
                response.template = tmpfile
            content_type = response.content_type
            
            #if debug mode, then display a default_template
            if self.debug:
                d = ['default.html', self.default_template]
            else:
                d = None
            response.write(self.template(tmpfile, result, env, default_template=d))
        elif isinstance(result, (str, unicode)):
            response.write(result)
        elif isinstance(result, (Response, BaseResponse)):
            response = result
        #add generator support 2014-1-8
        elif isinstance(result, types.GeneratorType):
            return Response(result, direct_passthrough=True, content_type='text/html;charset=utf-8')
        else:
            response = Response(str(result), content_type='text/html')
        return response
    
    def get_view_env(self):
        #prepare local env
        local_env = {}
        
        #process before view call
        dispatch.call(self, 'prepare_view_env', local_env)
        
        local_env['application'] = __global__.application
        local_env['request'] = local.request
        local_env['response'] = local.response
        local_env['url_for'] = url_for
        local_env['redirect'] = redirect
        local_env['Redirect'] = Redirect
        local_env['error'] = error
        local_env['settings'] = __global__.settings
        local_env['json'] = json
        local_env['function'] = function
        local_env['functions'] = functions
        local_env['json_dumps'] = json_dumps
        
        return self.get_env(local_env)
       
    def _call_function(self, handler, request, response, env, args=None, kwargs=None):
        
        for k, v in env.items():
            handler.func_globals[k] = v
        
        handler.func_globals['env'] = env
        
        args = args or ()
        kwargs = kwargs or {}
        result = handler(*args, **kwargs)
        if isinstance(result, LocalProxy) and result._obj_name == 'response':
            result = local.response
        return result
    
    def call_handler(self, handler, request, response, env, wrap_result=None, args=None, kwargs=None):
        wrap = wrap_result or self.wrap_result
        result = self._call_function(handler, request, response, env, args, kwargs)
        return wrap(handler, result, request, response, env)
            
    def collect_modules(self, check_view=True):
        modules = {}
        views = set()
        settings = []

        inifile = pkg.resource_filename('uliweb.core', 'default_settings.ini')
        settings.insert(0, inifile)
        
        def enum_views(views_path, appname, subfolder=None, pattern=None):
            if not os.path.exists(views_path):
                log.error("Can't found the app %s path, please check if the path is right" % appname)
                return
                 
            for f in os.listdir(views_path):
                fname, ext = os.path.splitext(f)
                if os.path.isfile(os.path.join(views_path, f)) and ext in ['.py', '.pyc', '.pyo'] and fname!='__init__':
                    if pattern:
                        import fnmatch
                        if not fnmatch.fnmatch(f, pattern):
                            continue
                    if subfolder:
                        views.add('.'.join([appname, subfolder, fname]))
                    else:
                        views.add('.'.join([appname, fname]))

        for p in self.apps:
            path = get_app_dir(p)
            #deal with views
            if check_view:
                views_path = os.path.join(path, 'views')
                if os.path.exists(views_path) and os.path.isdir(views_path):
                    enum_views(views_path, p, 'views')
                else:
                    enum_views(path, p, pattern='views*')
            #deal with settings
            inifile =os.path.join(get_app_dir(p), 'settings.ini')
            
            if os.path.exists(inifile):
                settings.append(inifile)

        set_ini = os.path.join(self.apps_dir, self.settings_file)
        if os.path.exists(set_ini):
            settings.append(set_ini)
        
        local_set_ini = os.path.join(self.apps_dir, self.local_settings_file)
        if os.path.exists(local_set_ini):
            settings.append(local_set_ini)
        
        modules['views'] = list(views)
        modules['settings'] = settings
        return modules
    
    def install_views(self, views):
        for v in views:
            try:
                myimport(v)
            except Exception, e:
                log.exception(e)
         
    def init_urls(self):
        #initialize urls
        for v in rules.merge_rules():
            appname, endpoint, url, kw = v
            static = kw.pop('static', None)
            if static:
                static_views.append(endpoint)
            try:
                rules.add_rule(url_map, url, endpoint, **kw)
            except:
                log.error("Wrong url url=%s, endpoint=%s" % (url, endpoint))
                raise
    
    def install_apps(self):
        for p in self.apps:
            try:
                myimport(p)
            except ImportError, e:
                pass
            except BaseException, e:
                log.exception(e)
            
    def install_template_processors(self):
        for v in settings.TEMPLATE_PROCESSORS.values():
            for ext in v.get('file_exts', []):
                self.template_processors[ext] = {'func':import_attr(v['processor']), 'args':v.get('args', {})}
        
    def install_settings(self, s):
#        settings = pyini.Ini()
        for v in s:
            settings.read(v)
        settings.update(self.default_settings)
        settings.freeze()
        
        #process FILESYSTEM_ENCODING
        if not settings.GLOBAL.FILESYSTEM_ENCODING:
            settings.GLOBAL.FILESYSTEM_ENCODING = sys.getfilesystemencoding() or settings.GLOBAL.DEFAULT_ENCODING
            
    def install_global_objects(self):
        """
        Process [GLOBAL_OBJECTS], and inject all object to uliweb module, so
        user can import from uliweb
        """
        import uliweb
        for k, v in settings.GLOBAL_OBJECTS.items():
            setattr(uliweb, k, import_attr(v))
        
    def install_binds(self):
        #process DISPATCH hooks
        #BINDS format
        #func = topic              #bind_name will be the same with function
        #bind_name = topic, func        
        #bind_name = topic, func, {args}
        d = settings.get('BINDS', {})
        for bind_name, args in d.items():
            if not args:
                continue
            is_wrong = False
            if isinstance(args, (tuple, list)):
                if len(args) == 2:
                    dispatch.bind(args[0])(args[1])
                elif len(args) == 3:
                    if not isinstance(args[2], dict):
                        is_wrong = True
                    else:
                        dispatch.bind(args[0], **args[2])(args[1])
                else:
                    is_wrong = True
            elif isinstance(args, (str, unicode)):
                dispatch.bind(args)(bind_name)
            else:
                is_wrong = True
            if is_wrong:
                log.error('BINDS definition should be "function=topic" or "bind_name=topic, function" or "bind_name=topic, function, {"args":value1,...}"')
                raise UliwebError('BINDS definition [%s=%r] is not right' % (bind_name, args))
                
    def install_exposes(self):
        #EXPOSES format
        #endpoint = topic              #bind_name will be the same with function
        #expose_name = topic, func        
        #expose_name = topic, func, {args}
        d = settings.get('EXPOSES', {})
        for name, args in d.items():
            if not args:
                continue
            is_wrong = False
            if isinstance(args, (tuple, list)):
                if len(args) == 2:
                    expose(args[0], name=name)(args[1])
                elif len(args) == 3:
                    if not isinstance(args[2], dict):
                        is_wrong = True
                    else:
                        expose(args[0], name=name, **args[2])(args[1])
                else:
                    is_wrong = True
            elif isinstance(args, (str, unicode)):
                expose(args)(name)
            else:
                is_wrong = True
            if is_wrong:
                log.error('EXPOSES definition should be "endpoint=url" or "name=url, endpoint" or "name=url, endpoint, {"args":value1,...}"')
                raise UliwebError('EXPOSES definition [%s=%r] is not right' % (name, args))
       
    def install_middlewares(self):
        return self.sort_middlewares(settings.get('MIDDLEWARES', {}).values())
    
    def sort_middlewares(self, middlewares):
        #middleware process
        #middleware can be defined as
        #middleware_name = middleware_class_path[, order]
        #middleware_name = <empty> will be skip
        m = []
        for v in middlewares:
            if not v:
                continue
            
            order = None
            if isinstance(v, (list, tuple)):
                if len(v) > 2:
                    raise UliwebError('Middleware %r difinition is not right' % v)
                middleware_path = v[0]
                if len(v) == 2:
                    order = v[1]
            else:
                middleware_path = v
            cls = import_attr(middleware_path)
            
            if order is None:
                order = getattr(cls, 'ORDER', 500)
            m.append((order, cls))
        
        m.sort(cmp=lambda x, y: cmp(x[0], y[0]))
            
        return [x[1] for x in m]
    
    def get_template_dirs(self):
        """
        Get templates directory from apps, but in reversed order, so the same named template
        file will be overrided by latter defined app
        """
        def if_not_empty(dir):
            if not os.path.exists(dir):
                return
            for root, dirs, files in os.walk(dir):
                if dirs:
                    return True
                for f in files:
                    if f != 'readme.txt':
                        return True
                    
        template_dirs = [os.path.join(self.project_dir, x) for x in settings.GLOBAL.TEMPLATE_DIRS or []]
        for p in reversed(self.apps):
            path = os.path.join(get_app_dir(p), 'templates')
            if if_not_empty(path):
                template_dirs.append(path)
                
        return template_dirs
    
    def get_templateplugins_dirs(self):
        return [os.path.join(get_app_dir(p), 'template_plugins') for p in self.apps]
    
    def open(self, *args, **kwargs):
        from werkzeug.test import EnvironBuilder
        
        pre_call = kwargs.pop('pre_call', None)
        post_call = kwargs.pop('post_call', None)
        middlewares = kwargs.pop('middlewares', [])
        if middlewares is not None:
            m = self.sort_middlewares(middlewares)
        else:
            m = self.middlewares
        
        builder = EnvironBuilder(*args, **kwargs)
        try:
            environ = builder.get_environ()
        finally:
            builder.close()
            
        return self._open(environ, pre_call=pre_call, post_call=post_call, middlewares=m)
        
    def _open(self, environ, pre_call=None, post_call=None, middlewares=None):
        if middlewares is None:
            middlewares = self.middlewares
            
        local.request = req = Request(environ)
        local.response = res = Response(content_type='text/html')
        #add local cached
        local.local_cache = {}
        #add in web flag
        local.in_web = True
        
        url_adapter = get_url_adapter('default')
        try:
            rule, values = url_adapter.match(return_rule=True)
            mod, handler_cls, handler = self.prepare_request(req, rule)
            
            #process static
            if rule.endpoint in static_views:
                response = self.call_view(mod, handler_cls, handler, req, res, kwargs=values)
            else:
                response = None
                _clses = {}
                _inss = {}
                for cls in middlewares:
                    if hasattr(cls, 'process_request'):
                        ins = cls(self, settings)
                        _inss[cls] = ins
                        response = ins.process_request(req)
                        if response is not None:
                            break
                
                if response is None:
                    try:
                        if pre_call:
                            response = pre_call(req)
                        if response is None:
                            try:
                                response = self.call_view(mod, handler_cls, handler, req, res, kwargs=values)
                            except RedirectException as e:
                                response = e.get_response()
                        if post_call:
                            response = post_call(req, response)
                    except Exception, e:
                        for cls in reversed(middlewares):
                            if hasattr(cls, 'process_exception'):
                                ins = _inss.get(cls)
                                if not ins:
                                    ins = cls(self, settings)
                                response = ins.process_exception(req, e)
                                if response:
                                    break
                        raise
                    
                for cls in reversed(middlewares):
                    if hasattr(cls, 'process_response'):
                        ins = _inss.get(cls)
                        if not ins:
                            ins = cls(self, settings)
                        response = ins.process_response(req, response)
                        
                        if not isinstance(response, (OriginalResponse, Response)):
                            raise Exception("Middleware %s should return an Response object, but %r found" % (ins.__class__.__name__, response))
                
                #process post_response call, you can set some async process in here
                #but the sync may fail, so you should think about the checking mechanism
                if hasattr(response, 'post_response') and response.post_response:
                    response.post_response()
                    
                if hasattr(res, 'post_response') and res.post_response:
                    res.post_response()
                
            #endif
            
        except HTTPError, e:
            response = self.render(e.errorpage, Storage(e.errors))
        except NotFound, e:
            response = self.not_found(e)
        except HTTPException, e:
            response = e
        except Exception, e:
            if not self.settings.get_var('GLOBAL/DEBUG'):
                response = self.internal_error(e)
            else:
#                log.exception(e)
                raise
        finally:
            local.local_cache = {}
            local.in_web = False
        return response
    
    def handler(self):
        return DispatcherHandler(self)

    def __call__(self, environ, start_response):
        response = self._open(environ)
        return response(environ, start_response)
            
class DispatcherHandler(object):
    def __init__(self, application):
        self.application = application
        
    def open(self, *args, **kw):
        return self.application.open(*args, **kw)
        
    def get(self, *args, **kw):
        """Like open but method is enforced to GET."""
        kw['method'] = 'GET'
        return self.open(*args, **kw)
    
    def patch(self, *args, **kw):
        """Like open but method is enforced to PATCH."""
        kw['method'] = 'PATCH'
        return self.open(*args, **kw)
    
    def post(self, *args, **kw):
        """Like open but method is enforced to POST."""
        kw['method'] = 'POST'
        return self.open(*args, **kw)
    
    def head(self, *args, **kw):
        """Like open but method is enforced to HEAD."""
        kw['method'] = 'HEAD'
        return self.open(*args, **kw)
    
    def put(self, *args, **kw):
        """Like open but method is enforced to PUT."""
        kw['method'] = 'PUT'
        return self.open(*args, **kw)
    
    def delete(self, *args, **kw):
        """Like open but method is enforced to DELETE."""
        kw['method'] = 'DELETE'
        return self.open(*args, **kw)

response = LocalProxy(local, 'response', Response)
request = LocalProxy(local, 'request', Request)
settings = LocalProxy(__global__, 'settings', pyini.Ini)
application = LocalProxy(__global__, 'application', Dispatcher)
