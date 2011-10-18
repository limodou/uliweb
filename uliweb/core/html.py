from __future__ import with_statement
import cgi
import StringIO

__noescape_attrs__ = ['href', 'src']

def u_str(v, encoding='utf-8'):
    if isinstance(v, str):
        pass
    elif isinstance(v, unicode):
        v = v.encode(encoding)
    else:
        v = str(v)
    return v

def _create_kwargs(args, nocreate_if_none=['id', 'for']):
    """
    Make python dict to k="v" format
    
    >>> print _create_kwargs({'name':'title'})
     name="title"
    >>> print _create_kwargs({'_class':'color', 'id':'title'})
     class="color" id="title"
    >>> print _create_kwargs({'_class':'color', 'id':None})
     class="color"
    >>> print _create_kwargs({'_class':'color', 'checked':None})
     class="color" checked
    >>> print _create_kwargs({'_class':'color', '_for':None})
     class="color"
    >>> print _create_kwargs({'action': '', '_class': 'yform', 'method': 'POST'})
     class="yform" action="" method="POST"
    >>> print _create_kwargs({'action': '"hello"'})
     class="yform" action="" method="POST"
    
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
            if t and t[0] not in "\"'":
                t = '"%s"' % t
            elif not t:
                t = '""'
            s.append('%s=%s' % (k, t))
    return ' '.join(s)

__tags__ = {}

class Buf(object):
    def __init__(self, encoding='utf-8'):
        self._document = StringIO.StringIO()
        self._indentation = 0
        self._indent = ' '*4
        self._encoding = encoding
        self._builder = self
        
    def bind(self, builder):
        self._builder = builder
        
    def __getattr__(self, name):
        tag = __tags__.get(name, Tag)
        t = tag(name)
        t.bind(self._builder)
        return t
    __getitem__ = __getattr__
    
    def __str__(self):
        return self._document.getvalue().encode(self._encoding)
    
    def __unicode__(self):
        return self._document.getvalue().decode(self._encoding)
    
    def _write(self, line):
        line = line.decode(self._encoding)
        self._document.write('%s%s\n' % (self._indentation * self._indent, line))
        
    def __lshift__(self, obj):
        if isinstance(obj, (tuple, list)):
            for x in obj:
                self._builder._write(u_str(x, self._encoding))
        else:
            self._builder._write(u_str(obj, self._encoding))

class Tag(Buf):
    _dummy = {}
    def __init__(self, tag_name, _value=_dummy, encoding='utf-8', **kwargs):
        Buf.__init__(self, encoding=encoding)
        self.name = tag_name
        self.attributes = {}
        self(_value, **kwargs)
#        if _value is None:
#            self._builder._write('<%s%s />' % (self.name, _create_kwargs(self.attributes)))
#        elif _value != Tag._dummy:
#            self._builder._write('<%s%s>%s</%s>' % (self.name, _create_kwargs(self.attributes), u_str(_value), self.name))
    
    def __enter__(self):
        self._builder._write('<%s%s>' % (self.name, _create_kwargs(self.attributes)))
        self._builder._indentation += 1
        return self
    
    def __exit__(self, type, value, tb):
        self._builder._indentation -= 1
        self._builder._write('</%s>' % self.name)
        
    def __call__(self, _value=_dummy, **kwargs):
        self.attributes.update(kwargs)
        if _value is None:
            self._builder._write('<%s%s />' % (self.name, _create_kwargs(self.attributes)))
        elif _value != Tag._dummy:
            self._builder._write('<%s%s>%s</%s>' % (self.name, _create_kwargs(self.attributes), u_str(_value, self._encoding), self.name))
            return
        return self
    
class Script(Tag):
    def __init__(self, src=Tag._dummy, **kwargs):
        kwargs['type'] = 'text/javascript'
        if src != Tag._dummy:
            kwargs['src'] = src
            Tag.__init__(self, tag_name="script", _value='', **kwargs)
        else:
            Tag.__init__(self, tag_name="script", _value=Tag._dummy, **kwargs)
 
__tags__['script'] = Script

def begin_tag(tag, **kwargs):
    return '<%s%s>' % (tag, _create_kwargs(kwargs))

def end_tag(tag):
    return '</%s>' % tag

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
    script = Script()
    with script:
        script << "var flag=true;"
        script << "if (flag > 6)"
    print script
    
