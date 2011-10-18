#coding=utf-8
from uliweb.core.js import simple_value, json_dumps
from uliweb.core.html import *

def test_simple_value():
    """
    >>> simple_value(1)
    1
    >>> simple_value('abc')
    'abc'
    >>> import datetime
    >>> d = datetime.datetime(2010, 10, 25)
    >>> simple_value(d)
    '2010-10-25 00:00:00'
    >>> import decimal
    >>> d = decimal.Decimal('10.2')
    >>> simple_value(d)
    '10.2'
    >>> def call():
    ...     return 'bbb'
    >>> simple_value(call)
    'bbb'
    """

def test_json_dumps():
    """
    >>> import datetime
    >>> a = {'name':u'limodou', 'date':datetime.datetime(2010, 10, 25), 'data':{'name':'aaa', 'total': 100, 'has':True}}
    >>> json_dumps(a)
    '{"date": "2010-10-25 00:00:00", "data": {"has": true, "total": 100, "name": "aaa"}, "name": "limodou"}'
    
    """
    
def test_tag():
    """
    >>> print Tag('a', 'Link', href='#')
    <a href="#">Link</a>
    <BLANKLINE>
    >>> print Tag('a', 'Link', href='http://localhost:8000?a=b&c=d')
    <a href="http://localhost:8000?a=b&c=d">Link</a>
    <BLANKLINE>
    >>> print Script(src="jquery.js")
    <script src="jquery.js" type="text/javascript"></script>
    <BLANKLINE>
    >>> html = Buf()
    >>> with html.html:
    ...     with html.head:
    ...         html.title('Test')
    >>> print html
    <html>
        <head>
            <title>Test</title>
        </head>
    </html>
    <BLANKLINE>
    >>> script = Script()
    >>> with script:
    ...     script << "var flag=true;"
    ...     script << "if (flag > 6)"
    >>> print script
    <script type="text/javascript">
        var flag=true;
        if (flag > 6)
    </script>
    <BLANKLINE>
    """
#if __name__ == '__main__':
#    import datetime
#    a = {'name':u'中文', 'date':datetime.datetime(2010, 10, 25), 'data':{'name':'aaa', 'total': 100, 'has':True}}
#    print json_dumps(a)
#    print json_dumps(a, indent=4)
#    