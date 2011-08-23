try:
    import json as JSON
except:
    import simplejson as JSON
import datetime
import decimal

#TAB = 4
#SIMPLE_IDEN = True
#
def simple_value(v):
    from uliweb.i18n.lazystr import LazyString
    
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
    elif isinstance(v, LazyString):
        return str(v)
    else:
        return v

def _encode(encoding='utf-8'):
    def _f(v, encoding='utf-8'):
        if isinstance(v, unicode):
            _v = v.encode(encoding)
        else:
            _v = v
        return JSON.encoder.encode_basestring(_v)
    return _f
    
class ComplexEncoder(JSON.JSONEncoder):
    def _iterencode(self, o, markers=None):
        if isinstance(o, basestring):
            if self.ensure_ascii:
                encoder = JSON.encoder.encode_basestring_ascii
            else:
                encoder = _encode(self.encoding)
            _encoding = self.encoding
            if (_encoding is not None and isinstance(o, str)
                    and not (_encoding == 'utf-8')):
                o = o.decode(_encoding)
            yield encoder(o)
        elif o is None:
            yield 'null'
        elif o is True:
            yield 'true'
        elif o is False:
            yield 'false'
        elif isinstance(o, (int, long)):
            yield str(o)
        elif isinstance(o, float):
            yield JSON.encoder.floatstr(o, self.allow_nan)
        elif isinstance(o, (list, tuple)):
            for chunk in self._iterencode_list(o, markers):
                yield chunk
        elif isinstance(o, dict):
            for chunk in self._iterencode_dict(o, markers):
                yield chunk
        else:
            if markers is not None:
                markerid = id(o)
                if markerid in markers:
                    raise ValueError("Circular reference detected")
                markers[markerid] = o
            for chunk in self._iterencode_default(o, markers):
                yield chunk
            if markers is not None:
                del markers[markerid]
    
    def default(self, obj):
        return simple_value(obj)
    
def json_dumps(obj, ensure_ascii=False, **kwargs):
    return JSON.dumps(obj, cls=ComplexEncoder, ensure_ascii=ensure_ascii, **kwargs)
    
def urlencode(data):
    from uliweb.utils.common import simple_value
    import urllib
    
    s = []
    if isinstance(data, dict):
        items = data.iteritems()
    elif isinstance(data, (tuple, list)):
        items = data
    else:
        raise Exception, "Can't support this data type %r" % data
    
        for k, v in items:
            if isinstance(v, (tuple, list)):
                for x in v:
                    s.append((k, simple_value(x)))
            else:
                s.append((k, simple_value(v)))
    return urllib.urlencode(s)

