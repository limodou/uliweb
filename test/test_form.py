#coding=utf-8
# How to test it?
# easy_install nose
# cd test
# nosetests test_form.py --with-doctest
import time, sys
sys.path.insert(0, '../uliweb/lib')

from uliweb.form import *
from uliweb.utils.test import BlankRequest
import datetime

def test_1():
    """
    >>> class F(Form):
    ...     title = StringField(label='Title', required=True, help_string='Title help string')
    ...     content = TextField(label='Content')
    >>> f = F()
    >>> print f
    <form action="" class="form-horizontal" method="POST">
    <div class="control-group" id="div_field_title">
        <label class="control-label" for="field_title">Title:<span class="field_required">*</span></label>
        <div class="controls">
        <input class="" id="field_title" name="title" type="text" value=""></input>
        <p class="help help-block">Title help string</p>
    </div>
    <BLANKLINE>
    </div>
    <BLANKLINE>
    <div class="control-group" id="div_field_content">
        <label class="control-label" for="field_content">Content:</label>
        <div class="controls">
        <textarea class="" cols id="field_content" name="content" rows="4"></textarea>
        <p class="help help-block"></p>
    </div>
    <BLANKLINE>
    </div>
    <BLANKLINE>
    <BLANKLINE>
    <div class="form-actions">
        <button class="btn btn-primary" name="submit" type="submit">Submit</button>
    </div>
    <BLANKLINE>
    </form>
    <BLANKLINE>
    >>> req = BlankRequest('/test?title=&content=')
    >>> f.validate(req.GET)
    False
    >>> req = BlankRequest('/test?title=Hello&content=')
    >>> f.validate(req.GET)
    True
    >>> req = BlankRequest('/test?title=Hello&content=aaaa')
    >>> f.validate(req.GET)
    True
    >>> f.title.data
    'Hello'
    >>> f.title.data = 'limodou'
    >>> print f.title.html
    <input class="" id="field_title" name="title" type="text" value="limodou"></input>
    >>> print F.title.html()
    <input class="" id="field_title" name="title" type="text" value=""></input>
    """

def test_select():
    """
    >>> from uliweb.form.widgets import Select
    >>> a = unicode('男', 'utf8')
    >>> b = unicode('女', 'utf8')
    >>> s = Select([(a, a), (b, b)], value=a, multiple=True)
    >>> print s
    <select multiple size="10">
    <option selected value="\xe7\x94\xb7">\xe7\x94\xb7</option>
    <option value="\xe5\xa5\xb3">\xe5\xa5\xb3</option>
    </select>
    <BLANKLINE>
    """
    
def test_form_class():
    """
    >>> class TForm(Form):
    ...     pass
    >>> form = TForm(html_attrs={'_class':'well form-inline'})
    >>> print form
    <form action="" class="well form-inline" method="POST">
    <div class="form-actions">
        <button class="btn btn-primary" name="submit" type="submit">Submit</button>
    </div>
    <BLANKLINE>
    </form>
    <BLANKLINE>
    >>> form = TForm(form_class='well form-inline')
    >>> print form
    <form action="" class="form-horizontal" method="POST">
    <div class="form-actions">
        <button class="btn btn-primary" name="submit" type="submit">Submit</button>
    </div>
    <BLANKLINE>
    </form>
    <BLANKLINE>
    """
    
def test_string():
    """
    >>> a = StringField(name='title', label='Title', required=True, id='field_title')
    >>> print a.html('Test')
    <input class="" id="field_title" name="title" type="text" value="Test"></input>
    >>> print a.get_label()
    <label for="field_title">Title:<span class="field_required">*</span></label>
    >>> a.validate('')
    (False, u'This field is required.')
    >>> a.validate('Hello')
    (True, 'Hello')
    >>> a.to_python('Hello')
    'Hello'
    >>> a = StringField(name='title', label='Title', required=True)
    >>> print a.html('')
    <input class="" name="title" type="text" value=""></input>
    >>> print a.get_label()
    <label>Title:<span class="field_required">*</span></label>
    >>> a.idtype = 'name'
    >>> print a.html('')
    <input class="" id="field_title" name="title" type="text" value=""></input>
    >>> print a.get_label()
    <label for="field_title">Title:<span class="field_required">*</span></label>
    >>> a = StringField(name='title', label='Title:', required=True, html_attrs={'class':'ffff'})
    >>> print a.html('')
    <input class="ffff" name="title" type="text" value=""></input>
    """

