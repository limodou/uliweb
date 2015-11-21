#!/usr/bin/env python
#
# Copyright 2009 Facebook
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
# This version is modified by limodou, in order to compatiable with uliweb
#

from __future__ import absolute_import, division, print_function, with_statement

import sys
from time import time
import datetime
import linecache
import os.path
import re
import threading
import shutil
import warnings

#################################
# escape module
#################################
class ObjectDict(dict):
    """Makes a dictionary behave like an object, with attribute-style access.
    """
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        self[name] = value

if type('') is not type(b''):
    def u(s):
        return s
    bytes_type = bytes
    unicode_type = str
    basestring_type = str
else:
    def u(s):
        return s.decode('unicode_escape')
    bytes_type = str
    unicode_type = unicode
    basestring_type = basestring

if sys.version_info > (3,):
    exec("""
def raise_exc_info(exc_info):
    raise exc_info[1].with_traceback(exc_info[2])

def exec_in(code, glob, loc=None):
    if isinstance(code, str):
        code = compile(code, '<string>', 'exec', dont_inherit=True)
    exec(code, glob, loc)
""")
else:
    exec("""
def raise_exc_info(exc_info):
    raise exc_info[0], exc_info[1], exc_info[2]

def exec_in(code, glob, loc=None):
    if isinstance(code, basestring):
        # exec(string) inherits the caller's future imports; compile
        # the string first to prevent that.
        code = compile(code, '<string>', 'exec', dont_inherit=True)
    exec code in glob, loc
""")

try:
    from urllib.parse import parse_qs as _parse_qs  # py3
except ImportError:
    from urlparse import parse_qs as _parse_qs  # Python 2.6+

try:
    import htmlentitydefs  # py2
except ImportError:
    import html.entities as htmlentitydefs  # py3

try:
    import urllib.parse as urllib_parse  # py3
except ImportError:
    import urllib as urllib_parse  # py2

import json

try:
    unichr
except NameError:
    unichr = chr

# _XHTML_ESCAPE_RE = re.compile('[&<>"\']')
# _XHTML_ESCAPE_DICT = {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;',
#                       '\'': '&#39;'}
_XHTML_ESCAPE_RE = re.compile('[&<>]')
_XHTML_ESCAPE_DICT = {'&': '&amp;', '<': '&lt;', '>': '&gt;'}


def xhtml_escape(value):
    """Escapes a string so it is valid within HTML or XML.

    Escapes the characters ``<``, ``>``, ``"``, ``'``, and ``&``.
    When used in attribute values the escaped strings must be enclosed
    in quotes.

    .. versionchanged:: 3.2

       Added the single quote to the list of escaped characters.
    """
    return _XHTML_ESCAPE_RE.sub(lambda match: _XHTML_ESCAPE_DICT[match.group(0)],
                                to_basestring(value))


def xhtml_unescape(value):
    """Un-escapes an XML-escaped string."""
    return re.sub(r"&(#?)(\w+?);", _convert_entity, _unicode(value))


# The fact that json_encode wraps json.dumps is an implementation detail.
# Please see https://github.com/facebook/tornado/pull/706
# before sending a pull request that adds **kwargs to this function.
def json_encode(value):
    """JSON-encodes the given Python object."""
    # JSON permits but does not require forward slashes to be escaped.
    # This is useful when json data is emitted in a <script> tag
    # in HTML, as it prevents </script> tags from prematurely terminating
    # the javscript.  Some json libraries do this escaping by default,
    # although python's standard library does not, so we do it here.
    # http://stackoverflow.com/questions/1580647/json-why-are-forward-slashes-escaped
    return json.dumps(value).replace("</", "<\\/")


def json_decode(value):
    """Returns Python objects for the given JSON string."""
    return json.loads(to_basestring(value))


def squeeze(value):
    """Replace all sequences of whitespace chars with a single space."""
    return re.sub(r"[\x00-\x20]+", " ", value).strip()


def url_escape(value, plus=True):
    """Returns a URL-encoded version of the given value.

    If ``plus`` is true (the default), spaces will be represented
    as "+" instead of "%20".  This is appropriate for query strings
    but not for the path component of a URL.  Note that this default
    is the reverse of Python's urllib module.

    .. versionadded:: 3.1
        The ``plus`` argument
    """
    quote = urllib_parse.quote_plus if plus else urllib_parse.quote
    return quote(utf8(value))


# python 3 changed things around enough that we need two separate
# implementations of url_unescape.  We also need our own implementation
# of parse_qs since python 3's version insists on decoding everything.
if sys.version_info[0] < 3:
    def url_unescape(value, encoding='utf-8', plus=True):
        """Decodes the given value from a URL.

        The argument may be either a byte or unicode string.

        If encoding is None, the result will be a byte string.  Otherwise,
        the result is a unicode string in the specified encoding.

        If ``plus`` is true (the default), plus signs will be interpreted
        as spaces (literal plus signs must be represented as "%2B").  This
        is appropriate for query strings and form-encoded values but not
        for the path component of a URL.  Note that this default is the
        reverse of Python's urllib module.

        .. versionadded:: 3.1
           The ``plus`` argument
        """
        unquote = (urllib_parse.unquote_plus if plus else urllib_parse.unquote)
        if encoding is None:
            return unquote(utf8(value))
        else:
            return unicode_type(unquote(utf8(value)), encoding)

    parse_qs_bytes = _parse_qs
else:
    def url_unescape(value, encoding='utf-8', plus=True):
        """Decodes the given value from a URL.

        The argument may be either a byte or unicode string.

        If encoding is None, the result will be a byte string.  Otherwise,
        the result is a unicode string in the specified encoding.

        If ``plus`` is true (the default), plus signs will be interpreted
        as spaces (literal plus signs must be represented as "%2B").  This
        is appropriate for query strings and form-encoded values but not
        for the path component of a URL.  Note that this default is the
        reverse of Python's urllib module.

        .. versionadded:: 3.1
           The ``plus`` argument
        """
        if encoding is None:
            if plus:
                # unquote_to_bytes doesn't have a _plus variant
                value = to_basestring(value).replace('+', ' ')
            return urllib_parse.unquote_to_bytes(value)
        else:
            unquote = (urllib_parse.unquote_plus if plus
                       else urllib_parse.unquote)
            return unquote(to_basestring(value), encoding=encoding)

    def parse_qs_bytes(qs, keep_blank_values=False, strict_parsing=False):
        """Parses a query string like urlparse.parse_qs, but returns the
        values as byte strings.

        Keys still become type str (interpreted as latin1 in python3!)
        because it's too painful to keep them as byte strings in
        python3 and in practice they're nearly always ascii anyway.
        """
        # This is gross, but python3 doesn't give us another way.
        # Latin1 is the universal donor of character encodings.
        result = _parse_qs(qs, keep_blank_values, strict_parsing,
                           encoding='latin1', errors='strict')
        encoded = {}
        for k, v in result.items():
            encoded[k] = [i.encode('latin1') for i in v]
        return encoded


