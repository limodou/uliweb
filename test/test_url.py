import time, sys
sys.path.insert(0, '../uliweb/lib')
from uliweb import expose
from uliweb.core import rules

def test_1():
    """
    >>> rules.clear_rules()
    >>> def view():pass
    >>> f = expose('!/')(view)
    >>> rules.merge_rules() # doctest:+ELLIPSIS
    [('__main__', '__main__.view', '/', {})]
    >>> f = expose('/hello')(view)
    >>> rules.merge_rules() # doctest:+ELLIPSIS
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
    __main__.TestView.index /test
    __main__.TestView.ttt /ttt
    __main__.TestView1.index /test/index
    __main__.TestView1.pnt /print
    __main__.TestView1.test /test/test
    __main__.TestView1.ttt /test/ttt
    __main__.view /
    __main__.view /hello
    """
    
def test_endpoint():
    """
    >>> def view():pass
    >>> f = expose('/hello')(view)
    >>> rules.get_endpoint(f)
    '__main__.view'
    >>> rules.get_endpoint('views.index')
    'views.index'
    >>> rules.clear_rules()
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
    >>> @expose('/test')
    ... class TestView1(TestView):
    ...     @expose('/print')
    ...     def pnt(self):
    ...         return {}
    ...     def test(self):
    ...         pass
    >>> rules.get_endpoint(TestView.pnt)
    '__main__.TestView.pnt'
    >>> rules.get_endpoint(TestView1.pnt)
    '__main__.TestView1.pnt'
    """

def test_template():
    """
    >>> rules.clear_rules()
    >>> @expose('/view', template='test.html')
    ... def view():
    ...     pass
    >>> print view.__template__
    test.html
    >>> @expose('/view')
    ... def view():
    ...     pass
    >>> print view.__template__
    None
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
    >>> @expose('/test', replace=True)
    ... class TestView1(TestView):
    ...     @expose('/print')
    ...     def pnt(self):
    ...         return {}
    ...     @expose('/test', template='test.html')
    ...     def test(self):
    ...         pass
    >>> print TestView.index.__template__
    {'function': 'index', 'view_class': 'TestView', 'appname': '__main__'}
    >>> print TestView1.index.__template__
    {'function': 'index', 'view_class': 'TestView', 'appname': '__main__'}
    >>> print TestView1.pnt.__template__
    None
    >>> print TestView1.test.__template__
    test.html
    """

def test_template1():
    """
    >>> rules.clear_rules()
    >>> @expose('/view', template='test.html')
    ... def view():
    ...     pass
    >>> print view.__template__
    test.html
    >>> @expose('/view')
    ... def view():
    ...     pass
    >>> print view.__template__
    None
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
    >>> @expose('/test')
    ... class TestView1(TestView):
    ...     @expose('/print')
    ...     def pnt(self):
    ...         return {}
    ...     @expose('/test', template='test.html')
    ...     def test(self):
    ...         pass
    >>> print TestView.index.__template__
    None
    >>> print TestView1.index.__template__
    None
    >>> print TestView1.pnt.__template__
    None
    >>> print TestView1.test.__template__
    test.html
    """

def test_not_replace():
    """
    >>> rules.clear_rules()
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
    >>> @expose('/test1')
    ... class TestView1(TestView):
    ...     @expose('/print')
    ...     def pnt(self):
    ...         return {}
    ...     def test(self):
    ...         pass
    >>> for v in sorted(rules.merge_rules(), key=lambda x:(x[1], x[2])):
    ...     print v[1], v[2]
    __main__.TestView.index /test
    __main__.TestView.ttt /ttt
    __main__.TestView1.index /test1/index
    __main__.TestView1.pnt /print
    __main__.TestView1.test /test1/test
    __main__.TestView1.ttt /test1/ttt
    """