def test_unicode_field():
    """
    >>> a = UnicodeField(name='title', label='Title', required=True, id='field_title')
    >>> print a.html('Test')
    <input class="" id="field_title" name="title" type="text" value="Test"></input>
    >>> print a.get_label()
    <label for="field_title">Title:<span class="field_required">*</span></label>
    >>> a.validate('')
    (False, u'This field is required.')
    >>> a.validate('Hello')
    (True, u'Hello')
    >>> a.to_python('Hello')
    u'Hello'
    >>> a.to_python('中国')
    u'\u4e2d\u56fd'
    """
    
def test_password_field():
    """
    >>> a = PasswordField(name='password', label='Password:', required=True, id='field_password')
    >>> print a.html('Test')
    <input class="" id="field_password" name="password" type="password" value="Test"></input>
    """

def test_hidden_field():
    """
    >>> a = HiddenField(name='id', id='field_id')
    >>> print a.html('Test')
    <input class="" id="field_id" name="id" type="hidden" value="Test"></input>
    """

def test_list_field():
    """
    >>> a = ListField(name='list', id='field_list')
    >>> print a.html(['a', 'b'])
    <input class="" id="field_list" name="list" type="text" value="a, b"></input>
    >>> print a.validate('a b')
    (True, ['a', 'b'])
    >>> print a.validate('')
    (True, [])
    >>> a = ListField(name='list', id='field_list', delimeter=',')
    >>> print a.validate('a,b,c')
    (True, ['a', 'b', 'c'])
    >>> a = ListField(name='list', id='field_list', delimeter=',', datatype=int)
    >>> print a.validate('1,b,c')
    (False, u"Can't convert '1,b,c' to ListField.")
    >>> print a.validate('1,2,3')
    (True, [1, 2, 3])
    """

def test_text_field():
    """
    >>> a = TextField(name='text', id='field_text')
    >>> print a.html('Test')
    <textarea class="" cols id="field_text" name="text" rows="4">Test</textarea>
    """

def test_textlines_field():
    """
    >>> a = TextLinesField(name='list', id='field_list')
    >>> print a.html(['a', 'b'])
    <textarea class="" cols id="field_list" name="list" rows="4">a
    b</textarea>
    """

def test_bool_field():
    """
    >>> a = BooleanField(name='bool', id='field_bool')
    >>> print a.html('Test')
    <input checked class="checkbox" id="field_bool" name="bool" type="checkbox"></input>
    >>> print a.validate('on')
    (True, True)
    >>> print a.validate('')
    (True, False)
    >>> print a.validate(None)
    (True, False)
    """
        
def test_int_field():
    """
    >>> a = IntField(name='int', id='field_int')
    >>> print a.html('Test')
    <input class="" id="field_int" name="int" type="number" value="Test"></input>
    >>> print a.validate('')
    (True, 0)
    >>> print a.validate(None)
    (True, 0)
    >>> print a.validate('aaaa')
    (False, u"Can't convert 'aaaa' to IntField.")
    >>> print a.validate('122')
    (True, 122)
    >>> a = BaseField(name='int', id='field_int', datatype=int)
    >>> print a.html('Test')
    <input class="" id="field_int" name="int" type="text" value="Test"></input>
    >>> print a.validate('122')
    (True, 122)
    """

def test_select_field():
    """
    >>> choices = [('a', 'AAA'), ('b', 'BBB')]
    >>> a = SelectField(name='select', id='field_select', default='a', choices=choices, validators=[TEST_IN(choices)])
    >>> print a.html('a')
    <select class="" id="field_select" name="select">
    <option selected value="a">AAA</option>
    <option value="b">BBB</option>
    </select>
    <BLANKLINE>
    >>> print a.validate('')
    (True, 'a')
    >>> print a.validate('aaaaaaa')
    (False, u'The value is not in choices.')
    >>> print a.validate('b')
    (True, 'b')
    >>> a = SelectField(name='select', id='field_select', choices=[(1, 'AAA'), (2, 'BBB')], datatype=int)
    >>> print a.validate('')
    (True, None)
    >>> print a.validate('2')
    (True, 2)
    """

