import os, sys
import re
import logging

log = logging

def safe_import(path):
    module = path.split('.')
    g = __import__(module[0], {}, {}, [''])
    for i in module[1:]:
        mod = g
        g = getattr(mod, i)
    return mod, g
        
def import_mod_attr(path):
    module, func = path.rsplit('.', 1)
    mod = __import__(module, {}, {}, [''])
    f = getattr(mod, func)
    return mod, f

def import_attr(func):
    mod, f = import_mod_attr(func)
    return f

def myimport(module):
    mod = __import__(module, {}, {}, [''])
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

def extract_file(module, path, dist, verbose=False):
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
    shutil.copy2(inf, dist)
    if verbose:
        log.info('Copy %s to %s' % (inf, dist))
  
def extract_dirs(mod, path, dst, verbose=False):
    log = logging.getLogger('uliweb.console')
    if not os.path.exists(dst):
        os.makedirs(dst)
        if verbose:
            log.info('Make directory %s' % dst)
    for r in pkg.resource_listdir(mod, path):
        if r in ['.svn', '_svn']:
            continue
        fpath = os.path.join(path, r)
        if pkg.resource_isdir(mod, fpath):
            extract_dirs(mod, fpath, os.path.join(dst, r), verbose)
        else:
            ext = os.path.splitext(fpath)[1]
            if ext in ['.pyc', '.pyo', '.bak', '.tmp']:
                continue
            extract_file(mod, fpath, dst, verbose)

def copy_dir(src, dst, verbose=False, check=False, processor=None):
    import shutil

    log = logging.getLogger('uliweb.console')

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
        log.info("Processing %s" % src)
        
    for r in os.listdir(src):
        if r in ['.svn', '_svn', '.git']:
            continue
        fpath = os.path.join(src, r)
        if os.path.isdir(fpath):
            copy_dir(fpath, os.path.join(dst, r), verbose, check, processor)
        else:
            ext = os.path.splitext(fpath)[1]
            if ext in ['.pyc', '.pyo', '.bak', '.tmp']:
                continue
            if check:
                df = os.path.join(dst, r)
                if os.path.exists(df):
                    a = _md5(fpath)
                    b = _md5(df)
                    if a != b:
                        log.error("Target file %s is already existed, and "
                            "it not same as source one %s, so copy failed" % (fpath, dst))
                else:
                    if processor:
                        if processor(fpath, dst):
                            continue
                    shutil.copy2(fpath, dst)
                    if verbose:
                        log.info("Copy %s to %s" % (fpath, dst))
                    
            else:
                if processor:
                    if processor(fpath, dst):
                        continue
                shutil.copy2(fpath, dst)
                if verbose:
                    log.info("Copy %s to %s" % (fpath, dst))

def copy_dir_with_check(dirs, dst, verbose=False, check=True, processor=None):
    log = logging.getLogger('uliweb.console')

    for d in dirs:
        if not os.path.exists(d):
            if verbose:
                log.warn("%s does not exist, SKIP" % d)
            continue

        copy_dir(d, dst, verbose, check, processor)

def check_apps_dir(apps_dir):
    log = logging.getLogger('uliweb.console')
    if not os.path.exists(apps_dir):
        log.error("Can't find the apps_dir [%s], please check it out", apps_dir)
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

def sort_list(alist, default=500, duplicate=False):
    """
    Sort a list, each element could be a tuple (order, value) or just a value
    for example:
        ['abc', (50, 'cde')]
    you can put a default argument to it, if there is no order of a element, then
    the order of this element will be the default value.
    All elements will be sorted according the order value, and the same order
    value elements will be sorted in the definition of the element
    
    if duplicate is True:
        will remove the duplicated keys
    
    >>> sort_list(['a', 'c', 'b'])
    ['a', 'c', 'b']
    >>> sort_list([(100, 'a'), 'c', 'd', (50, 'b')])
    ['b', 'a', 'c', 'd']
    >>> sort_list([(100, 'a'), (100, 'c'), 'd', (100, 'b')])
    ['a', 'c', 'b', 'd']
    >>> sort_list([(100, 'a'), (100, 'c'), 'd', (100, 'b'), (200, 'a')])
    ['c', 'b', 'a', 'd']
    """
    d = {}
    for v in alist:
        if isinstance(v, (tuple, list)):
            n, s = v[0], v[1]
        else:
            n, s = default, v
        p = d.setdefault(n, [])
        if duplicate:
            p.append(s)
        else:
            for v in d.values():
                if s in v:
                    v.remove(s)
                    break
            p.append(s)
    t = []
    for k in sorted(d.keys()):
        t.extend(d[k])
    return t

def timeit(func):
    log = logging.getLogger('uliweb.app')
    import time
    @wraps(func)
    def f(*args, **kwargs):
        begin = time.time()
        ret = func(*args, **kwargs)
        end = time.time()
        log.info("%s.%s [%s]s" % (func.__module__, func.__name__, end-begin))
        return ret
    return f

def safe_unicode(s, encoding='utf-8'):
    if isinstance(s, unicode):
        return s
    else:
        return unicode(s, encoding)

def safe_str(s, encoding='utf-8'):
    if isinstance(s, unicode):
        return s.encode(encoding)
    else:
        return s

def get_var(key):
    def f():
        from uliweb import settings
        
        return settings.get_var(key)
    return f

def get_choice(choices, value):
    if callable(choices):
        choices = choices()
    return dict(choices).get(value, '')

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
    
def str_value(v, encoding='utf-8', bool_int=True, none='NULL'):
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

__caches__ = {}
def cache_get(key, func, _type='default'):
    global __caches__
    v = __caches__.setdefault(_type, {})
    if key in v and v[key]:
        return v[key]
    else:
        v[key] = func(key)
        return v[key]
    
def norm_path(path):
    return os.path.normcase(os.path.abspath(path))

r_expand_path = re.compile('\$\{(\w+)\}')
def expand_path(path):
    """
    Auto search some variables defined in path string, such as:
        ${PROJECT}/files
        ${app_name}/files
    for ${PROJECT} will be replaced with uliweb application apps_dir directory
    and others will be treated as a normal python package, so uliweb will
    use pkg_resources to get the path of the package
    """
    from uliweb import application
    
    def replace(m):
        txt = m.groups()[0]
        if txt == 'PROJECT':
            return application.apps_dir
        else:
            return pkg.resource_filename(txt, '')
    return re.sub(r_expand_path, replace, path)

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

#if __name__ == '__main__':
#    log.info('Info: info')
#    try:
#        1/0
#    except:
#        log.exception('1/0')