_UTF8_TYPES = (bytes_type, type(None))


def utf8(value):
    """Converts a string argument to a byte string.

    If the argument is already a byte string or None, it is returned unchanged.
    Otherwise it must be a unicode string and is encoded as utf8.
    """
    if isinstance(value, _UTF8_TYPES):
        return value
    elif isinstance(value, unicode_type):
        return value.encode("utf-8")
    else:
        return str(value)

_TO_UNICODE_TYPES = (unicode_type, type(None))


def to_unicode(value):
    """Converts a string argument to a unicode string.

    If the argument is already a unicode string or None, it is returned
    unchanged.  Otherwise it must be a byte string and is decoded as utf8.
    """
    if isinstance(value, _TO_UNICODE_TYPES):
        return value
    if not isinstance(value, bytes_type):
        raise TypeError(
            "Expected bytes, unicode, or None; got %r" % type(value)
        )
    return value.decode("utf-8")

# to_unicode was previously named _unicode not because it was private,
# but to avoid conflicts with the built-in unicode() function/type
_unicode = to_unicode

# When dealing with the standard library across python 2 and 3 it is
# sometimes useful to have a direct conversion to the native string type
if str is unicode_type:
    native_str = to_unicode
else:
    native_str = utf8

_BASESTRING_TYPES = (basestring_type, type(None))


def to_basestring(value):
    """Converts a string argument to a subclass of basestring.

    In python2, byte and unicode strings are mostly interchangeable,
    so functions that deal with a user-supplied argument in combination
    with ascii string constants can use either and should return the type
    the user supplied.  In python3, the two types are not interchangeable,
    so this method is needed to convert byte strings to unicode.
    """
    if value is None:
        return 'None'
    if isinstance(value, _BASESTRING_TYPES):
        return value
    elif isinstance(value, unicode_type):
        return value.decode("utf-8")
    else:
        return str(value)


def recursive_unicode(obj):
    """Walks a simple data structure, converting byte strings to unicode.

    Supports lists, tuples, and dictionaries.
    """
    if isinstance(obj, dict):
        return dict((recursive_unicode(k), recursive_unicode(v)) for (k, v) in obj.items())
    elif isinstance(obj, list):
        return list(recursive_unicode(i) for i in obj)
    elif isinstance(obj, tuple):
        return tuple(recursive_unicode(i) for i in obj)
    elif isinstance(obj, bytes_type):
        return to_unicode(obj)
    else:
        return obj

# I originally used the regex from
# http://daringfireball.net/2010/07/improved_regex_for_matching_urls
# but it gets all exponential on certain patterns (such as too many trailing
# dots), causing the regex matcher to never return.
# This regex should avoid those problems.
# Use to_unicode instead of tornado.util.u - we don't want backslashes getting
# processed as escapes.
_URL_RE = re.compile(to_unicode(r"""\b((?:([\w-]+):(/{1,3})|www[.])(?:(?:(?:[^\s&()]|&amp;|&quot;)*(?:[^!"#$%&'()*+,.:;<=>?@\[\]^`{|}~\s]))|(?:\((?:[^\s&()]|&amp;|&quot;)*\)))+)"""))


def linkify(text, shorten=False, extra_params="",
            require_protocol=False, permitted_protocols=["http", "https"]):
    """Converts plain text into HTML with links.

    For example: ``linkify("Hello http://tornadoweb.org!")`` would return
    ``Hello <a href="http://tornadoweb.org">http://tornadoweb.org</a>!``

    Parameters:

    * ``shorten``: Long urls will be shortened for display.

    * ``extra_params``: Extra text to include in the link tag, or a callable
        taking the link as an argument and returning the extra text
        e.g. ``linkify(text, extra_params='rel="nofollow" class="external"')``,
        or::

            def extra_params_cb(url):
                if url.startswith("http://example.com"):
                    return 'class="internal"'
                else:
                    return 'class="external" rel="nofollow"'
            linkify(text, extra_params=extra_params_cb)

    * ``require_protocol``: Only linkify urls which include a protocol. If
        this is False, urls such as www.facebook.com will also be linkified.

    * ``permitted_protocols``: List (or set) of protocols which should be
        linkified, e.g. ``linkify(text, permitted_protocols=["http", "ftp",
        "mailto"])``. It is very unsafe to include protocols such as
        ``javascript``.
    """
    if extra_params and not callable(extra_params):
        extra_params = " " + extra_params.strip()

    def make_link(m):
        url = m.group(1)
        proto = m.group(2)
        if require_protocol and not proto:
            return url  # not protocol, no linkify

        if proto and proto not in permitted_protocols:
            return url  # bad protocol, no linkify

        href = m.group(1)
        if not proto:
            href = "http://" + href   # no proto specified, use http

        if callable(extra_params):
            params = " " + extra_params(href).strip()
        else:
            params = extra_params

        # clip long urls. max_len is just an approximation
        max_len = 30
        if shorten and len(url) > max_len:
            before_clip = url
            if proto:
                proto_len = len(proto) + 1 + len(m.group(3) or "")  # +1 for :
            else:
                proto_len = 0

            parts = url[proto_len:].split("/")
            if len(parts) > 1:
                # Grab the whole host part plus the first bit of the path
                # The path is usually not that interesting once shortened
                # (no more slug, etc), so it really just provides a little
                # extra indication of shortening.
                url = url[:proto_len] + parts[0] + "/" + \
                    parts[1][:8].split('?')[0].split('.')[0]

            if len(url) > max_len * 1.5:  # still too long
                url = url[:max_len]

            if url != before_clip:
                amp = url.rfind('&')
                # avoid splitting html char entities
                if amp > max_len - 5:
                    url = url[:amp]
                url += "..."

                if len(url) >= len(before_clip):
                    url = before_clip
                else:
                    # full url is visible on mouse-over (for those who don't
                    # have a status bar, such as Safari by default)
                    params += ' title="%s"' % href

        return u('<a href="%s"%s>%s</a>') % (href, params, url)

    # First HTML-escape so that our strings are all safe.
    # The regex is modified to avoid character entites other than &amp; so
    # that we won't pick up &quot;, etc.
    text = _unicode(xhtml_escape(text))
    return _URL_RE.sub(make_link, text)


def _convert_entity(m):
    if m.group(1) == "#":
        try:
            return unichr(int(m.group(2)))
        except ValueError:
            return "&#%s;" % m.group(2)
    try:
        return _HTML_UNICODE_MAP[m.group(2)]
    except KeyError:
        return "&%s;" % m.group(2)


def _build_unicode_map():
    unicode_map = {}
    for name, value in htmlentitydefs.name2codepoint.items():
        unicode_map[name] = unichr(value)
    return unicode_map