def test_radioselect_field():
    """
    >>> choices = [('a', 'AAA'), ('b', 'BBB')]
    >>> a = RadioSelectField(name='select', id='field_select', default='a', choices=choices, validators=[TEST_IN(choices)])
    >>> print a.html('a')
    <label class=""><input checked id="field_select" name="select" type="radio" value="a"></input>AAA</label>
    <label class=""><input id="field_select" name="select" type="radio" value="b"></input>BBB</label>
    >>> print a.validate('')
    (True, 'a')
    >>> print a.validate('aaaaaaa')
    (False, u'The value is not in choices.')
    >>> print a.validate('b')
    (True, 'b')
    """

def test_file_field():
    """
    >>> a = FileField(name='file', id='field_file')
    >>> print a.html('a')
    <input class="" id="field_file" name="file" type="file"></input>
    """
    
def test_time_field():
    """
    >>> a = TimeField(name='time', id='field_time')
    >>> print a.html(datetime.time(14, 30, 59))
    <input class="field_time" id="field_time" name="time" type="text" value="14:30:59"></input>
    >>> print a.validate('14:30:59')
    (True, datetime.time(14, 30, 59))
    >>> print a.validate('14:30')
    (True, datetime.time(14, 30))
    >>> print a.validate('')
    (True, None)
    >>> a = TimeField(name='time', id='field_time', default='now')
    """
    
def test_date_field():
    """
    >>> a = DateField(name='date', id='field_date')
    >>> print a.html(datetime.date(2009, 1, 1))
    <input class="field_date" id="field_date" name="date" type="text" value="2009-01-01"></input>
    >>> print a.validate('2009-01-01')
    (True, datetime.date(2009, 1, 1))
    >>> print a.validate('2009/01/01')
    (True, datetime.date(2009, 1, 1))
    >>> a = DateField(name='date', id='field_date', default='now')
    """
    
def test_datetime_field():
    """
    >>> a = DateTimeField(name='datetime', id='field_datetime')
    >>> print a.html(datetime.datetime(2009, 9, 25, 14, 30, 59))
    <input class="field_datetime" id="field_datetime" name="datetime" type="text" value="2009-09-25 14:30:59"></input>
    >>> print a.validate('2009-09-25 14:30:59')
    (True, datetime.datetime(2009, 9, 25, 14, 30, 59))
    >>> print a.validate('2009-09-25 14:30')
    (True, datetime.datetime(2009, 9, 25, 14, 30))
    >>> print a.validate('')
    (True, None)
    """

def test_form():
    """
    >>> class F(Form):
    ...     title = StringField(label='Title:')
    >>> form = F()
    >>> print form.form_begin
    <form action="" class="" method="POST">
    >>> class F(Form):
    ...     title = StringField(label='Title:')
    ...     file = FileField()
    >>> form = F(action='post')
    >>> print form.form_begin
    <form action="post" class="" enctype="multipart/form-data" method="POST">
    >>> print form.form_end
    </form>
    <BLANKLINE>
    """
    
def test_build():
    """
    >>> class F(Form):
    ...     title = StringField(label='Title:')
    >>> form = F()
    >>> build = form.build
    >>> print build.pre_html
    <BLANKLINE>
    >>> print build.begin
    <form action="" class="form-horizontal" method="POST">
    >>> print build.body
    <div class="control-group" id="div_field_title">
        <label class="control-label" for="field_title">Title::</label>
        <div class="controls">
        <input class="" id="field_title" name="title" type="text" value=""></input>
        <p class="help help-block"></p>
    </div>
    <BLANKLINE>
    </div>
    <BLANKLINE>
    <BLANKLINE>
    """
    
