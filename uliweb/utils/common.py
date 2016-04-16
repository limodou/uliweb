import os, sys
import re
import logging
import cPickle

log = logging
class _Default(object): pass

def safe_import(path):
    module = path.split('.')
    g = __import__(module[0], fromlist=['*'])
    s = [module[0]]
    for i in module[1:]:
        mod = g
        if hasattr(mod, i):
            g = getattr(mod, i)
        else:
            s.append(i)
            g = __import__('.'.join(s), fromlist=['*'])
    return mod, g
        
def import_mod_attr(path):
    """
    Import string format module, e.g. 'uliweb.orm' or an object
    return module object and object
    """
    import inspect

    if isinstance(path, (str, unicode)):
        v = path.split(':')
        if len(v) == 1:
            module, func = path.rsplit('.', 1)
        else:
            module, func = v
        mod = __import__(module, fromlist=['*'])
        f = mod
        for x in func.split('.'):
            try:
                f = getattr(f, x)
            except:
                raise AttributeError("Get %s attribute according %s error" % (x, path))
    else:
        f = path
        mod = inspect.getmodule(path)
    return mod, f

def import_attr(func):
    mod, f = import_mod_attr(func)
    return f

def myimport(module):
    mod = __import__(module, fromlist=['*'])
    return mod

def install(packages):
    from pkg_resources import load_entry_point
    
    load = load_entry_point('setuptools', 'console_scripts', 'easy_install')
    load(packages)

class MyPkg(object):
    @staticmethod
    def resource_filename(module, path):
        mod = myimport(module)
        p = os.path.dirname(mod.__file__)
        if path:
            return os.path.join(p, path)
        else:
            return p
    
    @staticmethod
    def resource_listdir(module, path):
        d = MyPkg.resource_filename(module, path)
        return os.listdir(d)
    
    @staticmethod
    def resource_isdir(module, path):
        d = MyPkg.resource_filename(module, path)
        return os.path.isdir(d)

try:
    import pkg_resources as pkg
except:
    pkg = MyPkg

def extract_file(module, path, dist, verbose=False, replace=True):
    outf = os.path.join(dist, os.path.basename(path))
#    d = pkg.get_distribution(module)
#    if d.has_metadata('zip-safe'):
#        f = open(outf, 'wb')
#        f.write(pkg.resource_string(module, path))
#        f.close()
#        if verbose:
#            print 'Info : Extract %s/%s to %s' % (module, path, outf)
#    else:
    import shutil

    inf = pkg.resource_filename(module, path)
    sfile = os.path.basename(inf)
    if os.path.isdir(dist):
        dfile = os.path.join(dist, sfile)
    else:
        dfile = dist
    f = os.path.exists(dfile)
    if replace or not f:
        shutil.copy2(inf, dfile)
        if verbose:
            print 'Copy %s to %s' % (inf, dfile)
  
def extract_dirs(mod, path, dst, verbose=False, exclude=None, exclude_ext=None, recursion=True, replace=True):
    """
    mod name
    path mod path
    dst output directory
    resursion True will extract all sub module of mod
    """
    default_exclude = ['.svn', '_svn', '.git']
    default_exclude_ext = ['.pyc', '.pyo', '.bak', '.tmp']
    exclude = exclude or []
    exclude_ext = exclude_ext or []
#    log = logging.getLogger('uliweb')
    if not os.path.exists(dst):
        os.makedirs(dst)
        if verbose:
            print 'Make directory %s' % dst
    for r in pkg.resource_listdir(mod, path):
        if r in exclude or r in default_exclude:
            continue
        fpath = os.path.join(path, r)
        if pkg.resource_isdir(mod, fpath):
            if recursion:
                extract_dirs(mod, fpath, os.path.join(dst, r), verbose, exclude, exclude_ext, recursion, replace)
        else:
            ext = os.path.splitext(fpath)[1]
            if ext in exclude_ext or ext in default_exclude_ext:
                continue
            extract_file(mod, fpath, dst, verbose, replace)

def match(f, patterns):
    from fnmatch import fnmatch
    
    flag = False
    for x in patterns:
        if fnmatch(f, x):
            return True
        