_HTML_UNICODE_MAP = _build_unicode_map()

#############################
# template module
#############################

BEGIN_TAG = '{{'
END_TAG = '}}'

try:
    from cStringIO import StringIO  # py2
except ImportError:
    from io import StringIO  # py3

_DEFAULT_AUTOESCAPE = "xhtml_escape"
_UNSET = object()

__custom_nodes__ = {}

default_namespace = {
    "escape": xhtml_escape,
    "xhtml_escape": xhtml_escape,
    "url_escape": url_escape,
    "json_encode": json_encode,
    "squeeze": squeeze,
    "linkify": linkify,
    "datetime": datetime,
    "_tt_utf8": utf8,  # for internal use
    "_tt_string_types": (unicode_type, bytes_type),
}

def register_node(name, node):
    global __custom_nodes__

    __custom_nodes__[name] = node

def reindent(text, filename):
    new_lines=[]
    k=0
    c=0
    for n, raw_line in enumerate(text.splitlines()):
        line=raw_line.strip()
        if not line or line[0]=='#':
            new_lines.append(line)
            continue

        line3 = line[:3]
        line4 = line[:4]
        line5 = line[:5]
        line6 = line[:6]
        line7 = line[:7]
        if line3=='if ' or line4 in ('def ', 'for ', 'try:') or\
            line6=='while ' or line6=='class ' or line5=='with ':
            new_lines.append('    '*k+line)
            k += 1
            continue
        elif line5=='elif ' or line5=='else:' or    \
            line7=='except:' or line7=='except ' or \
            line7=='finally:':
                c = k-1
                if c<0:
                    # print (_format_code(text))
                    raise ParseError("Extra pass founded on line %s:%d" % (filename, n))
                new_lines.append('    '*c+line)
                continue
        else:
            new_lines.append('    '*k+line)
        if line=='pass' or line5=='pass ':
            k-=1
        if k<0: k = 0
    text='\n'.join(new_lines)
    return text

class Template(object):
    """A compiled template.

    We compile into Python from the given template_string. You can generate
    the template from variables with generate().
    """
    # note that the constructor's signature is not extracted with
    # autodoc because _UNSET looks like garbage.  When changing
    # this signature update website/sphinx/template.rst too.
    def __init__(self, template_string,
                 begin_tag=BEGIN_TAG, end_tag=END_TAG,
                 name="<string>", loader=None,
                 compress_whitespace=None, filename=None,
                 _compile=None, debug=False, see=None,
                 skip_extern=False, log=None, multilines=False,
                 comment=True):
        """
        :param filename: used to store the real filename
        """
        self.name = name
        self.begin_tag = begin_tag
        self.end_tag = end_tag
        self.filename = filename or self.name
        self._compile = _compile or compile
        self.debug = debug
        self.see = see
        self.has_links = False
        self.skip_extern = skip_extern
        self.log = log
        self.multilines = multilines
        self.comment = comment
        if compress_whitespace is None:
            compress_whitespace = name.endswith(".html") or \
                name.endswith(".js")
        self.autoescape = None
        self.namespace = loader.namespace if loader else {}
        self.depends = {} #saving depends filenames such as extend, include, value is compile time
        reader = _TemplateReader(name, native_str(template_string))
        self.file = _File(self, _parse(reader, self, begin_tag=self.begin_tag,
                                       end_tag=self.end_tag, debug=self.debug,
                                       see=self.see))
        self.code = self._generate_python(loader, compress_whitespace)
        self.loader = loader
        try:
            # Under python2.5, the fake filename used here must match
            # the module name used in __name__ below.
            # The dont_inherit flag prevents template.py's future imports
            # from being applied to the generated code.
            self.compiled = self._compile(
                to_unicode(self.code),
                # "%s.generated.py" % self.name.replace('/', '_'),
                self.name,
                "exec", dont_inherit=True)
            self.compiled_time = time()
        except Exception:
            formatted_code = _format_code(self.code).rstrip()
            if self.log:
                self.log.error("%s code:\n%s", self.name, formatted_code)
            raise

    def generate(self, vars=None, env=None):
        """Generate this template with the given arguments."""
        def defined(v, default=None):
            _v = default
            if v in vars:
                _v = vars[v]
            elif v in env:
                _v = env[v]
            return _v

        namespace = {
            # __name__ and __loader__ allow the traceback mechanism to find
            # the generated source code.
            "defined": defined,
            #fix RuntimeWarning: Parent module 'a/b/c' not found while handling absolute import warning
            "__name__": self.name.replace('.', '_'),
            # "__name__": self.name,
            "__loader__": ObjectDict(get_source=lambda name: self.code),
        }
        namespace.update(default_namespace)
        namespace.update(env or {})
        namespace.update(self.namespace)
        namespace.update(vars or {})
        namespace['_vars'] = vars
        exec_in(self.compiled, namespace)
        execute = namespace["_tt_execute"]
        # Clear the traceback module's cache of source data now that
        # we've generated a new template (mainly for this module's
        # unittests, where different tests reuse the same name).
        linecache.clearcache()
        return execute()

    def _generate_python(self, loader, compress_whitespace):
        buffer = StringIO()
        try:
            # named_blocks maps from names to _NamedBlock objects
            named_blocks = {}
            ancestors = self._get_ancestors(loader)
            ancestors.reverse()
            for ancestor in ancestors:
                ancestor.find_named_blocks(loader, named_blocks)
            writer = _CodeWriter(buffer, named_blocks, loader, ancestors[0].template,
                                 compress_whitespace, comment=self.comment)
            ancestors[0].generate(writer, self.has_links)
            code =  buffer.getvalue()
            if self.multilines:
                return reindent(code, self.filename)
            else:
                return code
        finally:
            buffer.close()

    def _get_ancestors(self, loader):
        ancestors = [self.file]
        for chunk in self.file.body.chunks:
            if isinstance(chunk, _ExtendsBlock):
                if not loader:
                    raise ParseError("%s extends %s block found, but no "
                                    "template loader on file %s" % (self.begin_tag,
                                    self.end_tag, self.filename))
                template = loader.load(chunk.name, skip=self.filename,
                                    skip_original=self.name)
                #process depends
                self.depends[template.filename] = template.compiled_time
                self.depends.update(template.depends)
                if self.see:
                    self.see('extend', self.filename, template.filename)
                #process has_links
                if template.has_links:
                    self.has_links = True
                ancestors.extend(template._get_ancestors(loader))
        return ancestors

