"""
Compatible with py2 and py3, inspired by jinjin2, future, etc

common types & functions:

    name         2.x             3.x
    ------------ -----------     -----------
    unichr       unichr          chr
    unicode      unicode         str
    range        xrange          range
    string_types (str, unicode)  (str, )
    pickle       cPickle         pickle
    input        raw_input       input

StingIO, BytesIO

from io import StringIO, BytesIO

"""
import sys

PY3 = sys.version_info[0] == 3
PY2 = sys.version_info[0] == 2
PY26 = sys.version_info[0:2] == (2, 6)
PYPY = hasattr(sys, 'pypy_translation_info')
_identity = lambda x:x

if not PY2:
    unichr = chr
    range = range
    string_types = (str,)

    iterkeys = lambda d: iter(d.keys())
    itervalues = lambda d: iter(d.values())
    iteritems = lambda d: iter(d.items())

    import pickle

    def reraise(tp, value, tb=None):
        if value.__traceback__ is not tb:
            raise value.with_traceback(tb)
        raise value

    implements_iterator = _identity
    python_2_unicode_compatible = _identity

    ifilter = filter
    imap = map
    izip = zip

    def u(s, encoding='utf8'):
        if isinstance(s, str):
            return s
        else:
            return str(s)

    def b(s, encoding='utf8'):
        if isinstance(s, bytes):
            return s
        else:
            if isinstance(s, str):
                return s.encode(encoding)
            else:
                return bytes(s)

    import builtins
    exec_ = getattr(builtins, "exec")

    get_next = lambda x: x.next

    input = input
    open = open

else:
    unichr = unichr
    range = xrange
    string_types = (str, unicode)

    iterkeys = lambda d: d.iterkeys()
    itervalues = lambda d: d.itervalues()
    iteritems = lambda d: d.iteritems()

    import cPickle as pickle
    from io import BytesIO, StringIO

    exec('def reraise(tp, value, tb=None):\n raise tp, value, tb')

    from itertools import imap, izip, ifilter

    def implements_iterator(cls):
        cls.next = cls.__next__
        del cls.__next__
        return cls

    def python_2_unicode_compatible(cls):
        cls.__unicode__ = cls.__str__
        cls.__str__ = lambda x: x.__unicode__().encode('utf-8')
        return cls

    def u(s, encoding='utf8'):
        if isinstance(s, unicode):
            return s
        else:
            return unicode(str(s), encoding)

    def b(s, encoding='utf8'):
        if isinstance(s, unicode):
            return s.decode(encoding)
        else:
            return str(s)

    def exec_(code, globs=None, locs=None):
        """Execute code in a namespace."""
        if globs is None:
            frame = sys._getframe(1)
            globs = frame.f_globals
            if locs is None:
                locs = frame.f_locals
            del frame
        elif locs is None:
            locs = globs
        exec("""exec code in globs, locs""")

    get_next = lambda x: x.__next__

    input = raw_input

    from io import open

try:
    next = next
except NameError:
    def next(it):
        return it.next()


def with_metaclass(meta, *bases):
    # This requires a bit of explanation: the basic idea is to make a
    # dummy metaclass for one level of class instanciation that replaces
    # itself with the actual metaclass.  Because of internal type checks
    # we also need to make sure that we downgrade the custom metaclass
    # for one level to something closer to type (that's why __call__ and
    # __init__ comes back from type etc.).
    #
    # This has the advantage over six.with_metaclass in that it does not
    # introduce dummy classes into the final MRO.
    class metaclass(meta):
        __call__ = type.__call__
        __init__ = type.__init__
        def __new__(cls, name, this_bases, d):
            if this_bases is None:
                return type.__new__(cls, name, (), d)
            return meta(name, bases, d)
    return metaclass('temporary_class', None, {})

