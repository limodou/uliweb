from uliweb.utils.common import *

def test_query_string():
    """
    >>> a = 'http://localhost:8000/index?a=1'
    >>> q = QueryString(a)
    >>> str(q)
    'http://localhost:8000/index?a=1'
    >>> q['a'] = 2
    >>> str(q)
    'http://localhost:8000/index?a=2'
    >>> q.set('a', 3) # doctest:+ELLIPSIS
    <uliweb.utils.common.QueryString object at ...>
    >>> str(q)
    'http://localhost:8000/index?a=2&a=3'
    >>> q['b'] = 4
    >>> str(q)
    'http://localhost:8000/index?a=2&a=3&b=4'
    >>> query_string(a, a=2)
    'http://localhost:8000/index?a=2'
    >>> query_string(a, a=2, replace=False)
    'http://localhost:8000/index?a=1&a=2'
    >>> query_string(a, b=4, replace=False)
    'http://localhost:8000/index?a=1&b=4'
    """
    
def test_serial():
    """
    >>> from uliweb.utils import date
    >>> import datetime
    >>> a = {'a':'hello', 'b':12, 'c':date.now()}
    >>> s = Serial.dump(a)
    >>> b = Serial.load(s)
    >>> a == b
    True
    """
    
def test_serial_json():
    """
    >>> a = {'a':'hello', 'b':12}
    >>> s = Serial.dump(a, 'json')
    >>> b = Serial.load(s, 'json')
    >>> a == b
    True
    """

def test_import_attr():
    """
    >>> f = import_attr('datetime:datetime.ctime')
    >>> f.__name__
    ctime
    """