class LRUTmplatesCacheDict(object):
    """ A dictionary-like object, supporting LRU caching semantics.
    """

    __slots__ = ['max_size', 'check_modified_time', '__values',
                 '__access_keys', '__modified_times']

    def __init__(self, max_size=None, check_modified_time=False):
        self.max_size = max_size
        self.check_modified_time = check_modified_time

        self.__values = {}
        self.__access_keys = []
        self.__modified_times = {}

    def __len__(self):
        return len(self.__values)

    def clear(self):
        """
        Clears the dict.
        """
        self.__values.clear()
        self.__access_keys = []
        self.__modified_times.clear()

    def has(self, key, mtime=None):
        """
        This method should almost NEVER be used. The reason is that between the time
        has_key is called, and the key is accessed, the key might vanish.

        """
        v = self.__values.get(key, None)
        if not v:
            return False
        if self.check_modified_time:
            mtime = mtime or os.path.getmtime(key)
            if mtime != self.__modified_times[key]:
                del self[key]
                return False
        return True

    def __contains__(self, key):
        return self.has(key)

    def set(self, key, value, mtime=None):
        del self[key]
        self.__values[key] = value
        try:
            pos = self.__access_keys.remove(key)
        except ValueError:
            pass
        self.__access_keys.insert(0, key)
        if self.check_modified_time:
            self.__modified_times[key] = mtime or os.path.getmtime(key)
        self.cleanup()

    def __setitem__(self, key, value):
        self.set(key, value)

    def get(self, key, mtime=None):
        v = self.__values.get(key, None)
        if not v:
            return None
        if self.check_modified_time:
            mtime = mtime or os.path.getmtime(key)
            if mtime != self.__modified_times[key]:
                del self[key]
                return None
        self.__access_keys.remove(key)
        self.__access_keys.insert(0, key)
        return v

    def __getitem__(self, key):
        return self.get(key)

    def __delitem__(self, key):
        if key in self.__values:
            del self.__values[key]
            if self.check_modified_time:
                del self.__modified_times[key]
            self.__access_keys.remove(key)

    def cleanup(self):
        if not self.max_size: return
        for i in range(len(self.__access_keys)-1, self.max_size, -1):
            key = self.__access_keys.pop()
            self.__delitem__(key)

    def keys(self):
        return self.__values.keys()

r_extend = re.compile(r'(\s*#.*?)?\{\{extend[s]?\s\S+\s*\}\}', re.DOTALL)

class Loader(object):
    """A template loader that loads from a single root directory.
    """
    def __init__(self, dirs, namespace=None, cache=True, use_tmp=False,
                 tmp_dir='tmp/templates_temp', begin_tag=BEGIN_TAG,
                 end_tag=END_TAG, debug=False, see=None, max_size=None,
                 _compile=None, check_modified_time=False, skip_extern=False,
                 log=None, multilines=False, comment=True, taglibs_loader=None):
        self.dirs = dirs
        self.namespace = namespace or {}
        self.cache = cache
        self.use_tmp = use_tmp
        self.tmp_dir = tmp_dir
        self.check_modified_time = check_modified_time
        self.templates = LRUTmplatesCacheDict(max_size=max_size,
                        check_modified_time=check_modified_time)
        self.begin_tag = begin_tag
        self.end_tag = end_tag
        self.debug = debug
        self.see = see
        self._compile = compile
        self.lock = threading.RLock()
        self.skip_extern = skip_extern
        self.log = log
        self.multilines = multilines
        self.comment = comment
        self.taglibs_loader = taglibs_loader

        #init tmp_dir
        if self.cache and self.use_tmp and self.tmp_dir:
            if not os.path.exists(self.tmp_dir):
                os.makedirs(self.tmp_dir)


    def reset(self):
        """Resets the cache of compiled templates."""
        with self.lock:
            if self.cache:
                if self.use_tmp:
                    shutil.rmtree(self.tmp_dir, ignore_errors=True)
                else:
                    self.templates = {}

    def load(self, name, skip='', skip_original='', default_template=None, layout=None):
        """Loads a template."""
        filename = self.resolve_path(name, skip=skip, skip_original=skip_original,
                                     default_template=default_template)

        if not filename:
            raise ParseError("Can't find template %s." % name)

        with self.lock:
            if layout:
                _filename = filename + '.' + layout
                mtime = os.path.getmtime(filename)
            else:
                mtime = None
                _filename = filename

            if self.cache:
                if not self.use_tmp:
                    #check current template file expiration
                    t = self.templates.get(_filename, mtime=mtime)
                    if t:
                        #check depends tempaltes expiration
                        check = self.check_expiration(t)
                        if not check:
                            return t
                else:
                    #get cached file from disk
                    pass
            t = self._create_template(name, filename, layout=layout)
            if self.cache:
                if not self.use_tmp:
                    self.templates.set(_filename, t, mtime)
                else:
                    #save cached file to disk
                    pass

            return t

    def resolve_path(self, filename, skip='', skip_original='',
                     default_template=None):
        """
        Fetch the template filename according dirs
        :para skip: if the searched filename equals skip, then using the one before.
        """
        def _file(filename, dirs):
            for d in dirs:
                _f = os.path.normpath(os.path.join(d, filename))
                if os.path.exists(_f):
                    yield _f
            raise StopIteration

        filename = os.path.normpath(filename)
        skip = os.path.normpath(skip)
        skip_original = os.path.normpath(skip_original)

        if os.path.exists(filename):
            return filename

        if filename and self.dirs:
            _files = _file(filename, self.dirs)
            if skip_original == filename:
                for f in _files:
                    if f == skip:
                        break

            for f in _files:
                if f != skip:
                    return f
                else:
                    continue

        if default_template:
            if not isinstance(default_template, (tuple, list)):
                default_template = [default_template]
            for x in default_template:
                filename = self.resolve_path(x)
                if filename:
                    return filename

    def _process_tags(self, text):
        from .taglibs import parse

        return parse(text, loader=self.taglibs_loader)

    def _create_template(self, name, filename, _compile=None, see=None, layout=None):
        if not os.path.exists(filename):
            raise ParseError("The file %s is not existed." % filename)

        with open(filename, 'rb') as f:
            text = f.read()

            #add tag convert support 2015/11/21 limodou
            text = self._process_tags(text)

            #if layout is not empty and there is no {{extend}} exsited
            if layout:
                if not r_extend.match(text):
                    text = ('{{extend "%s"}}\n' % layout) + text
                    name = name + '.' + layout
                    filename = filename + '.' + layout

            template = Template(text, name=name, loader=self,
                                begin_tag=self.begin_tag, end_tag=self.end_tag,
                                debug=self.debug, see=self.see,
                                filename=filename, _compile=self._compile,
                                skip_extern=self.skip_extern, log=self.log,
                                multilines=self.multilines,
                                comment=self.comment)
        return template

    def _get_temp_template(self, filename):
        f, filename = os.path.splitdrive(filename)
        filename = filename.replace('\\', '_')
        filename = filename.replace('/', '_')
        f, ext = os.path.splitext(filename)
        filename = f + '.py'
        return os.path.normpath(os.path.join(self.tmp_dir, filename))

    def find_templates(self, filename):
        files = []
        if os.path.exists(filename):
            return [filename]

        for dir in self.dirs:
            _filename = os.path.join(dir, filename)
            if os.path.exists(_filename):
                _filename = _filename.replace('\\', '/')
                files.append(_filename)
        return files

    def check_expiration(self, template):
        for f, compiled_time in template.depends.items():
            t = self.templates.get(f)
            if not t:
                return f
            if compiled_time != t.compiled_time:
                return f
            # t = self.load(f)
            # x = self.check_expiration(t)
            # if x:
            #     return x

        return False

    def _get_rel_filename(self, filename, path):
        f1 = os.path.splitdrive(filename)[1]
        f2 = os.path.splitdrive(path)[1]
        f = os.path.relpath(f1, f2).replace('\\', '/')
        if f.startswith('..'):
            return filename.replace('\\', '/')
        else:
            return f

    def print_tree(self, filename, path=None):
        tree_ids = {}
        nodes = {}

        def make_tree(alist):
            parents = []
            for p, c, prop in alist:
                _ids = tree_ids.setdefault(p, [])
                _ids.append(c)
                nodes[c] = {'id':c, 'prop':prop}
                parents.append(p)

            d = list(set(parents) - set(nodes.keys()))
            for x in d:
                nodes[x] = {'id':x, 'prop':''}
            return d

        def print_tree(subs, cur=None, level=1, indent=4):
            for x in subs:
                n = nodes[x]
                caption = ('(%s)' % n['prop']) if n['prop'] else ''
                if cur == n['id']:
                    print ('-'*(level*indent-1)+'>', '%s%s' % (caption, n['id']))
                else:
                    print (' '*level*indent, '%s%s' % (caption, n['id']))
                print_tree(tree_ids.get(x, []), cur=cur, level=level+1, indent=indent)

        _filename = ''
        templates = []
        path = path or os.getcwd()
        for p in self.dirs:
            _filename = os.path.join(p, filename)
            if os.path.exists(_filename):
                print (self._get_rel_filename(_filename, path))
                print ()
                print ('-------------- Tree --------------')

                break
        if _filename:
            def see(action, cur_filename, filename):
                #templates(get_rel_filename(filename, path), cur_filename, action)
                if action == 'extend':
                    x = (self._get_rel_filename(filename, path), self._get_rel_filename(cur_filename, path), action)
                else:
                    x = (self._get_rel_filename(cur_filename, path), self._get_rel_filename(filename, path), action)
                if not x in templates:
                    templates.append(x)
            self.see = see
            self.cache = False
            t = self.load(filename)

            print_tree(make_tree(templates), self._get_rel_filename(_filename, path))

    def print_blocks(self, filename, with_filename=True, path=None):
        print ('-------------- Blocks --------------')
        t = self.load(filename)

        path = path or os.getcwd()
        blocks = {}
        block_names = []

        class ID(object):
            count = 1

        def see(name, filename, parent):
            if not name in blocks:
                _id = ID.count
                blocks[name] = {'filename':filename, 'path':[]}
                ID.count += 1
                if parent:
                    parent_path = blocks[parent]['path']
                else:
                    parent_path = []
                blocks[name]['path'] = x = parent_path + [_id]
                blocks[name]['indent'] = len(x)
                block_names.append((x, name))
            else:
                blocks[name]['filename'] = filename

        named_blocks = {}
        ancestors = t._get_ancestors(self)
        ancestors.reverse()
        for ancestor in ancestors:
            ancestor.see_named_blocks(self, named_blocks, None, see)

        for _path, name in sorted(block_names, key=lambda x:x[0]):
            filename, indent = blocks[name]['filename'], blocks[name]['indent']
            f = self._get_rel_filename(filename, path)
            if with_filename:
                print ('    '*indent + name, '  ('+f+')')
            else:
                print ('    '*indent + name)