def walk_dirs(path, include=None, include_ext=None, exclude=None,
        exclude_ext=None, recursion=True, file_only=False, use_default_pattern=True):
    """
    path directory path
    resursion True will extract all sub module of mod
    """
    default_exclude = ['.svn', '_svn', '.git']
    default_exclude_ext = ['.pyc', '.pyo', '.bak', '.tmp']
    exclude = exclude or []
    exclude_ext = exclude_ext or []
    include_ext = include_ext or []
    include = include or []

    if not os.path.exists(path):
        raise StopIteration

    for r in os.listdir(path):
        if match(r, exclude) or (use_default_pattern and r in default_exclude):
            continue
        if include and r not in include:
            continue
        fpath = os.path.join(path, r)
        if os.path.isdir(fpath):
            if not file_only:
                yield os.path.normpath(fpath).replace('\\', '/')
            if recursion:
                for f in walk_dirs(fpath, include, include_ext, exclude,
                    exclude_ext, recursion, file_only):
                    yield os.path.normpath(f).replace('\\', '/')
        else:
            ext = os.path.splitext(fpath)[1]
            if ext in exclude_ext or (use_default_pattern and ext in default_exclude_ext):
                continue
            if include_ext and ext not in include_ext:
                continue
            yield os.path.normpath(fpath).replace('\\', '/')

def copy_dir(src, dst, verbose=False, check=False, processor=None):
    import shutil

#    log = logging.getLogger('uliweb')

    def _md5(filename):
        try:
            import hashlib
            a = hashlib.md5()
        except ImportError:
            import md5
            a = md5.new()
            
        a.update(file(filename, 'rb').read())
        return a.digest()
    
    if not os.path.exists(dst):
        os.makedirs(dst)

    if verbose:
        print "Processing %s" % src
        
    for r in os.listdir(src):
        if r in ['.svn', '_svn', '.git']:
            continue
        fpath = os.path.join(src, r)
        
        if os.path.isdir(fpath):
            if os.path.abspath(fpath) != os.path.abspath(dst):
                copy_dir(fpath, os.path.join(dst, r), verbose, check, processor)
            else:
                continue
        else:
            ext = os.path.splitext(fpath)[1]
            if ext in ['.pyc', '.pyo', '.bak', '.tmp']:
                continue
            df = os.path.join(dst, r)
            if check:
                if os.path.exists(df):
                    a = _md5(fpath)
                    b = _md5(df)
                    if a != b:
                        print ("Error: Target file %s is already existed, and "
                            "it not same as source one %s, so copy failed" % (fpath, dst))
                else:
                    if processor:
                        if processor(fpath, dst, df):
                            continue
                    shutil.copy2(fpath, dst)
                    if verbose:
                        print "Copy %s to %s" % (fpath, dst)
                    
            else:
                if processor:
                    if processor(fpath, dst, df):
                        continue
                shutil.copy2(fpath, dst)
                if verbose:
                    print "Copy %s to %s" % (fpath, dst)

def copy_dir_with_check(dirs, dst, verbose=False, check=True, processor=None):
#    log = logging.getLogger('uliweb')

    for d in dirs:
        if not os.path.exists(d):
            continue

        copy_dir(d, dst, verbose, check, processor)

def check_apps_dir(apps_dir):
    log = logging
    if not os.path.exists(apps_dir):
        print >>sys.stderr, "[Error] Can't find the apps_dir [%s], please check it out" % apps_dir
        sys.exit(1)

def is_pyfile_exist(dir, pymodule):
    path = os.path.join(dir, '%s.py' % pymodule)
    if not os.path.exists(path):
        path = os.path.join(dir, '%s.pyc' % pymodule)
        if not os.path.exists(path):
            path = os.path.join(dir, '%s.pyo' % pymodule)
            if not os.path.exists(path):
                return False
    return True
    
def wraps(src):
    def _f(des):
        def f(*args, **kwargs):
            from uliweb import application
            if application:
                env = application.get_view_env()
                for k, v in env.iteritems():
                    src.func_globals[k] = v
                
                src.func_globals['env'] = env
            return des(*args, **kwargs)
        
        f.__name__ = src.__name__
        f.func_globals.update(src.func_globals)
        f.__doc__ = src.__doc__
        f.__module__ = src.__module__
        f.__dict__.update(src.__dict__)
        return f
    
    return _f

