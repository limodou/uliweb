from __future__ import with_statement
import cgi
import StringIO
from uliweb.utils.common import safe_unicode, safe_str

__noescape_attrs__ = ['href', 'src']
class DefaultValue(object):pass

def u_str(v, encoding='utf-8'):
    if isinstance(v, str):
        pass
    elif isinstance(v, unicode):
        v = v.encode(encoding)
    else:
        v = str(v)
    return v

def str_u(v, encoding='utf-8'):
    if isinstance(v, unicode):
        return v
    else:
        return unicode(v, encoding)

def to_attrs(args, nocreate_if_none=['id', 'for', 'class']):
    """
    Make python dict to k="v" format
    """
    if not args:
        return ''
    s = ['']
    for k, v in sorted(args.items()):
        if k.startswith('_'):
            k = k[1:]
        if v is None:
            if k not in nocreate_if_none:
                s.append(k)
        else:
            if k.lower() in __noescape_attrs__:
                t = u_str(v)
            else:
                t = cgi.escape(u_str(v))
            t = '"%s"' % t.replace('"', '&quot;')
            s.append('%s=%s' % (k, t))
    return ' '.join(s)

__tags__ = {}

class Buf(object):
    def __init__(self, encoding='utf-8', newline=True):
        self._document = StringIO.StringIO()
        self._indentation = 0
        self._indent = ' '*4
        self._encoding = encoding
        self._builder = self
        self._newline = newline
        
    def bind(self, builder):
        self._builder = builder
        
    def __getattr__(self, name):
        tag = __tags__.get(name, Tag)
        t = tag(name)
        t.bind(self._builder)
        return t
    __getitem__ = __getattr__
    
    def __str__(self):
        return u_str(self._document.getvalue(), self._encoding)
    
    def __unicode__(self):
        return str_u(self._document.getvalue(), self._encoding)
    
    def _write(self, line):
        line = line.decode(self._encoding)
        if self._newline:
            n = '\n'
        else:
            n = ''
        self._document.write('%s%s%s' % (self._indentation * self._indent, line, n))
        
    def __lshift__(self, obj):
        if isinstance(obj, (tuple, list)):
            for x in obj:
                self._builder._write(u_str(x, self._encoding))
        else:
            self._builder._write(u_str(obj, self._encoding))

class Tag(Buf):
    def __init__(self, tag_name, _value=DefaultValue, encoding='utf-8', newline=False, attrs=None, **kwargs):
        Buf.__init__(self, encoding=encoding, newline=newline)
        self.name = tag_name
        self.attributes = attrs or {}
        self(_value, **kwargs)
#        if _value is None:
#            self._builder._write('<%s%s />' % (self.name, to_attrs(self.attributes)))
#        elif _value != DefaultValue:
#            self._builder._write('<%s%s>%s</%s>' % (self.name, to_attrs(self.attributes), u_str(_value), self.name))
    
    def __enter__(self):
        self._builder._write('<%s%s>' % (self.name, to_attrs(self.attributes)))
        self._builder._indentation += 1
        return self
    
    def __exit__(self, type, value, tb):
        self._builder._indentation -= 1
        self._builder._write('</%s>' % self.name)
        
    def __call__(self, _value=DefaultValue, attrs=None, **kwargs):
        attrs = attrs or {}
        self.attributes.update(attrs)
        self.attributes.update(kwargs)
        if _value is None:
            self._builder._write('<%s%s />' % (self.name, to_attrs(self.attributes)))
        elif _value != DefaultValue:
            if self._newline:
               self._builder._write('<%s%s>\n%s\n</%s>' % (self.name, to_attrs(self.attributes), u_str(_value, self._encoding), self.name))
            else:
                self._builder._write('<%s%s>%s</%s>' % (self.name, to_attrs(self.attributes), u_str(_value, self._encoding), self.name))
            return
        return self
    
class Div(Tag):
    def __init__(self, _value=DefaultValue, newline=True, **kwargs):
        Tag.__init__(self, tag_name='div', _value=_value, newline=newline, **kwargs)

__tags__['Div'] = Div

class Builder(object):
    """
    Builder can be used to create multiple parts of code, such as
    
    b = Builder('begin', 'body', 'end')
    
    Then you can put something to each part:
        
    b.begin << '<table>'
    b.body << '<tbody></tbody>'
    b.end << '</table>'
    
    Then you can output the result:
        
    print b.text
    print b.body
    """
    def __init__(self, *parts):
        self.parts = parts or ['body']
        self.data = {}
    
    def __getattr__(self, key):
        if not key in self.parts:
            raise KeyError("Can't find the key %s" % key)
        return self.data.setdefault(key, Buf())

    @property
    def text(self):
        txt = []
        for x in self.parts:
            v = self.data.get(x, '')
            txt.append(str(v))
        return ''.join(txt)
    
    def __str__(self):
        return safe_str(self.text)
        
    def __unicode__(self):
        return safe_unicode(self.text)

def begin_tag(tag, **kwargs):
    return '<%s%s>' % (tag, to_attrs(kwargs))

def end_tag(tag):
    return '</%s>' % tag

def Table(data, head=None, **kwargs):
    header = head or []
    table = Tag('table', newline=True, **kwargs)
    with table:
        if head:
            with table.thead as thead:
                with thead.tr as tr:
                    for h in header:
                        tr.th(h)
        if data:
            with table.tbody as tbody:
                for row in data:
                    with tbody.tr as tr:
                        for t in row:
                            tr.td(t)
    return table


if __name__ == '__main__':
    b = Buf()
    with b.html(name='xml'):
        b.head('Hello')
    print str(b)
    div = Tag('div', _class="demo", style="display:none")
    with div:
        with div.span:
            div.a('Test', href='#')
    print div
    print Tag('a', 'Link', href='#')
    print Tag('br', None)
    with div:
        with div.span:
            div.a('Test', href='#')
        div << '<p>This is a paragraph</p>'
    print div
    b = Buf()
    b << 'hello'
    b << [Tag('a', 'Link', href='#'), Tag('a', 'Link', href='#')]
    print str(b)