#def dumps(obj):
#    return JSON.dumps(obj, cls=ComplexEncoder)
#
#class B(object):
#    def __init__(self, value=None):
#        self.value = value
#        self.parent = None
#        
#    def __str__(self):
#        return self.value
#    
#    def __call__(self):
#        return self.__str__()
#    
#class C(B):
#    def __call__(self):
#        return self.value
#    
#class U(B):
#    def __str__(self):
#        return S(self.value)
#    
#    def __call__(self):
#        return self.__str__()
#    
#def S(value, tab=0):
#    if isinstance(value, dict):
#        s = []
#        length = len(value)
#        s.insert(0, '{')
#        for i, j in enumerate(value.items()):
#            k, v = j
#            if i != length-1:
#                ending = ','
#            else:
#                ending = ''
#            if SIMPLE_IDEN and k.isalpha() and k not in ['class']:
#                s.append((tab+TAB) * ' ' + '%s: %s%s' % (S(k), S(v, tab+TAB), ending))
#            else:
#                s.append((tab+TAB) * ' ' + '%s: %s%s' % (S(k, tab+TAB), S(v, tab+TAB), ending))
#        s.append(tab*' ' + '}')
#        return '\n'.join(s)
#    elif isinstance(value, (tuple, list)):
#        s = []
#        s.append('[')
#        length = len(value)
#        for i, k in enumerate(value):
#            if i != length-1:
#                ending = ','
#            else:
#                ending = ''
#            s.append((tab+TAB) * ' ' + '%s%s' % (S(k, tab+TAB), ending))
#        s.append(tab*' ' + ']')
#        return '\n'.join(s)
#    elif isinstance(value, C):
#        return str(value)
#    elif isinstance(value, datetime.datetime):
#        return '"%s"' % value.strftime('%Y-%m-%d %H:%M:%S')
#    elif isinstance(value, datetime.date):
#        return '"%s"' % value.strftime('%Y-%m-%d')
#    elif isinstance(value, datetime.time):
#        return '"%s"' % value.strftime('%H:%M:%S')
#    elif isinstance(value, decimal.Decimal):
#        return str(value)
#    elif isinstance(value, str):
#        return '"' + value + '"'
#    else:
#        return dumps(value)
#
#class Var(B):
#    def __init__(self, name, value=None):
#        B.__init__(self, value)
#        self.name = name
#        
#    def __str__(self):
#        return 'var %s = %s;' % (self.name, S(self.value))
#    
#    def __call__(self):
#        return self.name
#    
#    def __getattr__(self, name):
#        return self.call(name)
#    
#    def call(self, name):
#        def r(*args):
#            if self.parent:
#                self.parent<<'%s.%s(%s);' % (self.name, name, ','.join(map(S, args)))
#        return r
#
#class Call(B):
#    def __init__(self, name, *args):
#        B.__init__(self)
#        self.name = name
#        self.args = args
#        
#    def __str__(self):
#        return '%s(%s);' % (self.name, ','.join(map(S, self.args)))
#    
#class New(B):
#    def __init__(self, value, *kwargs):
#        B.__init__(self, value)
#        self.kwargs = kwargs
#    
#    def __str__(self):
#        args = []
#        for i in self.kwargs:
#            if i is None:
#                continue
#            if isinstance(i, Var):
#                args.append(i.name)
#            else:
#                args.append(S(i))
#        return 'new %s(%s)' % (self.value, ','.join(args))
#    
#class Line(B):
#    def __str__(self):
#        v = str(self.value).strip()
#        if not v.endswith(';'):
#            return "%s;" % v
#        else:
#            return "%s" % v
#
#class CssLink(B):
#    def __init__(self, value=None, static_suffix=''):
#        B.__init__(self, value)
#        self.static_suffix = static_suffix
#        self.link = os.path.join(self.static_suffix, self.value)
#
#    def __str__(self):
#        return '<link rel="stylesheet" type="text/css" href="%s"/>' % self.link
#    
#class ScriptLink(B):
#    def __init__(self, value=None, static_suffix=''):
#        B.__init__(self, value)
#        self.static_suffix = static_suffix
#        self.link = os.path.join(self.static_suffix, self.value)
#
#    def __str__(self):
#        return '<script type="text/javascript" src="%s"></script>' % self.link
#        
#class Buf(B):
#    def __init__(self):
#        B.__init__(self)
#        self.buf = []
#    
#    def __lshift__(self, obj):
#        if not obj:
#            return None
#        if isinstance(obj, (tuple, list)):
#            self.buf.extend(obj)
#        else:
#            self.buf.append(obj)
#            obj = [obj]
#        for o in obj:
#            if isinstance(o, B):
#                o.parent = self
#        return obj[0]
#        
#    def __str__(self):
#        return self.render()
#        
#    def render(self):
#        return '\n'.join([str(x) for x in self.buf])
#    
#class LinkBuf(Buf):
#    def render(self):
#        s = []
#        for x in self.buf:
#            t = str(x)
#            if t not in s:
#                s.append(t)
#        return '\n'.join(s)
#        
#class Quote(Buf):
#    def __init__(self, begin='', end=''):
#        Buf.__init__(self)
#        self.begin = begin
#        self.end = end
#        
#    def render(self):
#        s = [self.begin]
#        s.append(Buf.render(self))
#        s.append(self.end)
#        return '\n'.join(s)
#        
#class Function(Quote):
#    def __init__(self, name='', args=[], content=''):
#        Quote.__init__(self, 'function ' + name + '(%s){', '}')
#        self.args = args
#        self.buf.append(content)
#        
#    def render(self):
#        if self.args:
#            s = [self.begin % ','.join(self.args)]
#        else:
#            s = [self.begin % '']
#        s.append(Buf.render(self))
#        s.append(self.end)
#        return '\n'.join(s)
#    
#class Script(Quote):
#    def __init__(self):
#        Quote.__init__(self, '<script type="text/javascript">', '</script>')
#    
#    def render(self):
#        content = Buf.render(self)
#        if content:
#            s = [self.begin]
#            s.append(content)
#            s.append(self.end)
#            return '\n'.join(s)
#        else:
#            return ''
#    
#class Style(Script):
#    def __init__(self):
#        Quote.__init__(self, '<style type="text/css">', '</style>')
#    
#if __name__ == '__main__':
#    ds = Var('ds', New('Ext.data.JsonStore', {
#        'url': '/Address/default/ajax_all/',
#        'root': "rows",
#        'fields': ['name', 'telphone']
#    }))
#    
#
#    print ds