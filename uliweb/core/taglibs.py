#!/usr/bin/env python
# Parse template tag and replace it
# Author: limodou
# inspired by xml2dict

import os
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

def _get_list(v):
    v = v or []
    if not isinstance(v, (tuple, list)):
        return [v]
    else:
        return v

def _get_options(v):
    d = {}
    for x in _get_list(v):
        d[x['_attrs']['name']] = x['_text']
    return d

def _has_attr(v, attr):
    if not v:
        return False
    return attr in v.get('_attrs', {})

def _get_attr(v, attr=None):
    if not v:
        return ''
    if not attr:
        return v.get('_attrs', {})
    return v.get('_attrs', {}).get(attr, '')

def _get_text(v):
    if not v:
        return ''
    return v.get('_text', '')

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

    env = {'to_attrs':_to_attrs, 'xml':_unparse, 'xml_full':_unparse_full,
           'get_list':_get_list, 'get_options':_get_options, 'has_attr':_has_attr,
           'get_attr':_get_attr, 'get_text':_get_text}

    return template(t, data, env=env, begin_tag='{%', end_tag='%}', log=log, multilines=True)

class ParseError(Exception):pass

class ParseXML(object):
    r_space = re.compile(r'\s*')
    r_begin_tag = re.compile(r'<(t:)?([a-zA-Z\._0-9:]+)[^>]*>', re.I|re.DOTALL)
    r_end_tag = re.compile(r'</(?:t:)?([a-zA-Z\._0-9:]+)>', re.I|re.DOTALL)
    r_string1 = re.compile(r'"([^"\\]*(?:\\.[^"\\]*)*)"', re.I|re.DOTALL)
    r_string2 = re.compile(r"'([^'\\]*(?:\\.[^'\\]*)*)'", re.I|re.DOTALL)
    r_string3 = re.compile(r"(\S+)", re.I|re.DOTALL)
    r_attrname = re.compile(r"([a-zA-Z\._0-9]+)", re.I|re.DOTALL)
    r_equal = re.compile(r'\s*=\s*')
    r_text = re.compile(r'[^<]*', re.I|re.DOTALL)

    def __init__(self, text, pos=0, log=None, encoding='utf8'):
        self.text = text
        self.pos = pos
        self.attrs = OrderedDict()
        self.stack = []
        self.log = log
        self.top = self.attrs
        self.tag = None
        self.encoding = encoding

    def decode(self, s):
        return unicode(s, self.encoding)

    def match(self, text):
        return self.text[self.pos:self.pos+len(text)] == text

    def feed(self, r):
        b = r.match(self.text, self.pos)
        if b:
            self.pos = b.span()[1]
        return b

    def parse_end_tag(self):
        b = self.feed(self.r_end_tag)
        if b:
            tag_name = self.decode(b.group(1))
            #pop up tag
            for t in reversed(self.stack):
                self.stack.pop()
                if t == tag_name:
                    break
            self.top = self.attrs
            for t in self.stack:
                self.top = self.top[t]
            if not self.stack:
                return False #If finished
            else:
                return True
        else:
            raise ParseError('End tag {} is not correct'.format(self.text[self.pos:20]))

    def parse_begin_tag(self):
        b = self.feed(self.r_begin_tag)
        if b:
            tag_name = self.decode(b.group(2))
            self.stack.append(tag_name)
            if not self.tag:
                self.tag = tag_name
            top = {'_attrs':OrderedDict(), '_text':''}
            top_v = self.top.get(tag_name)
            if top_v:
                if isinstance(top_v, list):
                    top_v.append(top)
                else:
                    self.top[tag_name] = [top_v, top]
            else:
                self.top[tag_name] = top
            self.top = top
            text = self.text[b.span(2)[1]:b.span()[1]-1]
            pos = 0
            text_len = len(text)
            while pos < text_len:
                b = self.r_space.match(text, pos)
                if b:
                    pos = b.span()[1]
                if pos >= text_len:break
                #get attrname
                b = self.r_attrname.match(text, pos)
                if b:
                    attrname = self.decode(b.group())
                    pos = b.span()[1]
                else:
                    raise ParseError("No attrname found in {}".format(text))
                #guess =
                b = self.r_equal.match(text, pos)
                if b:
                    pos = b.span()[1]
                    if text[pos] == '"':
                        b = self.r_string1.match(text, pos)
                    elif text[pos] == "'":
                        b = self.r_string2.match(text, pos)
                    else:
                        b = self.r_string3.match(text, pos)
                    if b:
                        attrvalue = self.decode(b.group(1))
                        pos = b.span()[1]
                else:
                    attrvalue = attrname
                self.top['_attrs'][attrname] = attrvalue

        else:
            raise ParseError('Begin tag {} is not correct'.format(self.text[self.pos:20]))

    def parse(self):
        while self.pos < len(self.text):
            if self.match('<'): #tag process
                if self.match('</'):
                    if not self.parse_end_tag():
                        break
                elif self.match('<![CDATA['):
                    end_pos = self.text.find(']]>', self.pos+9)
                    if end_pos != -1:
                        self.top['_text'] += self.decode(self.text[self.pos+9:end_pos].strip())
                        self.pos = end_pos + 3
                    else:
                        raise ParseError("<![CDATA[ is not completed!")
                elif self.match('<![['):
                    end_pos = self.text.find(']]>', self.pos+4)
                    if end_pos != -1:
                        self.top['_text'] += self.decode(self.text[self.pos+4:end_pos].strip())
                        self.pos = end_pos + 3
                    else:
                        raise ParseError("<![[ is not completed!")
                elif self.match('<!--'):
                    end_pos = self.text.find('-->', self.pos+4)
                    if end_pos != -1:
                        self.pos = end_pos + 3
                    else:
                        raise ParseError("Comment is not completed!")
                else:
                    self.parse_begin_tag()
            else:
                b = self.feed(self.r_text)
                if b and self.stack:
                    self.top['_text'] += self.decode(b.group().strip())

