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
    [('test_url', 'test_url.view', '/', {})]
    >>> f = expose('/hello')(view)
    >>> rules.merge_rules() # doctest:+ELLIPSIS
    [('test_url', 'test_url.view', '/', {}), ('test_url', 'test_url.view', '/hello', {})]
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
    test_url.TestView.index /test
    test_url.TestView.pnt /print
    test_url.TestView.ttt /ttt
    test_url.view /
    test_url.view /hello
    >>> @expose('/test')
    ... class TestView1(TestView):
    ...     @expose('/print')
    ...     def pnt(self):
    ...         return {}
    ...     def test(self):
    ...         pass
    >>> for v in sorted(rules.merge_rules(), key=lambda x:(x[1], x[2])):
    ...     print v[1], v[2]
    test_url.TestView.index /test
    test_url.TestView1.index /test/index
    test_url.TestView1.pnt /print
    test_url.TestView1.test /test/test
    test_url.TestView1.ttt /ttt
    test_url.view /
    test_url.view /hello
    """
    
def test_endpoint():
    """
    >>> def view():pass
    >>> f = expose('/hello')(view)
    >>> rules.get_endpoint(f)
    'test_url.view'
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
    'test_url.TestView.pnt'
    >>> rules.get_endpoint(TestView1.pnt)
    'test_url.TestView1.pnt'
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
    {'function': 'index', 'view_class': 'TestView', 'appname': 'test_url'}
    >>> print TestView1.index.__template__
    {'function': 'index', 'view_class': 'TestView', 'appname': 'test_url'}
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
    test_url.TestView.index /test
    test_url.TestView1.index /test1/index
    test_url.TestView1.pnt /print
    test_url.TestView1.test /test1/test
    test_url.TestView1.ttt /ttt
    >>> @expose('/test2')
    ... class TestView2(TestView):
    ...     @expose('/print')
    ...     def pnt(self):
    ...         return {}
    ...     def test(self):
    ...         pass
    >>> for v in sorted(rules.merge_rules(), key=lambda x:(x[1], x[2])):
    ...     print v[1], v[2]
    test_url.TestView.index /test
    test_url.TestView1.index /test1/index
    test_url.TestView1.test /test1/test
    test_url.TestView2.index /test2/index
    test_url.TestView2.pnt /print
    test_url.TestView2.test /test2/test
    test_url.TestView2.ttt /ttt
    """

def test_subdomain():
    """
    >>> rules.clear_rules()
    >>> def view():pass
    >>> f = expose('!/')(view)
    >>> rules.merge_rules() # doctest:+ELLIPSIS
    [('test_url', 'test_url.view', '/', {})]
    >>> f = expose('/hello')(view)
    >>> rules.merge_rules() # doctest:+ELLIPSIS
    [('test_url', 'test_url.view', '/', {}), ('test_url', 'test_url.view', '/hello', {})]
    >>> f = expose('/hello', subdomain='www')(view)
    >>> rules.merge_rules() # doctest:+ELLIPSIS
    [('test_url', 'test_url.view', '/', {}), ('test_url', 'test_url.view', '/hello', {}), ('test_url', 'test_url.view', '/hello', {'subdomain': 'www'})]
    >>> @expose('/test', subdomain='www')
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
    ...     print v[1], v[2], v[3]
    test_url.TestView.index /test {'subdomain': 'www'}
    test_url.TestView.pnt /print {'subdomain': 'www'}
    test_url.TestView.ttt /ttt {'subdomain': 'www'}
    test_url.view / {}
    test_url.view /hello {}
    test_url.view /hello {'subdomain': 'www'}
    >>> @expose('/test', subdomain='demo')
    ... class TestView1(TestView):
    ...     @expose('/print')
    ...     def pnt(self):
    ...         return {}
    ...     def test(self):
    ...         pass
    >>> for v in sorted(rules.merge_rules(), key=lambda x:(x[1], x[2])):
    ...     print v[1], v[2], v[3]
    test_url.TestView.index /test {'subdomain': 'www'}
    test_url.TestView.pnt /print {'subdomain': 'www'}
    test_url.TestView.ttt /ttt {'subdomain': 'www'}
    test_url.TestView1.index /test/index {'subdomain': 'demo'}
    test_url.TestView1.pnt /print {'subdomain': 'demo'}
    test_url.TestView1.test /test/test {'subdomain': 'demo'}
    test_url.TestView1.ttt /ttt {'subdomain': 'demo'}
    test_url.view / {}
    test_url.view /hello {}
    test_url.view /hello {'subdomain': 'www'}
    """


def test_app_subdomain():
    """
    >>> rules.clear_rules()
    >>> rules.__app_rules__ = {'test_url':{'subdomain':'test'}}
    >>> def view():pass
    >>> f = expose('/hello')(view)
    >>> @expose('/test', subdomain='www')
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
    ...     print v[1], v[2], v[3]
    test_url.TestView.index /test {'subdomain': 'test'}
    test_url.TestView.pnt /print {'subdomain': 'test'}
    test_url.TestView.ttt /ttt {'subdomain': 'test'}
    test_url.view /hello {'subdomain': 'test'}
    """

def test_app_prefix():
    """
    >>> rules.clear_rules()
    >>> rules.__app_rules__ = {'test_url':{'prefix':'/demo'}}
    >>> def view():pass
    >>> f = expose('/hello')(view)
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
    ...     print v[1], v[2], v[3]
    test_url.TestView.index /demo/test {}
    test_url.TestView.pnt /demo/print {}
    test_url.TestView.ttt /ttt {}
    test_url.view /demo/hello {}
    """

def test_url_route():
    """
    >>> rules.clear_rules()
    >>> rules.set_app_rules()
    >>> rules.set_urlroute_rules({'0':
    ...     ('/test', '/demo'),
    ...     '1':('(/hhhh)', r'/name\\1'),
    ... })
    >>> def view():pass
    >>> f = expose('/hello')(view)
    >>> @expose('/test')
    ... class TestView(object):
    ...     def index(self):
    ...         return {}
    ...
    ...     @expose('/hhhh/hello')
    ...     def ttt(self):
    ...         return {}
    ...
    >>> for v in sorted(rules.merge_rules(), key=lambda x:(x[1], x[2])):
    ...     print v[1], v[2], v[3]
    test_url.TestView.index /demo/index {}
    test_url.TestView.ttt /name/hhhh/hello {}
    test_url.view /hello {}

    """

def test_multi_expose():
    """
    >>> rules.clear_rules()
    >>> rules.__app_rules__ = {}
    >>> rules.set_urlroute_rules([])
    >>> @expose('/test')
    ... class TestView(object):
    ...     @expose('')
    ...     @expose('/')
    ...     def index(self):
    ...         return {}
    ...     @expose('a')
    ...     @expose('/d')
    ...     def test(self):
    ...         return {}
    ...
    >>> for v in sorted(rules.merge_rules(), key=lambda x:(x[1], x[2])):
    ...     print v[1], v[2], v[3]
    test_url.TestView.index / {}
    test_url.TestView.index /test {}
    test_url.TestView.test /d {}
    test_url.TestView.test /test/a {}

    """

def init_env():
    class Application(object):
        domains = {'default': {'domain':'', 'display':False, 'url_prefix':''}}
    application = Application()
    import uliweb.core.SimpleFrame as frame
    frame.application = application
    init_urls(frame.url_map, application.domains)

def init_urls(url_map, domains):
    for v in rules.merge_rules():
        appname, endpoint, url, kw = v
        static = kw.pop('static', None)
        if static:
            domain_name = 'static'
        else:
            domain_name = 'default'
        domain = domains.get(domain_name, {})
        url_prefix = domain.get('url_prefix', '')
        _url = url_prefix + url

        rules.add_rule(url_map, _url, endpoint, **kw)


def test_url_for_format():
    """
    >>> rules.clear_rules()
    >>> def view(name, value):pass
    >>> f = expose('/view/<name>/<int:value>')(view)
    >>> init_env()
    >>> from uliweb import url_for
    >>> url_for(view, name='abc', value='123')
    '/view/abc/123'
    >>> url_for(view, _format=True)
    '/view/{name}/{value}'
    """