class _Node(object):
    def each_child(self):
        return ()

    def generate(self, writer):
        raise NotImplementedError()

    def find_named_blocks(self, loader, named_blocks):
        for child in self.each_child():
            child.find_named_blocks(loader, named_blocks)

    def see_named_blocks(self, loader, named_blocks, path=None, see=None):
        for child in self.each_child():
            child.see_named_blocks(loader, named_blocks, path, see)

class _File(_Node):
    def __init__(self, template, body):
        self.template = template
        self.body = body
        self.line = 0

    def generate(self, writer, has_links):
        writer.write_line("def _tt_execute():", self.line)
        with writer.indent():
            writer.write_line("_tt_buffer = []", self.line)
            writer.write_line("_tt_append = _tt_buffer.append", self.line)
            writer.write_line("def _tt_write(t, escape=True):", self.line)
            writer.write_line("    if escape:", self.line)
            writer.write_line("        _tt_append(xhtml_escape(_tt_utf8(t)))", self.line)
            writer.write_line("    else:", self.line)
            writer.write_line("        _tt_append(_tt_utf8(t))", self.line)
            writer.write_line("        pass", self.line)
            writer.write_line("    pass", self.line)
            writer.write_line("def out_write(value):", self.line)
            writer.write_line("    _tt_append(_tt_utf8(value))", self.line)
            writer.write_line("    pass", self.line)

            if has_links:
                writer.write_line("_tt_links = {'toplinks': [], 'bottomlinks': [], 'headlinks':[]}", self.line)
                writer.write_line("def _tt_use(name, *args, **kwargs):", self.line)
                writer.write_line("    _tag_use(_tt_links, name, *args, **kwargs)", self.line)
                writer.write_line("    pass", self.line)
                writer.write_line("def _tt_link(name, to='toplinks', **kwargs):", self.line)
                writer.write_line("    _tag_link(_tt_links, name, to=to, **kwargs)", self.line)
                writer.write_line("    pass", self.line)
                writer.write_line("def _tt_head(name, **kwargs):", self.line)
                writer.write_line("    _tag_head(_tt_links, name, **kwargs)", self.line)
                writer.write_line("    pass", self.line)
                writer.write_line("def _tt_head_link(args):", self.line)
                writer.write_line("    _tag_head_link(_tt_links, args)", self.line)
                writer.write_line("    pass", self.line)
            self.body.generate(writer)
            if has_links:
                writer.write_line("return _tag_htmlmerge(_tt_utf8('').join(_tt_buffer), _tt_links)", self.line)
            else:
                writer.write_line("return _tt_utf8('').join(_tt_buffer)", self.line)

    def each_child(self):
        return (self.body,)


class _ChunkList(_Node):
    def __init__(self, chunks):
        self.chunks = chunks

    def generate(self, writer):
        for chunk in self.chunks:
            chunk.generate(writer)

    def each_child(self):
        return self.chunks