def test_form_hidden_field():
    """
    >>> class F(Form):
    ...     layout_class = BootstrapTableLayout
    ...
    ...     title = StringField(label='Title', required=True, help_string='Title help string')
    ...     content = HiddenField(label='Content')
    >>> f = F()
    >>> print f
    <form action="" class="form-horizontal" method="POST">
    <input class="" id="field_content" name="content" type="hidden" value=""></input>
    <table class="table table-layout width100"><tbody>
    <tr>
        <td colspan="1" valign="top" width="100%">
            <div class="control-group" id="div_field_title">
                <label class="control-label" for="field_title">Title:<span class="field_required">*</span></label>
                <div class="controls">
        <input class="" id="field_title" name="title" type="text" value=""></input>
        <div class="help help-block">
    Title help string
    </div>
    <BLANKLINE>
    </div>
    <BLANKLINE>
            </div>
        </td>
    </tr>
    <BLANKLINE>
    <tr>
    </tr>
    <BLANKLINE>
    </tbody></table>
    <BLANKLINE>
    <div class="form-actions">
        <button class="btn btn-primary" name="submit" type="submit">Submit</button>
    </div>
    <BLANKLINE>
    </form>
    <BLANKLINE>
    """

def test_make_form():
    """
    >>> fields = [
    ...     {'name':'str', 'type':'str', 'label':'String'},
    ... ]
    >>> from uliweb.form.layout import BootstrapLayout
    >>> F = make_form(fields=fields, layout_class=BootstrapLayout)
    >>> print F()
    <form action="" class="form-horizontal" method="POST">
    <div class="control-group" id="div_field_str">
        <label class="control-label" for="field_str">String:</label>
        <div class="controls">
        <input class="" id="field_str" name="str" type="text" value=""></input>
        <p class="help help-block"></p>
    </div>
    <BLANKLINE>
    </div>
    <BLANKLINE>
    <BLANKLINE>
    <div class="form-actions">
        <button class="btn btn-primary" name="submit" type="submit">Submit</button>
    </div>
    <BLANKLINE>
    </form>
    <BLANKLINE>
    """

def test_make_form_field():
    """
    >>> fields = [
    ...     StringField('String', name='str'),
    ... ]
    >>> from uliweb.form.layout import BootstrapLayout
    >>> F = make_form(fields=fields, layout_class=BootstrapLayout)
    >>> print F()
    <form action="" class="form-horizontal" method="POST">
    <div class="control-group" id="div_field_str">
        <label class="control-label" for="field_str">String:</label>
        <div class="controls">
        <input class="" id="field_str" name="str" type="text" value=""></input>
        <p class="help help-block"></p>
    </div>
    <BLANKLINE>
    </div>
    <BLANKLINE>
    <BLANKLINE>
    <div class="form-actions">
        <button class="btn btn-primary" name="submit" type="submit">Submit</button>
    </div>
    <BLANKLINE>
    </form>
    <BLANKLINE>
    """

def test_make_form_hidden():
    """
    >>> fields = [
    ...     HiddenField('String', name='str'),
    ...     {'name':'str1', 'type':'str', 'label':'String1', 'hidden':True},
    ... ]
    >>> from uliweb.form.layout import BootstrapLayout
    >>> F = make_form(fields=fields, layout_class=BootstrapLayout)
    >>> print F()
    <form action="" class="form-horizontal" method="POST">
    <input class="" id="field_str" name="str" type="hidden" value=""></input><input class="" id="field_str1" name="str1" type="hidden" value=""></input>
    <div class="form-actions">
        <button class="btn btn-primary" name="submit" type="submit">Submit</button>
    </div>
    <BLANKLINE>
    </form>
    <BLANKLINE>
    """

def test_rules():
    """
    >>> fields = [
    ...     {'name':'str1', 'type':'str', 'label':'String1', 'hidden':True},
    ... ]
    >>> rules = {'str1':{'required':True}}
    >>> from uliweb.form.layout import BootstrapLayout
    >>> F = make_form(fields=fields, layout_class=BootstrapLayout, rules=rules)
    >>> f = F()
    >>> F.rules
    {'str1': {'required': True}}
    >>> data = {'str1':''}
    >>> f.validate(data)
    False
    >>> data = {'str1':'xxxx'}
    >>> f.validate(data)
    True
    """