def timeit(func):
    log = logging.getLogger('uliweb.app')
    import time
    @wraps(func)
    def f(*args, **kwargs):
        begin = time.time()
        ret = func(*args, **kwargs)
        end = time.time()
        print ("%s.%s [%s]s" % (func.__module__, func.__name__, end-begin))
        return ret
    return f

def safe_unicode(s, encoding='utf-8'):
    from uliweb.i18n.lazystr import LazyString
    
    if isinstance(s, unicode):
        return s
    elif isinstance(s, LazyString):
        return unicode(s)
    else:
        return unicode(str(s), encoding)

def safe_str(s, encoding='utf-8'):
    from uliweb.i18n.lazystr import LazyString

    if isinstance(s, unicode):
        return s.encode(encoding)
    elif isinstance(s, LazyString):
        return unicode(s).encode(encoding)
    else:
        return str(s)

def get_var(key):
    def f():
        from uliweb import settings
        
        return settings.get_var(key)
    return f

def get_choice(choices, value, default=None):
    if callable(choices):
        choices = choices()
    return dict(choices).get(value, default)

def simple_value(v, encoding='utf-8', none=False):
    import datetime
    import decimal
    
    if callable(v):
        v = v()
    if isinstance(v, datetime.datetime):
        return v.strftime('%Y-%m-%d %H:%M:%S')
    elif isinstance(v, datetime.date):
        return v.strftime('%Y-%m-%d')
    elif isinstance(v, datetime.time):
        return v.strftime('%H:%M:%S')
    elif isinstance(v, decimal.Decimal):
        return str(v)
    elif isinstance(v, unicode):
        return v.encode(encoding)
    elif isinstance(v, (tuple, list)):
        s = []
        for x in v:
            s.append(simple_value(x, encoding, none))
        return s
    elif isinstance(v, dict):
        d = {}
        for k, v in v.iteritems():
            d[simple_value(k)] = simple_value(v, encoding, none)
        return d
    elif v is None:
        if none:
            return v
        else:
            return ''
    else:
        return v
    
re_newline = re.compile(r'\r\n|\r|\n')
def str_value(v, encoding='utf-8', bool_int=True, none='NULL', newline_escape=False):
    import datetime
    import decimal
    
    if callable(v):
        v = v()
    if isinstance(v, datetime.datetime):
        return v.strftime('%Y-%m-%d %H:%M:%S')
    elif isinstance(v, datetime.date):
        return v.strftime('%Y-%m-%d')
    elif isinstance(v, datetime.time):
        return v.strftime('%H:%M:%S')
    elif isinstance(v, decimal.Decimal):
        return str(v)
    elif isinstance(v, (str, unicode)):
        if isinstance(v, unicode):
            v = v.encode(encoding)
        if newline_escape:
            v = re_newline.sub(r'\\n', v)
        return v
    elif v is None:
        return none
    elif isinstance(v, bool):
        if bool_int:
            if v:
                return '1'
            else:
                return '0'
        else:
            return str(v)
    else:
        return str(v)

def norm_path(path):
    return os.path.normpath(os.path.abspath(path))

r_expand_path = re.compile('\$\[(\w+)\]')
def expand_path(path):
    """
    Auto search some variables defined in path string, such as:
        $[PROJECT]/files
        $[app_name]/files
    for $[PROJECT] will be replaced with uliweb application apps_dir directory
    and others will be treated as a normal python package, so uliweb will
    use pkg_resources to get the path of the package
    
    update: 0.2.5 changed from ${} to $[]

    Also apply with os.path.expandvars(os.path.expanduser(path))
    """
    from uliweb import application
    
    def replace(m):
        txt = m.groups()[0]
        if txt == 'PROJECT':
            return application.apps_dir
        else:
            return pkg.resource_filename(txt, '')
    p = re.sub(r_expand_path, replace, path)
    return os.path.expandvars(os.path.expanduser(path))

def date_in(d, dates):
    """
    compare if d in dates. dates should be a tuple or a list, for example:
        date_in(d, [d1, d2])
    and this function will execute:
        d1 <= d <= d2
    and if d is None, then return False
    """
    if not d:
        return False
    return dates[0] <= d <= dates[1]