class _NamedBlock(_Node):
    def __init__(self, name, body, template, line):
        self.name = name
        self.body = body
        self.template = template
        self.line = line

    def each_child(self):
        return (self.body,)

    def generate(self, writer):
        block = writer.named_blocks[self.name]
        if self.template.debug:
            writer.write_line('_tt_append("<!-- BLOCK %s (%s) -->")' % (self.name, block.template.filename), self.line)
        with writer.include(block.template, self.line):
            block.body.generate(writer)
        if self.template.debug:
            writer.write_line('_tt_append("<!-- END %s -->")' % self.name, self.line)

    def find_named_blocks(self, loader, named_blocks):
        named_blocks[self.name] = self
        _Node.find_named_blocks(self, loader, named_blocks)

    def see_named_blocks(self, loader, named_blocks, parent=None, see=None):
        named_blocks[self.name] = self
        if see:
            see(self.name, self.template.filename, parent=parent)
        _Node.see_named_blocks(self, loader, named_blocks, self.name, see)


class _ExtendsBlock(_Node):
    def __init__(self, name):
        self.name = name


class _IncludeBlock(_Node):
    def __init__(self, name, reader, line, template):
        self.name = name
        self.template_name = reader.name
        self.line = line
        self.template = template

    def find_named_blocks(self, loader, named_blocks):
        included = loader.load(self.name, self.template_name)
        self.template.depends[included.filename] = included.compiled_time
        if loader.see:
            loader.see('include', self.template.filename, included.filename)
        if included.has_links:
            self.template.has_links = True
        included.file.find_named_blocks(loader, named_blocks)

    def see_named_blocks(self, loader, named_blocks, parent, see=None):
        included = loader.load(self.name, self.template_name)
        self.template.depends[included.filename] = included.compiled_time
        # if loader.see:
        #     loader.see('include', self.template.filename, included.filename)
        included.file.see_named_blocks(loader, named_blocks, parent, see)

    def generate(self, writer):
        included = writer.loader.load(self.name, self.template_name)
        with writer.include(included, self.line):
            included.file.body.generate(writer)


class _ApplyBlock(_Node):
    def __init__(self, method, line, body=None):
        self.method = method
        self.line = line
        self.body = body

    def each_child(self):
        return (self.body,)

    def generate(self, writer):
        method_name = "_tt_apply%d" % writer.apply_counter
        writer.apply_counter += 1
        writer.write_line("def %s():" % method_name, self.line)
        with writer.indent():
            writer.write_line("_tt_buffer = []", self.line)
            writer.write_line("_tt_append = _tt_buffer.append", self.line)
            writer.write_line("def _tt_write(t, escape=True):", self.line)
            writer.write_line("    if escape:", self.line)
            writer.write_line("         _tt_append(xhtml_escape(t))", self.line)
            writer.write_line("    else: _tt_append(t)", self.line)
            writer.write_line("        _tt_append(t)", self.line)
            writer.write_line("        pass", self.line)
            writer.write_line("    pass", self.line)
            self.body.generate(writer)
            writer.write_line("return _tt_utf8('').join(_tt_buffer)", self.line)
        writer.write_line("_tt_append(_tt_utf8(%s(%s())))" % (
            self.method, method_name), self.line)

class _ControlBlock(_Node):
    def __init__(self, statement, line, body=None):
        self.statement = statement
        self.line = line
        self.body = body

    def each_child(self):
        return (self.body,)

    def generate(self, writer):
        # writer.write_line("%s:" % self.statement, self.line)
        #in uliewb, ':' will be added by user
        writer.write_line("%s" % self.statement, self.line)
        with writer.indent():
            self.body.generate(writer)
            # Just in case the body was empty
            writer.write_line("pass", self.line)

class BaseBlockNode(_ControlBlock):
    pass

class _IntermediateControlBlock(_Node):
    def __init__(self, statement, line):
        self.statement = statement
        self.line = line

    def generate(self, writer):
        # In case the previous block was empty
        writer.write_line("pass", self.line)
        #writer.write_line("%s:" % self.statement, self.line, writer.indent_size() - 1)
        #in uliewb, ':' will be added by user
        writer.write_line("%s" % self.statement, self.line, writer.indent_size() - 1)


class _Statement(_Node):
    def __init__(self, statement, line):
        self.statement = statement
        self.line = line

    def generate(self, writer):
        writer.write_line(self.statement, self.line)

class BaseNode(_Statement):
    pass

class _Expression(_Node):
    def __init__(self, expression, line, raw=False):
        self.expression = expression
        self.line = line
        self.raw = raw

    def generate(self, writer):
        writer.write_line("_tt_tmp = %s" % self.expression, self.line)
        writer.write_line("if isinstance(_tt_tmp, _tt_string_types):", self.line)
        writer.write_line("    _tt_tmp = _tt_utf8(_tt_tmp)", self.line)
        writer.write_line("else:", self.line)
        writer.write_line("    _tt_tmp = _tt_utf8(str(_tt_tmp))", self.line)
        writer.write_line("    pass", self.line)
        if not self.raw and writer.current_template.autoescape is not None:
            # In python3 functions like xhtml_escape return unicode,
            # so we have to convert to utf8 again.
            writer.write_line("_tt_tmp = _tt_utf8(%s(_tt_tmp))" %
                              writer.current_template.autoescape, self.line)
        writer.write_line("_tt_append(_tt_tmp)", self.line)


class _Module(_Expression):
    def __init__(self, expression, line):
        super(_Module, self).__init__("_tt_modules." + expression, line,
                                      raw=True)


class _Text(_Node):
    def __init__(self, value, line):
        self.value = value
        self.line = line

    def generate(self, writer):
        value = self.value

        # Compress lots of white space to a single character. If the whitespace
        # breaks a line, have it continue to break a line, but just with a
        # single \n character
        if writer.compress_whitespace and "<pre>" not in value:
            value = re.sub(r"([\t ]+)", " ", value)
            value = re.sub(r"(\s*\n\s*)", "\n", value)

        if value:
            writer.write_line('_tt_append(%r)' % utf8(value), self.line)

class _Use(_Node):
    def __init__(self, value, line, template):
        self.value = value
        self.line = line
        self.template = template
        self.template.has_links = True

    def generate(self, writer):
        value = self.value
        if value:
            writer.write_line('_tt_use(%s)' % value, self.line)

class _Link(_Node):
    def __init__(self, value, line, template):
        self.value = value
        self.line = line
        self.template = template
        self.template.has_links = True


    def generate(self, writer):
        value = self.value
        if value:
            writer.write_line('_tt_link(%s)' % value, self.line)

class _Head(_Node):
    def __init__(self, value, line, template):
        self.value = value
        self.line = line
        self.template = template
        self.template.has_links = True


    def generate(self, writer):
        value = self.value
        if value:
            writer.write_line('_tt_head(%s)' % value, self.line)

