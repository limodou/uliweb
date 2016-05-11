#coding=utf8
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
    ['abc', 'cde']
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
    >>> x.keys()
    ['set', '_', 'gettext_lazy', 'default']
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
    ... #coding=utf8
    ... [DEFAULT]
    ... a = u'''hello
    ... 中文
    ... '''
    ... \"\"\")
    >>> x = Ini()
    >>> x.read(buf)
    >>> print repr(x.DEFAULT.a)
    u'hello\\n\\u4e2d\\u6587\\n'
    """

def test_save():
    """
    >>> from uliweb.i18n import gettext_lazy as _, i18n_ini_convertor
    >>> from StringIO import StringIO
    >>> x = Ini(env={'_':_}, convertors=i18n_ini_convertor)
    >>> buf = StringIO(\"\"\"
    ... [default]
    ... option = _('English')
    ... str = 'str'
    ... str1 = "str"
    ... float = 1.2
    ... int = 1
    ... list = [1, 'str', 0.12]
    ... dict = {'a':'b', 1:2}
    ... s = u'English'
    ... [other]
    ... option = 'default'
    ... options1 = '{{option}} xxx'
    ... options2 = '{{default.int}}'
    ... options3 = option
    ... options4 = '-- {{default.option}} --'
    ... options5 = '-- {{default.s}} --'
    ... options6 = u'English {{default.s}} --'
    ... options7 = default.str + default.str1
    ... \"\"\")
    >>> x.read(buf)
    >>> print x
    #coding=UTF-8
    <BLANKLINE>
    [default]
    option = _('English')
    str = 'str'
    str1 = 'str'
    float = 1.2
    int = 1
    list = [1, 'str', 0.12]
    dict = {'a': 'b', 1: 2}
    s = u'English'
    [other]
    option = 'default'
    options1 = 'default xxx'
    options2 = '1'
    options3 = 'default'
    options4 = '-- English --'
    options5 = '-- English --'
    options6 = u'English English --'
    options7 = 'strstr'
    <BLANKLINE>
    """
    
def test_merge_data():
    """
    >>> from uliweb.utils.pyini import merge_data
    >>> a = [[1,2,3], [2,3,4], [4,5]]
    >>> b = [{'a':[1,2], 'b':{'a':[1,2]}}, {'a':[2,3], 'b':{'a':['b'], 'b':2}}]
    >>> c = [set([1,2,3]), set([2,4])]
    >>> print merge_data(a)
    [1, 2, 3, 4, 5]
    >>> print merge_data(b)
    {'a': [1, 2, 3], 'b': {'a': [1, 2, 'b'], 'b': 2}}
    >>> print merge_data(c)
    set([1, 2, 3, 4])
    >>> print merge_data([2])
    2
    """
    
def test_lazy():
    """
    >>> from uliweb.i18n import gettext_lazy as _, i18n_ini_convertor
    >>> from StringIO import StringIO
    >>> x = Ini(env={'_':_}, convertors=i18n_ini_convertor, lazy=True)
    >>> buf = StringIO(\"\"\"
    ... [default]
    ... option = _('English')
    ... str = 'str'
    ... str1 = "str"
    ... float = 1.2
    ... int = 1
    ... list = [1, 'str', 0.12]
    ... dict = {'a':'b', 1:2}
    ... s = u'English'
    ... [other]
    ... option = 'default'
    ... options1 = '{{option}} xxx'
    ... options2 = '{{default.int}}'
    ... options3 = option
    ... options4 = '-- {{default.option}} --'
    ... options5 = '-- {{default.s}} --'
    ... options6 = u'English {{default.s}} --'
    ... options7 = default.str + default.str1
    ... \"\"\")
    >>> x.read(buf)
    >>> x.freeze()
    >>> print x
    #coding=UTF-8
    <BLANKLINE>
    [default]
    option = _('English')
    str = 'str'
    str1 = 'str'
    float = 1.2
    int = 1
    list = [1, 'str', 0.12]
    dict = {'a': 'b', 1: 2}
    s = u'English'
    [other]
    option = 'default'
    options1 = 'default xxx'
    options2 = '1'
    options3 = 'default'
    options4 = '-- English --'
    options5 = '-- English --'
    options6 = u'English English --'
    options7 = 'strstr'
    <BLANKLINE>
    """

def test_multiple_read():
    """
    >>> from uliweb.i18n import gettext_lazy as _, i18n_ini_convertor
    >>> from StringIO import StringIO
    >>> x = Ini(env={'_':_}, convertors=i18n_ini_convertor, lazy=True)
    >>> buf = StringIO(\"\"\"
    ... [default]
    ... option = 'abc'
    ... [other]
    ... option = default.option
    ... option1 = '{{option}} xxx'
    ... option2 = '{{default.option}}'
    ... option3 = '{{other.option}}'
    ... \"\"\")
    >>> x.read(buf)
    >>> buf1 = StringIO(\"\"\"
    ... [default]
    ... option = 'hello'
    ... \"\"\")
    >>> x.read(buf1)
    >>> x.freeze()
    >>> print x
    #coding=UTF-8
    <BLANKLINE>
    [default]
    option = 'hello'
    [other]
    option = 'hello'
    option1 = 'hello xxx'
    option2 = 'hello'
    option3 = 'hello'
    <BLANKLINE>
    """

def test_chinese():
    """
    >>> from uliweb.i18n import gettext_lazy as _, i18n_ini_convertor
    >>> from StringIO import StringIO
    >>> x = Ini(env={'_':_}, convertors=i18n_ini_convertor)
    >>> buf = StringIO(\"\"\"#coding=utf-8
    ... [default]
    ... option = '中文'
    ... option1 = u'中文'
    ... option2 = _('中文')
    ... option3 = '{{option}}'
    ... [other]
    ... x = '中文 {{default.option}}'
    ... x1 = u'中文 {{default.option}}'
    ... x2 = u'xbd {{default.option}}'
    ... \"\"\")
    >>> x.read(buf)
    >>> print x
    #coding=utf-8
    [default]
    option = '\xe4\xb8\xad\xe6\x96\x87'
    option1 = u'\xe4\xb8\xad\xe6\x96\x87'
    option2 = _('\xe4\xb8\xad\xe6\x96\x87')
    option3 = '\xe4\xb8\xad\xe6\x96\x87'
    [other]
    x = '\xe4\xb8\xad\xe6\x96\x87 \xe4\xb8\xad\xe6\x96\x87'
    x1 = u'\xe4\xb8\xad\xe6\x96\x87 \xe4\xb8\xad\xe6\x96\x87'
    x2 = u'xbd \xe4\xb8\xad\xe6\x96\x87'
    <BLANKLINE>
    >>> print repr(x.other.x1)
    u'\u4e2d\u6587 \u4e2d\u6587'
    >>> x.keys()
    ['set', '_', 'gettext_lazy', 'default', 'other']
    """

def test_set():
    """
    >>> from StringIO import StringIO
    >>> x = Ini()
    >>> buf = StringIO(\"\"\"#coding=utf-8
    ... [default]
    ... set1 = {1,2,3}
    ... set2 = set([1,2,3])
    ... \"\"\")
    >>> x.read(buf)
    >>> print x
    #coding=utf-8
    [default]
    set1 = set([1, 2, 3])
    set2 = set([1, 2, 3])
    <BLANKLINE>
    >>> buf2 = StringIO(\"\"\"#coding=utf-8
    ... [default]
    ... set1 = {5,3}
    ... \"\"\")
    >>> x.read(buf2)
    >>> print x.default.set1
    set([1, 2, 3, 5])
    """

def test_triple_string():
    """
    >>> from StringIO import StringIO
    >>> buf = StringIO(\"\"\"
    ... #coding=utf8
    ... [DEFAULT]
    ... a = 'b'
    ... \"\"\")
    >>> x = Ini(raw=True)
    >>> x.set_filename('test.ini')
    >>> x.read(buf)
    >>> print x.DEFAULT
    <BLANKLINE>
    #coding=utf8
    test.ini                      :0003 [DEFAULT]
    test.ini                      :0004 a = 'b'
    <BLANKLINE>
    """

def test_var_in_section():
    """
    >>> from StringIO import StringIO
    >>> buf = StringIO(\"\"\"
    ... #coding=utf8
    ... [DEFAULT]
    ... MENUS2012 = [
    ...     ('about', _('关于大会'), '/2012/about'),
    ...     ('schedulebj', _('北京日程'), '/2012/schedulebj'),
    ...     ('schedulesh', _('上海日程'), '/2012/schedulesh'),
    ...     ('Hackathon', _('编程马拉松'), 'http://www.douban.com/event/17299206/'),
    ...     ('registration', _('报名'), '/2012/registration'),
    ...     ('volunteer', _('志愿'), '/2012/volunteer'),
    ...     ('sponsors', _('赞助'), '/2012/sponsors'),
    ...     ('Weibo', _('微博'), 'http://weibo.com/pyconcn'),
    ...     ('2011', _('2011'), '/2011'),
    ... ]
    ... a = [1,2,3]
    ... b <= MENUS2012
    ... \"\"\")
    >>> x = Ini()
    >>> x.set_filename('test.ini')
    >>> x.read(buf)
    >>> print x.DEFAULT.b[0][0]
    about
    """

def test_env_var_1():
    """
    >>> from uliweb.i18n import gettext_lazy as _, i18n_ini_convertor
    >>> from StringIO import StringIO
    >>> import os
    >>> os.environ['TEST'] = 'test'
    >>> os.environ['OK'] = '3'
    >>> x = Ini(lazy=True)
    >>> buf = StringIO(\"\"\"
    ... [default]
    ... a = '$TEST/ok'
    ... c = '${TEST}ok'
    ... b = $OK
    ... d = {'name_$TEST':'$OK'}
    ... \"\"\")
    >>> x = Ini()
    >>> x.set_filename('test.ini')
    >>> x.read(buf)
    >>> x.freeze()
    >>> print repr(x.default.a)
    'test/ok'
    >>> print repr(x.default.b)
    3
    >>> print repr(x.default.c)
    'testok'
    >>> print repr(x.default.d)
    {'name_test': '3'}
    >>> x = Ini()
    >>> buf = StringIO(\"\"\"
    ... [default]
    ... a = '$TEST/ok'
    ... c = '${TEST}ok'
    ... b = $OK
    ... \"\"\")
    >>> x = Ini()
    >>> x.set_filename('test.ini')
    >>> x.read(buf)
    >>> print repr(x.default.a)
    'test/ok'
    >>> print repr(x.default.b)
    3
    >>> print repr(x.default.c)
    'testok'
    """

def test_env_var_2():
    """
    >>> from uliweb.i18n import gettext_lazy as _, i18n_ini_convertor
    >>> from StringIO import StringIO
    >>> import os
    >>> os.environ['TEST'] = 'test'
    >>> os.environ['OK'] = '3'
    >>> x = Ini(lazy=True)
    >>> buf = StringIO(\"\"\"
    ... [default]
    ... a = '$TEST/ok'
    ... c = '${TEST}ok'
    ... \"\"\")
    >>> x = Ini(import_env=False)
    >>> x.set_filename('test.ini')
    >>> x.read(buf)
    >>> x.freeze()
    >>> print x
    #coding=UTF-8
    <BLANKLINE>
    [default]
    a = '$TEST/ok'
    c = '${TEST}ok'
    <BLANKLINE>
    """
    
def test_email():
    """
    >>> from uliweb.i18n import gettext_lazy as _, i18n_ini_convertor
    >>> from StringIO import StringIO
    >>> import os
    >>> os.environ['MAIL'] = 'test'
    >>> x = Ini(import_env=True, lazy=True)
    >>> buf = StringIO(\"\"\"
    ... [MAIL]
    ... host = '128.192.168.2'
    ... \"\"\")
    >>> x.set_filename('test.ini')
    >>> x.read(buf)
    >>> x.freeze()
    >>> print x
    #coding=UTF-8
    <BLANKLINE>
    [MAIL]
    host = '128.192.168.2'
    <BLANKLINE>
    """

def test_pre_var():
    """
    >>> from uliweb.i18n import gettext_lazy as _, i18n_ini_convertor
    >>> from StringIO import StringIO
    >>> import os
    >>> x = Ini(import_env=True, lazy=True, pre_variables={'appname':'test'})
    >>> buf = StringIO(\"\"\"
    ... [DEFAULT]
    ... model = '#{appname}.models.Model'
    ... \"\"\")
    >>> x.set_filename('test.ini')
    >>> x.read(buf)
    >>> x.freeze()
    >>> print x
    #coding=UTF-8
    <BLANKLINE>
    [DEFAULT]
    model = 'test.models.Model'
    <BLANKLINE>
    """

def test_dict_init():
    """
    >>> x = Ini({'default':{'abc':'name'}})
    >>> print x
    #coding=utf-8
    [default]
    abc = 'name'
    <BLANKLINE>

    """
