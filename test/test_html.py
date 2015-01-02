#coding=utf-8
from uliweb.core.js import simple_value, json_dumps
from uliweb.core.html import *
from uliweb.core.html import to_attrs

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

def testto_attrs():
    """
    >>> print to_attrs({'name':'title'})
     name="title"
    >>> print to_attrs({'_class':'color', 'id':'title'})
     class="color" id="title"
    >>> print to_attrs({'_class':'color', 'id':None})
     class="color"
    >>> print to_attrs({'_class':'color', 'checked':None})
     class="color" checked
    >>> print to_attrs({'_class':'color', '_for':None})
     class="color"
    >>> print to_attrs({'action': '', '_class': 'yform', 'method': 'POST'})
     class="yform" action="" method="POST"
    >>> print to_attrs({'action': '"hello"'})
     action="&quot;hello&quot;"
    >>> print to_attrs({'action': ''})
     action=""
    """
    
def test_json_dumps():
    """
    >>> import datetime
    >>> a = {'name':u'limodou', 'date':datetime.datetime(2010, 10, 25), 'data':{'name':'aaa', 'total': 100, 'has':True}}
    >>> json_dumps(a)
    '{"date":"2010-10-25 00:00:00","data":{"has":true,"total":100,"name":"aaa"},"name":"limodou"}'
    
    """
    
def test_tag():
    """
    >>> print Tag('a', 'Link', href='#')
    <a href="#">Link</a>
    >>> print Tag('a', 'Link', href='http://localhost:8000?a=b&c=d')
    <a href="http://localhost:8000?a=b&c=d">Link</a>
    >>> print Tag('p', 'Hello', attrs={'data-link':'ok'}, newline=False)
    <p data-link="ok">Hello</p>
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
    >>> div_group = Tag('div', _class='div', newline=True)
    >>> with div_group: 
    ...     div_group << Tag('label', 'Hello')
    >>> print div_group
    <div class="div">
        <label>Hello</label>
    </div>
    <BLANKLINE>
    >>> div = Tag('div', newline=True)
    >>> with div:
    ...     div.span('test', attrs={'data-target':"Hello"})
    >>> print div
    <div>
        <span data-target="Hello">test</span>
    </div>
    <BLANKLINE>
    """

def test_other():
    """
    >>> print Div('Test', _class='data-group')
    <div class="data-group">
    Test
    </div>
    <BLANKLINE>
    """
#if __name__ == '__main__':
#    import datetime
#    a = {'name':u'中文', 'date':datetime.datetime(2010, 10, 25), 'data':{'name':'aaa', 'total': 100, 'has':True}}
#    print json_dumps(a)
#    print json_dumps(a, indent=4)
#

def test_Table():
    """
    >>> print Table([['a', 'b']], head=['A', 'B'])
    <table>
        <thead>
            <tr>
                <th>A</th>
                <th>B</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>a</td>
                <td>b</td>
            </tr>
        </tbody>
    </table>
    <BLANKLINE>
    """