class _HeadLink(_Node):
    def __init__(self, value, line, template):
        self.value = value
        self.line = line
        self.template = template
        self.template.has_links = True


    def generate(self, writer):
        value = self.value
        if value:
            writer.write_line('_tt_head_link(%s)' % value, self.line)

class ParseError(Exception):
    """Raised for template syntax errors."""
    pass


class _CodeWriter(object):
    def __init__(self, file, named_blocks, loader, current_template,
                 compress_whitespace, comment=False):
        self.file = file
        self.named_blocks = named_blocks
        self.loader = loader
        self.current_template = current_template
        self.compress_whitespace = compress_whitespace
        self.apply_counter = 0
        self.include_stack = []
        self._indent = 0
        self.comment = comment

    def indent_size(self):
        return self._indent

    def indent(self):
        class Indenter(object):
            def __enter__(_):
                self._indent += 1
                return self

            def __exit__(_, *args):
                assert self._indent > 0
                self._indent -= 1

        return Indenter()

    def include(self, template, line):
        self.include_stack.append((self.current_template, line))
        self.current_template = template

        class IncludeTemplate(object):
            def __enter__(_):
                return self

            def __exit__(_, *args):
                self.current_template = self.include_stack.pop()[0]

        return IncludeTemplate()

    def write_line(self, line, line_number, indent=None):
        if indent is None:
            indent = self._indent
        if self.comment:
            line_comment = '  # %s:%d' % (self.current_template.name, line_number)
            if self.include_stack:
                ancestors = ["%s:%d" % (tmpl.name, lineno)
                             for (tmpl, lineno) in self.include_stack]
                line_comment += ' (via %s)' % ', '.join(reversed(ancestors))
        else:
            line_comment = ''
        print("    " * indent + line + line_comment, file=self.file)


class _TemplateReader(object):
    def __init__(self, name, text):
        self.name = name
        self.text = text
        self.line = 1
        self.pos = 0

    def find(self, needle, start=0, end=None):
        assert start >= 0, start
        pos = self.pos
        start += pos
        if end is None:
            index = self.text.find(needle, start)
        else:
            end += pos
            assert end >= start
            index = self.text.find(needle, start, end)
        if index != -1:
            index -= pos
        return index

    def consume(self, count=None):
        if count is None:
            count = len(self.text) - self.pos
        newpos = self.pos + count
        self.line += self.text.count("\n", self.pos, newpos)
        s = self.text[self.pos:newpos]
        self.pos = newpos
        return s

    def remaining(self):
        return len(self.text) - self.pos

    def __len__(self):
        return self.remaining()

    def __getitem__(self, key):
        if type(key) is slice:
            size = len(self)
            start, stop, step = key.indices(size)
            if start is None:
                start = self.pos
            else:
                start += self.pos
            if stop is not None:
                stop += self.pos
            return self.text[slice(start, stop, step)]
        elif key < 0:
            return self.text[key]
        else:
            return self.text[self.pos + key]

    def __str__(self):
        return self.text[self.pos:]


def _format_code(code):
    lines = code.splitlines()
    format = "%%%dd  %%s\n" % len(repr(len(lines) + 1))
    return "".join([format % (i + 1, line) for (i, line) in enumerate(lines)])

r_out_write = re.compile(r'out\.write', re.DOTALL)
r_out_xml = re.compile(r'out\.xml', re.DOTALL)

