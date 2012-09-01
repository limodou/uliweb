import time, sys
sys.path.insert(0, '../uliweb/lib')
from uliweb import expose
from uliweb.core import rules

def test_1():
    """
    >>> def view():pass
    >>> f = expose('!/')(view)
    >>> rules.merge_rules()
    [('__main__', '__main__.view', '/', {})]
    >>> f = expose('/hello')(view)
    >>> rules.merge_rules()
    [('__main__', '__main__.view', '/', {}), ('__main__', '__main__.view', '/hello', {})]
    >>> @expose('/test')
    ... class TestView(object):
    ...     @expose('')
    ...     def index(self):
    ...         return {}
    ... 
    ...     @expose('!/ttt')
    ...     def ttt(self):
    ...         return {}
    ... 
    ...     @expose('/print')
    ...     def pnt(self):
    ...         return {}
    >>> rules.merge_rules()
    [('__main__', '__main__.TestView.index', '/test', {}), ('__main__', '__main__.TestView.pnt', '/print', {}), ('__main__', '__main__.TestView.ttt', '/ttt', {}), ('__main__', '__main__.view', '/', {}), ('__main__', '__main__.view', '/hello', {})]
    """