class Serial(object):
    """
    For json protocal, datetime will convert to string, and convert reversed be 
    be not datetime
    """
    @classmethod
    def load(cls, s, protocal=None):
        import json
        
        if not protocal:
            return cPickle.loads(s)
        elif protocal == 'json':
            return json.loads(s)
        else:
            raise Exception("Can't support this protocal %s" % protocal)
    
    @classmethod
    def dump(cls, v, protocal=None):
        from uliweb import json_dumps
        
        if not protocal:
            return cPickle.dumps(v, cPickle.HIGHEST_PROTOCOL)
        elif protocal == 'json':
            return json_dumps(v)
        else:
            raise Exception("Can't support this protocal %s" % protocal)

import urlparse
class QueryString(object):
    def __init__(self, url):
        self.url = str(url)
        self.scheme, self.netloc, self.script_root, qs, self.anchor = self.parse()
        self.qs = urlparse.parse_qs(qs, True)
        
    def parse(self):
        return urlparse.urlsplit(self.url)
    
    def __getitem__(self, name):
        return self.qs.get(name, [])
    
    def __setitem__(self, name, value):
        self.qs[name] = [value]
    
    def set(self, name, value, replace=False):
        v = self.qs.setdefault(name, [])
        if replace:
            self.qs[name] = [value]
        else:
            v.append(value)
        return self

    def __str__(self):
        import urllib
        
        qs = urllib.urlencode(self.qs, True)
        return urlparse.urlunsplit((self.scheme, self.netloc, self.script_root, qs, self.anchor))
    
def query_string(url, replace=True, **kwargs):
    q = QueryString(url)
    for k, v in kwargs.items():
        q.set(k, v, replace)
    return str(q)

def camel_to_(s):
    """
    Convert CamelCase to camel_case
    """
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', s)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
def application_path(path):
    """
    Join application project_dir and path
    """
    from uliweb import application
    return os.path.join(application.project_dir, path)

def get_uuid(type=4):
    """
    Get uuid value
    """
    import uuid
    
    name = 'uuid'+str(type)
    u = getattr(uuid, name)
    return u().hex

def pretty_dict(d, leading=' ', newline='\n', indent=0, tabstop=4, process=None):
    """
    Output pretty formatted dict, for example:
        
        d = {"a":"b",
            "c":{
                "d":"e",
                "f":"g",
                }
            }
        
    will output:
        
        a : 'b'
        c : 
            d : 'e'
            f : 'g'
        
    """
    for k, v in d.items():
        if process:
            k, v = process(k, v)
        if isinstance(v, dict):
            yield '%s%s : %s' % (indent*tabstop*leading, simple_value(k), newline)
            for x in pretty_dict(v, leading=leading, newline=newline, indent=indent+1, tabstop=tabstop):
                yield x
            continue
        yield '%s%s : %s%s' % (indent*tabstop*leading, simple_value(k), simple_value(v), newline)

def request_url(req=None):
    """
    Get full url of a request
    """
    from uliweb import request
    
    r = req or request
    if request:
        if r.query_string:
            return r.path + '?' + r.query_string
        else:
            return r.path
    else:
        return ''

def flat_list(*alist):
    """
    Flat a tuple, list, single value or list of list to flat list
    e.g.
    
    >>> flat_list(1,2,3)
    [1, 2, 3]
    >>> flat_list(1)
    [1]
    >>> flat_list([1,2,3])
    [1, 2, 3]
    >>> flat_list([None])
    []
    """
    a = []
    for x in alist:
        if x is None:
            continue
        if isinstance(x, (tuple, list)):
            a.extend([i for i in x if i is not None])
        else:
            a.append(x)
    return a
    
def compare_dict(da, db):
    """
    Compare differencs from two dicts
    """
    sa = set(da.items())
    sb = set(db.items())
    
    diff = sa & sb
    return dict(sa - diff), dict(sb - diff)