def _parse(reader, template, in_block=None, in_loop=None,
           begin_tag=BEGIN_TAG, end_tag=END_TAG, debug=False, see=None):
    body = _ChunkList([])
    _len_b = len(begin_tag)
    _len_e = len(end_tag)
    comment_end = '##%s' % end_tag
    _len_comment = len(comment_end)
    filename = template.filename

    # Find begin and tag definition
    if reader.find('#uliweb-template-tag:') > -1:
        pos = reader.find('\n', 21)
        tag_head = reader.consume(26)[21:]
        begin_tag, end_tag = [x.strip() for x in tag_head.split(',')][:2]
        _len_b = len(begin_tag)
        _len_e = len(end_tag)
        comment_end = '##%s' % end_tag
        _len_comment = len(comment_end)

    while True:
        # Find next template directive
        curly = 0
        while True:
            curly = reader.find(begin_tag, curly)
            if curly == -1 or curly + _len_b == reader.remaining():
                # EOF
                if in_block:
                    raise ParseError("Missing %s end %s block for %s on line %s:%d" %
                                     (begin_tag, end_tag, in_block, filename,
                                     reader.line))
                body.chunks.append(_Text(reader.consume(), reader.line))
                return body
            # If the first curly brace is not the start of a special token,
            # start searching from the character after it
            # if reader[curly + _len_b] not in ("{",):
            #     curly += _len_b
            #     continue
            # When there are more than 2 curlies in a row, use the
            # innermost ones.  This is useful when generating languages
            # like latex where curlies are also meaningful
            # if (curly + _len_b + 1< reader.remaining() and
            #         reader[curly + 2] == '{' and reader[curly + 3] == '{'):
            #     curly += 1
            #     continue
            break

        # Append any text before the special token
        if curly > 0:
            cons = reader.consume(curly)
            body.chunks.append(_Text(cons, reader.line))

        start_brace = reader.consume(_len_b)
        line = reader.line

        # Template directives may be escaped as "{{!" or "{%!".
        # In this case output the braces and consume the "!".
        # This is especially useful in conjunction with jquery templates,
        # which also use double braces.
        # if reader.remaining() and reader[0] == "!":
        #     reader.consume(1)
        #     body.chunks.append(_Text(start_brace, line))
        #     continue

        # Multiple comment
        # if start_brace == "{{##":
        if reader[:2] == '##':
            end = reader.find(comment_end)
            if end == -1:
                raise ParseError("Missing end expression #} on line %s:%d" % (
                    filename, line))
            contents = reader.consume(end).strip()
            reader.consume(_len_comment)
            continue

        # Single comment
        # if start_brace == "{{#":
        if reader[0] == '#':
            end = reader.find(end_tag)
            if end == -1:
                raise ParseError("Missing end expression #} on line %s:%d" % (
                    filename, line))
            contents = reader.consume(end).strip()
            reader.consume(_len_b)
            continue

        # Expression
        # if start_brace == "{{":
        if reader[0] == "=":
            reader.consume(1)
            end = reader.find(end_tag)
            if end == -1:
                raise ParseError("Missing end expression %s on line %s:%d" % (
                    end_tag, filename, line))
            contents = reader.consume(end).strip()
            reader.consume(_len_e)
            if not contents:
                raise ParseError("Empty expression on line %s:%d" % (
                        filename, line))
            body.chunks.append(_Expression('escape(%s)' % contents, line))
            continue

        # Escape expression
        # if start_brace == '{{<<'
        if reader[:2] == "<<":
            reader.consume(2)
            end = reader.find(end_tag)
            if end == -1:
                raise ParseError("Missing end expression %s on line %s:%d" % (
                    end_tag, filename, line))
            contents = reader.consume(end).strip()
            reader.consume(_len_e)
            if not contents:
                raise ParseError("Empty expression on line %s:%d" % (
                    filename, line))
            body.chunks.append(_Expression(contents, line))
            continue

        # Block
        assert start_brace == begin_tag, start_brace
        end = reader.find(end_tag)
        if end == -1:
            raise ParseError("Missing end block %s on line %s:%d" % (end_tag,
                                                 filename, line))
        contents = reader.consume(end).strip()
        reader.consume(_len_e)
        if not contents:
            raise ParseError("Empty block tag (%s %s) on line %s:%d" % (begin_tag,
                                            end_tag, filename, line))

        operator, space, suffix = contents.partition(" ")
        suffix = suffix.strip()

        #just skip super
        if operator == 'super':
            warnings.simplefilter('default')
            warnings.warn("Super is not supported on line %s:%d." % (
                    filename, line
            ), DeprecationWarning)
            continue

        #multilines supports
        x_operator = operator.rstrip(':')
        if template.multilines and x_operator in ['else', 'elif', 'except',
              'finally', 'pass', 'try', 'if', 'for', 'while', 'break',
              'continue', 'def']:
            for i, x in enumerate(contents.splitlines()):
                txt = r_out_write.sub('_tt_write', x)
                txt = r_out_xml.sub('out_write', txt)
                body.chunks.append(_Statement(txt, line+i))
            continue

        # Intermediate ("else", "elif", etc) blocks
        intermediate_blocks = {
            "else": set(["if", "for", "while", "try"]),
            "elif": set(["if"]),
            "except": set(["try"]),
            "finally": set(["try"]),
        }
        allowed_parents = intermediate_blocks.get(x_operator)
        if allowed_parents is not None:
            if not in_block:
                raise ParseError("%s outside %s block on line %s:%d" %
                                (operator, allowed_parents, filename, line))
            if in_block not in allowed_parents:
                raise ParseError("%s block cannot be attached to %s block on line %s:%d" % (
                    operator, in_block, filename, line))
            body.chunks.append(_IntermediateControlBlock(contents, line))
            continue

        # End tag
        elif operator in ("end", 'pass'):
            if not in_block:
                raise ParseError("Extra %s end %s block on line %s:%d" % (begin_tag,
                                  end_tag, filename, line))
            return body

        elif operator in ("extend", "extends", "include", "embed",
                          "BEGIN_TAG", "END_TAG", "use", "link",
                          "head", "head_link"):
            if operator in ("extend", "extends"):
                if template.skip_extern: continue
                suffix = suffix.strip('"').strip("'")
                if not suffix:
                    raise ParseError("extends missing file path on line %s:%d" % (
                        filename, line))
                block = _ExtendsBlock(suffix)
            elif operator == "include":
                if template.skip_extern: continue
                suffix = suffix.strip('"').strip("'")
                if not suffix:
                    raise ParseError("include missing file path on line %s:%d" %
                                     (filename, line))
                block = _IncludeBlock(suffix, reader, line, template)
            elif operator == "use":
                block = _Use(suffix, line, template)
            elif operator == "link":
                block = _Link(suffix, line, template)
            elif operator == "head":
                block = _Head(suffix, line, template)
            elif operator == "head_link":
                block = _HeadLink(suffix, line, template)
            elif operator == "embed":
                # warnings.simplefilter('default')
                # warnings.warn("embed is not supported any more, just replace it with '<<'.", DeprecationWarning)
                block = _Expression(suffix, line)
            elif operator == "BEGIN_TAG":
                block = _Text(begin_tag, line)
            elif operator == "END_TAG":
                block = _Text(end_tag, line)
            body.chunks.append(block)
            continue

        elif operator in ("apply", "block", "try", "if", "for", "while"):
            # parse inner body recursively
            if operator in ("for", "while"):
                block_body = _parse(reader, template, operator, operator,
                                    begin_tag, end_tag, debug=debug, see=see)
            elif operator == "apply":
                # apply creates a nested function so syntactically it's not
                # in the loop.
                block_body = _parse(reader, template, operator, None,
                                    begin_tag, end_tag, debug=debug, see=see)
            else:
                block_body = _parse(reader, template, operator, in_loop,
                                    begin_tag, end_tag, debug=debug, see=see)

            if operator == "apply":
                if not suffix:
                    raise ParseError("apply missing method name on line %s:%d" % (filename,
                                  line))
                block = _ApplyBlock(suffix, line, block_body)
            elif operator == "block":
                if not suffix:
                    raise ParseError("block missing name on line %s:%d" % (filename, line))
                block = _NamedBlock(suffix, block_body, template, line)
            else:
                block = _ControlBlock(contents, line, block_body)
            body.chunks.append(block)
            continue

        elif operator == 'def':
            block_body = _parse(reader, template, operator, None,
                    begin_tag, end_tag, debug=debug, see=see)
            block = _ControlBlock(contents, line, block_body)
            body.chunks.append(block)
            continue

        elif operator in ("break", "continue"):
            if not in_loop:
                raise ParseError("%s outside %s block on line %s:%d" % (operator,
                                    set(["for", "while"]), filename, line))
            body.chunks.append(_Statement(contents, line))
            continue

        else:
            #check custom nodes
            if operator in __custom_nodes__:
                if template.skip_extern: continue

                NodeCls = __custom_nodes__[operator]
                if issubclass(NodeCls, BaseNode):
                    body.chunks.append(NodeCls(suffix, line))
                elif issubclass(NodeCls, BaseBlockNode):
                    block_body = _parse(reader, template, operator, in_block,
                            begin_tag, end_tag, debug=debug, see=see)
                    block = NodeCls(suffix, line, block_body)
                    body.chunks.append(block)
                else:
                    raise ParseError("Not support this custom node type %s on line %s:%d" %
                                     (NodeCls.__name__, filename, line)
                    )
            else:
                #add multiple lines support
                for i, x in enumerate(contents.splitlines()):
                    txt = r_out_write.sub('_tt_write', x)
                    txt = r_out_xml.sub('out_write', txt)
                    body.chunks.append(_Statement(txt, line+i))


def template(text, vars=None, env=None, **kwargs):
    t = Template(text, **kwargs)
    return t.generate(vars, env)

def template_py(text, **kwargs):
    t = Template(text, **kwargs)
    return t.code

def template_file(filename, vars=None, env=None, dirs=None, loader=None, layout=None, **kwargs):
    if not loader:
        loader = Loader(dirs, **kwargs)
    return loader.load(filename, layout=layout).generate(vars, env)

def template_file_py(filename, dirs=None, loader=None, layout=None, **kwargs):
    if not loader:
        loader = Loader(dirs, **kwargs)
    return loader.load(filename, layout=layout).code

