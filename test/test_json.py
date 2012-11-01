#coding=utf8

def test():
    """
    >>> from uliweb import json_dumps
    >>> print json_dumps({'a':'中文'})
    {"a":"\xe4\xb8\xad\xe6\x96\x87"}
    >>> print json_dumps({'a':'中文'}, unicode=True)
    {"a":"\u4e2d\u6587"}
    >>> import datetime
    >>> print json_dumps({'a':1, 'b':True, 'c':False})
    {"a":1,"c":false,"b":true}
    >>> print json_dumps({1:1})
    {"1":1}
    >>> print json_dumps([1,2,3])
    [1,2,3]
    >>> print json_dumps((1,2,3))
    [1,2,3]
    >>> print json_dumps(12.2)
    12.2
    >>> import decimal
    >>> print json_dumps(decimal.Decimal("12.3"))
    12.3
    >>> print json_dumps(datetime.datetime(2011, 11, 8))
    "2011-11-08 00:00:00"
    >>> print json_dumps(['中文', unicode('中文', 'utf-8')])
    ["\xe4\xb8\xad\xe6\x96\x87","\xe4\xb8\xad\xe6\x96\x87"]
    >>> from uliweb.core.html import Builder
    >>> b = Builder('head', 'body', 'end')
    >>> b.head << '<h1>'
    >>> b.body << 'test'
    >>> b.end << '</h1>'
    >>> json_dumps({'b':b})
    '{"b":<h1>\ntest\n</h1>\n}'
    """
    
