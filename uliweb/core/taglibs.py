#!/usr/bin/env python
# Parse template tag and replace it
# Author: limodou
# inspired by xml2dict

import os
from xml.parsers import expat
from xml.sax.saxutils import XMLGenerator
from xml.sax.xmlreader import AttributesImpl
import re
try:  # pragma no cover
    from cStringIO import StringIO
except ImportError:  # pragma no cover
    try:
        from StringIO import StringIO
    except ImportError:
        from io import StringIO
try:  # pragma no cover
    from collections import OrderedDict
except ImportError:  # pragma no cover
    try:
        from ordereddict import OrderedDict
    except ImportError:
        OrderedDict = dict
from uliweb.core.template import LRUTmplatesCacheDict
from uliweb.utils.common import safe_str

try:  # pragma no cover
    _basestring = basestring
except NameError:  # pragma no cover
    _basestring = str
try:  # pragma no cover
    _unicode = unicode
except NameError:  # pragma no cover
    _unicode = str

__author__ = 'limodou'
__version__ = '0.1'
__license__ = 'MIT'


class ParsingInterrupted(Exception):
    pass


class _DictSAXHandler(object):
    def __init__(self,
                 item_depth=0,
                 item_callback=lambda *args: True,
                 xml_attribs=True,
                 attr_prefix='@',
                 cdata_key='_text',
                 force_cdata=False,
                 cdata_separator='',
                 postprocessor=None,
                 dict_constructor=OrderedDict,
                 strip_whitespace=True,
                 force_list=()):
        self.path = []
        self.stack = []
        self.data = None
        self.item = None
        self.item_depth = item_depth
        self.xml_attribs = xml_attribs
        self.item_callback = item_callback
        self.attr_prefix = attr_prefix
        self.cdata_key = cdata_key
        self.force_cdata = force_cdata
        self.cdata_separator = cdata_separator
        self.postprocessor = postprocessor
        self.dict_constructor = dict_constructor
        self.strip_whitespace = strip_whitespace
        self.force_list = force_list

    def _build_name(self, full_name):
        if ':' in full_name:
            return full_name.split(':', 1)[1]
        else:
            return full_name

    def _attrs_to_dict(self, attrs):
        if isinstance(attrs, dict):
            return attrs
        return self.dict_constructor(zip(attrs[0::2], attrs[1::2]))

    def startElement(self, full_name, attrs):
        name = self._build_name(full_name)
        attrs = self._attrs_to_dict(attrs)
        self.path.append((name, attrs or None))
        if len(self.path) > self.item_depth:
            self.stack.append((self.item, self.data))
            if self.xml_attribs:
                attrs = {'_attrs':attrs}
                # attrs = self.dict_constructor(
                #     (self.attr_prefix+self._build_name(key), value)
                #     for (key, value) in attrs.items())
            else:
                attrs = None
            self.item = attrs or None
            self.data = None

    def endElement(self, full_name):
        name = self._build_name(full_name)
        if len(self.path) == self.item_depth:
            item = self.item
            if item is None:
                item = self.data
            should_continue = self.item_callback(self.path, item)
            if not should_continue:
                raise ParsingInterrupted()
        if len(self.stack):
            item, data = self.item, self.data
            self.item, self.data = self.stack.pop()
            if self.strip_whitespace and data is not None:
                data = data.strip() or None
            if data and self.force_cdata and item is None:
                item = self.dict_constructor()
            if item is not None:
                if data:
                    self.push_data(item, self.cdata_key, data)
                self.item = self.push_data(self.item, name, item)
            else:
                self.item = self.push_data(self.item, name, data)
        else:
            self.item = self.data = None
        self.path.pop()

    def characters(self, data):
        if not self.data:
            self.data = data
        else:
            self.data += self.cdata_separator + data

    def push_data(self, item, key, data):
        if self.postprocessor is not None:
            result = self.postprocessor(self.path, key, data)
            if result is None:
                return item
            key, data = result
        if item is None:
            item = self.dict_constructor()
        try:
            value = item[key]
            if isinstance(value, list):
                value.append(data)
            else:
                item[key] = [value, data]
        except KeyError:
            if key in self.force_list:
                item[key] = [data]
            else:
                item[key] = data
        return item

