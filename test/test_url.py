import time, sys
sys.path.insert(0, '../uliweb/lib')
from uliweb import expose
from uliweb.core import rules

def test_1():
    """
    >>> def view():pass
    >>> f = expose('!/')(view)
    >>> rules.merge_rules() # doctest:+ELLIPSIS
    [('__main__', '__main__.view', '/', {}, datetime.datetime...)]
    >>> f = expose('/hello')(view)
    >>> rules.merge_rules() # doctest:+ELLIPSIS
    [('__main__', '__main__.view', '/', {}, datetime.datetime...), ('__main__', '__main__.view', '/hello', {}, datetime.datetime...)]
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
    >>> for v in sorted(rules.merge_rules(), key=lambda x:(x[1], x[2])):
    ...     print v[1], v[2]
    __main__.TestView.index /test
    __main__.TestView.pnt /print
    __main__.TestView.ttt /ttt
    __main__.view /
    __main__.view /hello
    >>> @expose('/test')
    ... class TestView1(TestView):
    ...     @expose('/print')
    ...     def pnt(self):
    ...         return {}
    ...     def test(self):
    ...         pass
    >>> for v in sorted(rules.merge_rules(), key=lambda x:(x[1], x[2])):
    ...     print v[1], v[2]
    __main__.TestView1.index /test
    __main__.TestView1.pnt /print
    __main__.TestView1.test /test/test
    __main__.TestView1.ttt /ttt
    __main__.view /
    __main__.view /hello
    """