def parse_xml(text, log=None):
    p = ParseXML(text, 0, log)
    p.parse()
    return p.attrs

r_tag = re.compile(r'<t:([a-zA-Z\._0-9]+?)[^>]*>', re.I|re.M|re.S)
def parse(text, loader=None, begin_position=0, end_position=None, log=None):
    if not loader or not loader.available():
        return text
    start = begin_position
    if not end_position:
        end_position = len(text)
    result = []
    for b in r_tag.finditer(text, start, end_position):
        span = b.span()
        result.append(text[start:span[0]])
        p = ParseXML(text, b.span()[0], log)
        p.parse()
        # print_dict(p.attrs)
        result.append(process_tag(p.attrs[p.tag], p.tag, loader, log=log))
        start = p.pos

    result.append(text[start:end_position])
    return ''.join(result)

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

def print_dict(d, tabstop=1):
    print '{'
    for k, v in d.items():
        print ' '*tabstop*4, repr(k), ':',
        if isinstance(v, OrderedDict):
            print_dict(v, tabstop+1)
        else:
            print repr(v)
    print ' '*(tabstop-1)*4, '}'

if __name__ == '__main__':
    tags = {'panel':
"""<div {%=to_attrs(_attrs, {'class':'panel'})%}>
  <div class="panel-head">
    <h3>{%<< xml(head)%}</h3>
    {% if defined('button'):%}
        {%<< xml_full('button', button)%}
    {%pass%}
  </div>
</div>""",
            'listview':
    """<div {%=to_attrs(_attrs)%}></div>""",
            'button':
    """<button class="btn btn-{%=_attrs['class']%}">{%=_text%}</button>"""
    }

    loader = Loader(tags=tags, tags_dir='taglibs')

    a = """<t:listview id="{{<< request.url}}" url="'abc'" id='table1'>
    <pagination>1
    </pagination>
</t:listview>

<t:listview id="{{<< request.url}}" url="'abc'" id='table2'>
    <pagination>1
    </pagination>
    <pagination>2
    </pagination>
</t:listview>"""
    # print parse_(a, loader)


    t = """
Text
<t:panel a="b">
<head>head</head>
</t:panel>
End"""
    print parse(t, loader)


    t = """
Text
<t:panel a="b">
<head>head</head>
<t:button class="primary">Submit</t:button>
</t:panel>
End"""
    print parse(t, loader) # doctest: +REPORT_UDIFF

    t = """<t:form_input_field name="title" label="label" required="required">
<input type="text" value="value" placeholder="placeholder" help="help">
<![CDATA[
<h3>CDATA</h3>
]]>
</input>
</t:form_input_field>
"""
    print parse_xml(t)