def _to_attrs(attrs, args=None, **kwargs):
    if args and not isinstance(args, dict):
        raise ValueError("args should be a dict value, but {!r} found.".format(args))
    else:
        args = args or {}

    kwargs.update(args)
    for k, v in kwargs.items():
        value = attrs.setdefault(k, '')
        attrs[k] = value + ' ' + v
    return ' '.join(['{0}="{1}"'.format(k, safe_str(v)) for k, v in attrs.items()])

def _unparse(input_dict):
    return unparse(input_dict, child_only=True)

def _unparse_full(tag_name, input_dict):
    return unparse(input_dict, child_only=False, tag_name=tag_name)

class Loader(object):
    def __init__(self, tags=None, tags_dir=None, max_size=None, check_modified_time=False):
        self.tags = tags or {}
        self.tags_dir = tags_dir
        if not isinstance(tags_dir, (tuple, list)):
            self.tags_dir = [tags_dir]
        self.cache = LRUTmplatesCacheDict(max_size=max_size, check_modified_time=check_modified_time)

    def find(self, tag):
        if tag in self.tags:
            return self.tags[tag]
        if self.tags_dir:
            for path in self.tags_dir:
                tag_file = os.path.join(path, '{}.html'.format(tag.replace('.', '/')))
                if self.cache.has(tag_file):
                    return self.cache[tag_file]
                else:
                    if os.path.exists(tag_file):
                        with open(tag_file) as f:
                            text = f.read()
                            self.cache.set(tag_file, text)
                        return text
            raise ValueError("Tag {} template file {} can't be found".format(tag, tag_file))

        else:
            raise ValueError("Tag {} can't be found".format(tag))

    def available(self):
        return bool(self.tags or self.tags_dir)


def process_tag(data, tag, loader, log=None):
    from uliweb.core.template import template

    t = loader.find(tag)
    if not t:
        raise ValueError("Tag {} can't be found".format(tag))

    env = {'to_attrs':_to_attrs, 'xml':_unparse, 'xml_full':_unparse_full}

    return template(t, data, env=env, begin_tag='{%', end_tag='%}', log=log, multilines=True)



def parse(text, loader=None, namespace='t', begin_position=0, end_position=None, log=None):
    if not loader or not loader.available():
        return text
    r_tag = re.compile(r'<{0}:([a-zA-Z\._0-9]+?)[^>]*>(.*)</{0}:\1>'.format(namespace), re.I|re.M|re.S)
    result = []
    start = begin_position
    if not end_position:
        end_position = len(text)
    for b in r_tag.finditer(text, start, end_position):
        span = b.span()
        result.append(text[start:span[0]])

        #parse tag
        tag_name = b.group(1)
 
        #process child tag
        begin_txt = text[span[0]:b.span(2)[0]]
        end_txt = text[b.span(2)[1]:span[1]]
        new_txt = parse(text, loader=loader, namespace=namespace, 
            begin_position=b.span(2)[0], end_position=b.span(2)[1])
        data = parse_xml(''.join([begin_txt, new_txt, end_txt]), attr_prefix='')
        result.append(process_tag(data[tag_name], tag_name, loader, log=log))

        start = span[1]
    result.append(text[start:end_position])
    return ''.join(result)