modules_mapping = {
    'socketserver':'SocketServer',
    'queue':'Queue',
    'configparser':'ConfigParser',

    'html.entities':'htmlentitydefs',
    'html.parser':'HTMLParser',

    'http.client':'httplib',
    'http.server':['BaseHTTPServer', 'CGIHTTPServer', 'SimpleHTTPServer', 'CGIHTTPServer'],

        # from BaseHTTPServer
        # from CGIHTTPServer
        # from SimpleHTTPServer
        # from CGIHTTPServer

    'http.cookies':'Cookie',
    'http.cookiejar':'cookielib',

    'urllib.parse':{'urlparse':['ParseResult', 'SplitResult',
                                'parse_qs', 'parse_qsl',
                                'urldefrag', 'urljoin',
                                'urlparse', 'urlsplit',
                                'urlunparse', 'urlunsplit'],
                    'urllib':['quote', 'quote_plus',
                              'unquote', 'unquote_plus',
                              'urlencode', 'splitquery']},

        # from urlparse import (ParseResult, SplitResult, parse_qs, parse_qsl,
        #           urldefrag, urljoin, urlparse, urlsplit,
        #               urlunparse, urlunsplit)
        # from urllib import (quote,
        #             quote_plus,
        #             unquote,
        #             unquote_plus,
        #             urlencode,
        #             splitquery)

    'urllib.request':{'urllib':['pathname2url',
                                'url2pathname',
                                'getproxies',
                                'urlretrieve',
                                'urlcleanup',
                                'URLopener',
                                'FancyURLopener',
                                'proxy_bypass'],
                      'urllib2':['AbstractBasicAuthHandler',
                                 'AbstractDigestAuthHandler',
                                 'BaseHandler', 'CacheFTPHandler',
                                 'FileHandler', 'FTPHandler',
                                 'HTTPBasicAuthHandler',
                                 'HTTPCookieProcessor',
                                 'HTTPDefaultErrorHandler',
                                 'HTTPDigestAuthHandler',
                                 'HTTPErrorProcessor', 'HTTPHandler',
                                 'HTTPPasswordMgr',
                                 'HTTPPasswordMgrWithDefaultRealm',
                                 'HTTPRedirectHandler', 'HTTPSHandler',
                                 'URLError', 'build_opener',
                                 'install_opener', 'OpenerDirector',
                                 'ProxyBasicAuthHandler',
                                 'ProxyDigestAuthHandler',
                                 'ProxyHandler', 'Request',
                                 'UnknownHandler', 'urlopen'],
                      'urlparse':['urldefrag','urljoin', 'urlparse',
                                  'urlunparse', 'urlsplit', 'urlunsplit',
                                  'parse_qs', 'parse_q']},

        # from urllib import (pathname2url,
        #                     url2pathname,
        #                     getproxies,
        #                     urlretrieve,
        #                     urlcleanup,
        #                     URLopener,
        #                     FancyURLopener,
        #                     proxy_bypass)

        # from urllib2 import (
        #                  AbstractBasicAuthHandler,
        #                  AbstractDigestAuthHandler,
        #                  BaseHandler,
        #                  CacheFTPHandler,
        #                  FileHandler,
        #                  FTPHandler,
        #                  HTTPBasicAuthHandler,
        #                  HTTPCookieProcessor,
        #                  HTTPDefaultErrorHandler,
        #                  HTTPDigestAuthHandler,
        #                  HTTPErrorProcessor,
        #                  HTTPHandler,
        #                  HTTPPasswordMgr,
        #                  HTTPPasswordMgrWithDefaultRealm,
        #                  HTTPRedirectHandler,
        #                  HTTPSHandler,
        #                  URLError,
        #                  build_opener,
        #                  install_opener,
        #                  OpenerDirector,
        #                  ProxyBasicAuthHandler,
        #                  ProxyDigestAuthHandler,
        #                  ProxyHandler,
        #                  Request,
        #                  UnknownHandler,
        #                  urlopen,
        #                 )

        # from urlparse import (
        #                  urldefrag
        #                  urljoin,
        #                  urlparse,
        #                  urlunparse,
        #                  urlsplit,
        #                  urlunsplit,
        #                  parse_qs,
        #                  parse_q
        #                 )

    'urllib.error':{'urllib':['ContentTooShortError'],
                    'urllib2':['URLError', 'HTTPError']},

        # from urllib import ContentTooShortError
        # from urllib2 import URLError, HTTPError

    'xmlrpc.client':'xmlrpclib',
    'xmlrpc.server':'xmlrpclib',
}
for k, v in modules_mapping.items():
    if isinstance(v, dict):
        x = {}
        for m, attrs in v.items():
            for a in attrs:
                x[a] = m
        modules_mapping[k] = x

def import_(module, objects=None, py2=None):
    """
    :param module: py3 compatiable module path
    :param objects: objects want to imported, it should be a list
    :param via: for some py2 module, you should give the import path according the
        objects which you want to imported
    :return: object or module

    Usage:
        import_('urllib.parse', 'urlparse')
        import_('urllib.parse', ['urlparse', 'urljoin'])
        import_('urllib.parse', py2='urllib2')
    """
    if not PY2:
        mod = __import__(module, fromlist=['*'])
    else:
        path = modules_mapping.get(module)
        if not path:
            raise Exception("Can't find the module %s in mappings." % module)

        if objects:
            if not isinstance(objects, (list, tuple)):
                objects = [objects]

            r = []
            for x in objects:
                m = path.get(x)
                if not m:
                    raise Exception("Can't find the object %s in %s." % (x, path))
                mod = __import__(m, fromlist=['*'])
                r.append(getattr(mod, x))
            if len(r) > 1:
                return tuple(r)
            else:
                return r[0]

        else:
            if isinstance(path, (dict, list)):
                if not py2:
                    raise Exception("You should give py2 parameter to enable import from py2.")
                path = py2
            mod = __import__(path, fromlist=['*'])

            return mod