def test_field_rules():
    """
    >>> fields = [
    ...     {'name':'str1', 'type':'str', 'label':'String1', 'hidden':True,
    ...             'rules':{'required:front':True, 'url':True}},
    ... ]
    >>> from uliweb.form.layout import BootstrapLayout
    >>> F = make_form(fields=fields, layout_class=BootstrapLayout)
    >>> f = F()
    >>> F.front_rules
    {'rules': {'str1': {'url': True, 'required': True}}, 'messages': {'str1': {'url': u'Please enter a valid URL.', 'required': u'This field is required.'}}}
    >>> data = {'str1':'xxxx'}
    >>> f.validate(data)
    False
    >>> data = {'str1':'http://abc.com'}
    >>> f.validate(data)
    True
    """

def test_rule_equalto():
    """
    >>> fields = [
    ...     {'name':'str1', 'type':'str', 'label':'String1', 'hidden':True,
    ...             'rules':{'equalTo':'str2'}},
    ...     {'name':'str2', 'type':'str', 'label':'String2'},
    ... ]
    >>> from uliweb.form.layout import BootstrapLayout
    >>> F = make_form(fields=fields, layout_class=BootstrapLayout)
    >>> f = F()
    >>> data = {'str1':'xxxx', 'str2':'yyyy'}
    >>> f.validate(data)
    False
    >>> data = {'str1':'xxxx', 'str2':'xxxx'}
    >>> f.validate(data)
    True
    """

def test_validators():
    """
    >>> v = TEST_EMAIL()
    >>> v.get_message()
    u'Please enter a valid email address.'
    >>> v.validate('abc')
    False
    >>> v.validate('abc@gmail.com')
    True
    >>> v = TEST_DATE()
    >>> v.validate('2012-12-12')
    True
    >>> v.validate('abc')
    False
    >>> v = TEST_MIN(3)
    >>> v.validate(2)
    False
    >>> v.validate(3)
    True
    >>> v.validate(4)
    True
    >>> v = TEST_MAX(3)
    >>> v.validate(2)
    True
    >>> v.validate(3)
    True
    >>> v.validate(4)
    False
    >>> v = TEST_RANGE((2,3))
    >>> v.validate(1)
    False
    >>> v.validate(2)
    True
    >>> v.validate(3)
    True
    >>> v.validate(4)
    False
    >>> v = TEST_MINLENGTH(3)
    >>> v.validate('aa')
    False
    >>> v.validate('aaa')
    True
    >>> v.validate('aaaa')
    True
    >>> v = TEST_MAXLENGTH(3)
    >>> v.validate('aa')
    True
    >>> v.validate('aaa')
    True
    >>> v.validate('aaaa')
    False
    >>> v = TEST_RANGELENGTH((2,3))
    >>> v.get_message()
    u'Please enter a value between 2 and 3 characters long.'
    >>> v.validate('a')
    False
    >>> v.validate('aa')
    True
    >>> v.validate('aaa')
    True
    >>> v.validate('aaaa')
    False
    >>> v = TEST_NUMBER()
    >>> v.validate('a')
    False
    >>> v.validate('1')
    True
    >>> v.validate('-1.1')
    True
    >>> v = TEST_DIGITS()
    >>> v.validate('a')
    False
    >>> v.validate('1')
    True
    >>> v.validate('-1.1')
    False
    """

if __name__ == '__main__':
    fields = [
        {'name':'str1', 'type':'str', 'label':'String1', 'hidden':True,
                'rules':{'equalTo':('str2', 'String2')}},
        {'name':'str2', 'type':'str', 'label':'String2'},
    ]
    from uliweb.form.layout import BootstrapLayout
    F = make_form(fields=fields, layout_class=BootstrapLayout)
    f = F()
    print F.fields_list
    data = {'str1':'xxxx', 'str2':'yyyy'}
    print f.validate(data)
    data = {'str1':'xxxx', 'str2':'xxxx'}
    print f.validate(data)