def parse_xml(xml_input, encoding=None, expat=expat, **kwargs):
    """Parse the given XML input and convert it into a dictionary.

    `xml_input` can either be a `string` or a file-like object.

    If `xml_attribs` is `True`, element attributes are put in the dictionary
    among regular child elements, using `@` as a prefix to avoid collisions. If
    set to `False`, they are just ignored.

    Simple example::

        >>> import xmltodict
        >>> doc = xmltodict.parse(\"\"\"
        ... <a prop="x">
        ...   <b>1</b>
        ...   <b>2</b>
        ... </a>
        ... \"\"\")
        >>> doc['a']['_attrs']['prop']
        u'x'
        >>> doc['a']['b']
        [u'1', u'2']

    If `item_depth` is `0`, the function returns a dictionary for the root
    element (default behavior). Otherwise, it calls `item_callback` every time
    an item at the specified depth is found and returns `None` in the end
    (streaming mode).

    The callback function receives two parameters: the `path` from the document
    root to the item (name-attribs pairs), and the `item` (dict). If the
    callback's return value is false-ish, parsing will be stopped with the
    :class:`ParsingInterrupted` exception.

    Streaming example::

        >>> def handle(path, item):
        ...     print 'path:%s item:%s' % (path, item)
        ...     return True
        ...
        >>> xmltodict.parse(\"\"\"
        ... <a prop="x">
        ...   <b>1</b>
        ...   <b>2</b>
        ... </a>\"\"\", item_depth=2, item_callback=handle)
        path:[(u'a', {u'prop': u'x'}), (u'b', None)] item:1
        path:[(u'a', {u'prop': u'x'}), (u'b', None)] item:2

    The optional argument `postprocessor` is a function that takes `path`,
    `key` and `value` as positional arguments and returns a new `(key, value)`
    pair where both `key` and `value` may have changed. Usage example::

        >>> def postprocessor(path, key, value):
        ...     try:
        ...         return key + ':int', int(value)
        ...     except (ValueError, TypeError):
        ...         return key, value
        >>> xmltodict.parse('<a><b>1</b><b>2</b><b>x</b></a>',
        ...                 postprocessor=postprocessor)
        OrderedDict([(u'a', OrderedDict([(u'b:int', [1, 2]), (u'b', u'x')]))])

    You can pass an alternate version of `expat` (such as `defusedexpat`) by
    using the `expat` parameter. E.g:

        >>> import defusedexpat
        >>> xmltodict.parse('<a>hello</a>', expat=defusedexpat.pyexpat)
        OrderedDict([(u'a', u'hello')])

    You can use the force_list argument to force lists to be created even
    when there is only a single child of a given level of hierarchy. The
    force_list argument is a tuple of keys. If the key for a given level
    of hierarchy is in the force_list argument, that level of hierarchy
    will have a list as a child (even if there is only one sub-element).
    The index_keys operation takes precendence over this. This is applied
    after any user-supplied postprocessor has already run.

        For example, given this input:
        <servers>
          <server>
            <name>host1</name>
            <os>Linux</os>
            <interfaces>
              <interface>
                <name>em0</name>
                <ip_address>10.0.0.1</ip_address>
              </interface>
            </interfaces>
          </server>
        </servers>

        If called with force_list=('interface',), it will produce
        this dictionary:
        {'servers':
          {'server':
            {'name': 'host1',
             'os': 'Linux'},
             'interfaces':
              {'interface':
                [ {'name': 'em0', 'ip_address': '10.0.0.1' } ] } } }
    """
    handler = _DictSAXHandler(**kwargs)
    if isinstance(xml_input, _unicode):
        if not encoding:
            encoding = 'utf-8'
        xml_input = xml_input.encode(encoding)
    parser = expat.ParserCreate(
        encoding
    )
    try:
        parser.ordered_attributes = True
    except AttributeError:
        # Jython's expat does not support ordered_attributes
        pass
    parser.StartElementHandler = handler.startElement
    parser.EndElementHandler = handler.endElement
    parser.CharacterDataHandler = handler.characters
    parser.buffer_text = True
    try:
        parser.ParseFile(xml_input)
    except (TypeError, AttributeError):
        parser.Parse(xml_input, True)
    return handler.item


def unparse(input_dict, child_only=True, tag_name=None):
    result = []
    attrs = input_dict.pop('_attrs', {})
    if not child_only:
        if not tag_name:
            raise ValueError("tag_name can't be None")
        if attrs:
            result.append('<{0} {1}>'.format(tag_name, _to_attrs(attrs)))
        else:
            result.append('<{0}>'.format(tag_name))
    for key, value in input_dict.items():
        if key == '_text':
            result.append(value)
        else:
            result.append(unparse(value, child_only=False, tag_name=key))
    if not child_only:
        result.append('</{}>'.format(tag_name))

    return ''.join(result)