def get_caller(skip=None):
    """
    Get the caller information, it'll return: module, filename, line_no
    """
    import inspect
    from fnmatch import fnmatch

    try:
        stack = inspect.stack()
    except:
        stack = [None, inspect.currentframe()]
    if len(stack) > 1:
        stack.pop(0)
        if skip and not isinstance(skip, (list, tuple)):
            skip = [skip]
        else:
            skip = []
        ptn = [os.path.splitext(s.replace('\\', '/'))[0] for s in skip]
        for frame in stack:
            #see doc: inspect
            #the frame object, the filename, the line number of the current line, 
            #the function name, a list of lines of context from the source code, 
            #and the index of the current line within that list
            if isinstance(frame, tuple):
                filename, funcname, lineno = frame[1], frame[3], frame[2]
            else:
                filename, funcname, lineno = frame.f_code.co_filename, frame.f_code.co_name, frame.f_lineno
            del frame
            found = False
            for k in ptn:
                filename = os.path.splitext(filename.replace('\\', '/'))[0]
                if fnmatch(filename, k):
                    found = True
                    break
            if not found:
                return filename, lineno, funcname

class classonlymethod(classmethod):
    """
    Use to limit the class method can only be called via class object, but not instance
    object
    
    >>> class A(object):
    ...     @classonlymethod
    ...     def p(cls):
    ...         print 'call p()'
    >>> A.p()
    call p()
    >>> a = A()
    >>> try:
    ...     a.p()        
    ... except Exception as e:
    ...     print e
    This method can only be called with class object.
    """
    def __get__(self, instance, owner):
        if instance is not None:
            raise AttributeError("This method can only be called with class object.")
        return super(classonlymethod, self).__get__(instance, owner)

def trim_path(path, length=30):
    """
    trim path to specified length, for example:
    >>> a = '/project/apps/default/settings.ini'
    >>> trim_path(a)
    '.../apps/default/settings.ini'
    
    The real length will be length-4, it'll left '.../' for output.
    """
    s = path.replace('\\', '/').split('/')
    t = -1
    for i in range(len(s)-1, -1, -1):
        t = len(s[i]) + t + 1
        if t > length-4:
            break
    return '.../' + '/'.join(s[i+1:])
  
class cached_property(object):
    """
    cached function return value
    """
    def __init__(self, func):
        self.value = _Default
        self.func = func

    def __get__(self, obj, type=None):
        value = self.value
        if self.value is _Default:
            value = self.func(type)
            self.value = value
        return value

def get_temppath(prefix, suffix='', dir=''):
    import tempfile
    return tempfile.mkdtemp(suffix=suffix, prefix=prefix, dir=dir)

def get_tempfilename2(prefix, suffix='', dir=''):
    import tempfile
    return tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=dir)

def get_tempfilename(prefix, suffix='', dir=''):
    return get_tempfilename2(prefix, suffix, dir)[1]

def get_configrable_object(key, section, cls=None):
    """
    if obj is a class, then check if the class is subclass of cls
    or it should be object path, and it'll be imported by import_attr
    """
    from uliweb import UliwebError, settings
    import inspect

    if inspect.isclass(key) and cls and issubclass(key, cls):
        return key
    elif isinstance(key, (str, unicode)):
        path = settings[section].get(key)
        if path:
            _cls = import_attr(path)
            return _cls
        else:
            raise UliwebError("Can't find section name %s in settings" % section)
    else:
        raise UliwebError("Key %r should be subclass of %r object or string path format!" % (key, cls))

def format_size(size):
    """
    Convert size to XB, XKB, XMB, XGB
    :param size: length value
    :return: string value with size unit
    """
    units = ['B', 'KB', 'MB', 'GB']
    unit = ''
    n = size
    old_n = n
    value = size
    for i in units:
        old_n = n
        x, y = divmod(n, 1024)
        if x == 0:
            unit = i
            value = y
            break

        n = x
        unit = i
        value = old_n
    return str(value)+unit

def convert_bytes(n):
    """
    Convert a size number to 'K', 'M', .etc
    """
    symbols = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
    prefix = {}
    for i, s in enumerate(symbols):
        prefix[s] = 1 << (i + 1) * 10
    for s in reversed(symbols):
        if n >= prefix[s]:
            value = float(n) / prefix[s]
            return '%.1f%s' % (value, s)
    return "%sB" % n


#if __name__ == '__main__':
#    log.info('Info: info')
#    try:
#        1/0
#    except:
#        log.exception('1/0')
