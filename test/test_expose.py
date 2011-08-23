from uliweb.core.rules import expose, clear_rules, merge_rules, set_app_rules
import uliweb.core.rules as rules

def test():
    """
    >>> @expose
    ... def index():pass
    >>> print merge_rules()
    [('__main__', '__main__.index', '/__main__/index', {})]
    >>> clear_rules()
    >>> ####################################################
    >>> @expose
    ... def index(id):pass
    >>> print merge_rules()
    [('__main__', '__main__.index', '/__main__/index/<id>', {})]
    >>> clear_rules()
    >>> ####################################################
    >>> @expose()
    ... def index():pass
    >>> print merge_rules()
    [('__main__', '__main__.index', '/__main__/index', {})]
    >>> clear_rules()
    >>> ####################################################
    >>> @expose()
    ... def index(id):pass
    >>> print merge_rules()
    [('__main__', '__main__.index', '/__main__/index/<id>', {})]
    >>> clear_rules()
    >>> ####################################################
    >>> @expose('/index')
    ... def index():pass
    >>> print merge_rules()
    [('__main__', '__main__.index', '/index', {})]
    >>> clear_rules()
    >>> ####################################################
    >>> @expose(static=True)
    ... def index():pass
    >>> print merge_rules()
    [('__main__', '__main__.index', '/__main__/index', {'static': True})]
    >>> clear_rules()
    >>> ####################################################
    >>> @expose('/index')
    ... def index(id):pass
    >>> print merge_rules()
    [('__main__', '__main__.index', '/index', {})]
    >>> clear_rules()
    >>> ####################################################
    >>> @expose
    ... class A:pass
    >>> print merge_rules()
    []
    >>> clear_rules()
    >>> ####################################################
    >>> @expose
    ... class A:
    ...     def index(self):pass
    >>> print merge_rules()
    [('__main__', '__main__.A.index', '/__main__/A/index', {})]
    >>> clear_rules()
    >>> ####################################################
    >>> @expose
    ... class A:
    ...     def index(self, id):pass
    >>> print merge_rules()
    [('__main__', '__main__.A.index', '/__main__/A/index/<id>', {})]
    >>> clear_rules()
    >>> ####################################################
    >>> @expose
    ... class A:
    ...     def index(self, id):pass
    ...     @classmethod
    ...     def p(cls, id):pass
    ...     @staticmethod
    ...     def x(id):pass
    >>> print merge_rules()
    [('__main__', '__main__.A.index', '/__main__/A/index/<id>', {}), ('__main__', '__main__.A.p', '/__main__/A/p/<id>', {}), ('__main__', '__main__.A.x', '/__main__/A/x/<id>', {})]
    >>> clear_rules()
    >>> ####################################################
    >>> @expose
    ... class A:
    ...     @expose('/index')
    ...     def index(self, id):pass
    >>> print merge_rules()
    [('__main__', '__main__.A.index', '/index', {})]
    >>> clear_rules()
    >>> ####################################################
    >>> @expose('/user')
    ... class A:
    ...     @expose('/index')
    ...     def index(self, id):pass
    ...     def hello(self):pass
    >>> print merge_rules()
    [('__main__', '__main__.A.index', '/index', {}), ('__main__', '__main__.A.hello', '/user/hello', {})]
    >>> clear_rules()
    >>> ####################################################
    >>> @expose('/user')
    ... class A(object):
    ...     @expose('/index')
    ...     def index(self, id):pass
    ...     def hello(self):pass
    >>> print merge_rules()
    [('__main__', '__main__.A.index', '/index', {}), ('__main__', '__main__.A.hello', '/user/hello', {})]
    >>> clear_rules()
    >>> ####################################################
    >>> app_rules = {'__main__':'/wiki'}
    >>> set_app_rules(app_rules)
    >>> @expose('/user')
    ... class A(object):
    ...     @expose('/index')
    ...     def index(self, id):pass
    ...     def hello(self):pass
    ...     @expose('inter')
    ...     def inter(self):pass
    >>> print merge_rules()
    [('__main__', '__main__.A.index', '/wiki/index', {}), ('__main__', '__main__.A.inter', '/wiki/user/inter', {}), ('__main__', '__main__.A.hello', '/wiki/user/hello', {})]
    >>> clear_rules()
    >>> rules.__app_rules__ = {}
    >>> ####################################################
    >>> @expose
    ... class A:
    ...     @expose('/index', name='index', static=True)
    ...     def index(self, id):pass
    >>> print merge_rules()
    [('__main__', '__main__.A.index', '/index', {'static': True})]
    >>> clear_rules()
    >>> ####################################################
    >>> set_app_rules({})
    >>> @expose
    ... class A:
    ...     @expose
    ...     def index(self, id):pass
    >>> print merge_rules()
    [('__main__', '__main__.A.index', '/__main__/A/index/<id>', {})]
    >>> clear_rules()
    >>> ####################################################
    >>> set_app_rules({})
    >>> @expose
    ... class A:
    ...     @expose()
    ...     def index(self, id):pass
    >>> print merge_rules()
    [('__main__', '__main__.A.index', '/__main__/A/index/<id>', {})]
    >>> clear_rules()
    >>> ####################################################
    >>> @expose
    ... class A:
    ...     @expose(name='index', static=True)
    ...     def index(self, id):pass
    >>> print merge_rules()
    [('__main__', '__main__.A.index', '/__main__/A/index/<id>', {'static': True})]
    >>> clear_rules()
    >>> ####################################################
    >>> @expose('/')
    ... class A:
    ...     def index(self, id):pass
    >>> print merge_rules()
    [('__main__', '__main__.A.index', '/index/<id>', {})]
    >>> clear_rules()
    >>> ####################################################
    >>> def static():pass
    >>> n = expose('/static', static=True)(static)
    >>> print merge_rules()
    [('__main__', '__main__.static', '/static', {'static': True})]
    >>> clear_rules()
    >>> ####################################################
    >>> @expose
    ... class A:
    ...     @expose('/index', name='index', static=True)
    ...     def index(self, id):pass
    >>> print merge_rules()
    [('__main__', '__main__.A.index', '/index', {'static': True})]
    >>> print rules.__url_names__
    {'index': '__main__.A.index'}
    >>> clear_rules()
    >>> ####################################################
    >>> @expose('/')
    ... class A:
    ...     @expose('index/<id>')
    ...     def index(self, id):pass
    >>> print merge_rules()
    [('__main__', '__main__.A.index', '/index/<id>', {})]
    >>> clear_rules()
    >>> ####################################################
    >>> @expose
    ... class A:
    ...     @expose('index')
    ...     def index(self, id):pass
    >>> print merge_rules()
    [('__main__', '__main__.A.index', '/__main__/A/index', {})]
    >>> clear_rules()
    
    """
    
#if __name__ == '__main__':
#    @expose
#    class A(object):
#        @expose('index')
#        def index(self, id):pass
#        def hello(self):pass
#    print merge_rules()
