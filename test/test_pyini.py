from uliweb.utils.pyini import *

def test_sorteddict():
    """
    >>> d = SortedDict()
    >>> d
    <SortedDict {}>
    >>> d.name = 'limodou'
    >>> d['class'] = 'py'
    >>> d
    <SortedDict {'class':'py', 'name':'limodou'}>
    >>> d.keys()
    ['name', 'class']
    >>> d.values()
    ['limodou', 'py']
    >>> d['class']
    'py'
    >>> d.name
    'limodou'
    >>> d.get('name', 'default')
    'limodou'
    >>> d.get('other', 'default')
    'default'
    >>> 'name' in d
    True
    >>> 'other' in d
    False
    >>> print d.other
    None
    >>> try:
    ...     d['other']
    ... except Exception, e:
    ...     print e
    'other'
    >>> del d['class']
    >>> del d['name']
    >>> d
    <SortedDict {}>
    >>> d['name'] = 'limodou'
    >>> d.pop('other', 'default')
    'default'
    >>> d.pop('name')
    'limodou'
    >>> d
    <SortedDict {}>
    >>> d.update({'class':'py', 'attribute':'border'})
    >>> d
    <SortedDict {'attribute':'border', 'class':'py'}>
    """
def test_section():
    """
    >>> s = Section('default', "#comment")
    >>> print s
    #comment
    [default]
    <BLANKLINE>
    >>> s.name = 'limodou'
    >>> s.add_comment('name', '#name')
    >>> s.add_comment(comments='#change')
    >>> print s
    #change
    [default]
    #name
    name = 'limodou'
    <BLANKLINE>
    >>> del s.name
    >>> print s
    #change
    [default]
    <BLANKLINE>
    """
    
def test_ini1():
    """
    >>> x = Ini()
    >>> s = x.add('default')
    >>> print x
    #coding=utf-8
    [default]
    <BLANKLINE>
    >>> s['abc'] = 'name'
    >>> print x
    #coding=utf-8
    [default]
    abc = 'name'
    <BLANKLINE>
    
    """
def test_ini2():
    """
    >>> x = Ini()
    >>> x['default'] = Section('default', "#comment")
    >>> x.default.name = 'limodou'
    >>> x.default['class'] = 'py'
    >>> x.default.list = ['abc']
    >>> print x
    #coding=utf-8
    #comment
    [default]
    name = 'limodou'
    class = 'py'
    list = ['abc']
    <BLANKLINE>
    >>> x.default.list = ['cde'] #for mutable object will merge the data, including dict type
    >>> print x.default.list
    ['cde', 'abc']
    >>> x.default.d = {'a':'a'}
    >>> x.default.d = {'b':'b'}
    >>> print x.default.d
    {'a': 'a', 'b': 'b'}
    """  

def test_gettext():
    """
    >>> from uliweb.i18n import gettext_lazy as _
    >>> x = Ini(env={'_':_})
    >>> x['default'] = Section('default')
    >>> x.default.option = _('Hello')
    >>> x
    <Ini {'default':<Section {'option':gettext_lazy('Hello')}>}>
    """
    
def test_replace():
    """
    >>> x = Ini()
    >>> x['default'] = Section('default')
    >>> x.default.option = ['a']
    >>> x.default.option
    ['a']
    >>> x.default.option = ['b']
    >>> x.default.option
    ['a', 'b']
    >>> x.default.add('option', ['c'], replace=True)
    >>> x.default.option
    ['c']
    >>> print x.default
    [default]
    option <= ['c']
    <BLANKLINE>
    
    """

def test_set_var():
    """
    >>> x = Ini()
    >>> x.set_var('default/key', 'name')
    True
    >>> print x
    #coding=utf-8
    [default]
    key = 'name'
    <BLANKLINE>
    >>> x.set_var('default/key/name', 'hello')
    True
    >>> print x
    #coding=utf-8
    [default]
    key = 'name'
    key/name = 'hello'
    <BLANKLINE>
    >>> x.get_var('default/key')
    'name'
    >>> x.get_var('default/no')
    >>> x.get_var('defaut/no', 'no')
    'no'
    >>> x.del_var('default/key')
    True
    >>> print x
    #coding=utf-8
    [default]
    key/name = 'hello'
    <BLANKLINE>
    >>> x.get_var('default/key/name')
    'hello'
    >>> x.get_var('default')
    <Section {'key/name':'hello'}>
    """

def test_update():
    """
    >>> x = Ini()
    >>> x.set_var('default/key', 'name')
    True
    >>> d = {'default/key':'limodou', 'default/b':123}
    >>> x.update(d)
    >>> print x
    #coding=utf-8
    [default]
    key = 'limodou'
    b = 123
    <BLANKLINE>
    
    """

def test_uni_print():
    """
    >>> a = ()
    >>> uni_prt(a, 'utf-8')
    '()'
    >>> a = (1,2)
    >>> uni_prt(a)
    '(1, 2)'
    """

def test_triple_string():
    """
    >>> from StringIO import StringIO
    >>> buf = StringIO(\"\"\"
    ... [DEFAULT]
    ... a = u'''hello
    ... uliweb
    ... '''
    ... \"\"\")
    >>> x = Ini()
    >>> x.read(buf)
    >>> print x.DEFAULT.a
    hello
    uliweb
    <BLANKLINE>
    """
