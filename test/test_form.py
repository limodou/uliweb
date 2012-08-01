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
    ...     title = StringField(label='Title:', required=True, help_string='Title help string')
    ...     content = TextField(label='Content:')
    >>> f = F()
    >>> print f
    <form action="" class="form-horizontal" method="POST">
    <div class="control-group" id="div_field_title">
        <label class="control-label" for="field_title">Title::<span class="field_required">*</span>
    </label>
    <BLANKLINE>
        <div class="controls">
        <input class="field" id="field_title" name="title" placeholder="" type="text" value=""></input>
    <BLANKLINE>
        <p class="help help-block"><label class="description" for="field_title">Title help string</label>
    </p>
    <BLANKLINE>
    </div>
    <BLANKLINE>
    </div>
    <BLANKLINE>
    <div class="control-group" id="div_field_content">
        <label class="control-label" for="field_content">Content::</label>
    <BLANKLINE>
        <div class="controls">
        <textarea class="field" cols id="field_content" name="content" placeholder="" rows="10"></textarea>
    <BLANKLINE>
        <p class="help help-block"></p>
    <BLANKLINE>
    </div>
    <BLANKLINE>
    </div>
    <BLANKLINE>
    <div class="form-actions">
        <button class="btn btn-primary" name="submit" type="submit">Submit</button>
    <BLANKLINE>
    <BLANKLINE>
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
    <input class="field" id="field_title" name="title" placeholder="" type="text" value="limodou"></input>
    <BLANKLINE>
    >>> print F.title.html()
    <input class="field" id="field_title" name="title" placeholder="" type="text" value=""></input>
    <BLANKLINE>
    """

def test_IS_PAST_DATE():
    """
    >>> date = datetime.datetime(2011, 10, 12)
    >>> f = IS_PAST_DATE(date)
    >>> d = datetime.datetime(2011, 10, 12)
    >>> f(d)
    >>> f(datetime.datetime(2011, 10, 13))
    'The date can not be greater than 2011-10-12 00:00:00'
    >>> f(datetime.datetime(2011, 10, 11))
    """
    
def test_select():
    """
    >>> from uliweb.form.widgets import Select
    >>> a = unicode('男', 'utf8')
    >>> b = unicode('女', 'utf8')
    >>> s = Select([(a, a), (b, b)], value=a, multiple=True)
    >>> print s
    <select multiple size="10"><option selected value="男">男</option>
    <BLANKLINE>
    <option value="女">女</option>
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
    <BLANKLINE>
    <BLANKLINE>
    </div>
    <BLANKLINE>
    </form>
    <BLANKLINE>
    >>> form = TForm(form_class='well form-inline')
    >>> print form
    <form action="" class="form-horizontal" method="POST">
    <div class="form-actions">
        <button class="btn btn-primary" name="submit" type="submit">Submit</button>
    <BLANKLINE>
    <BLANKLINE>
    </div>
    <BLANKLINE>
    </form>
    <BLANKLINE>
    """
    
def test_string():
    """
    >>> a = StringField(name='title', label='Title', required=True, id='field_title')
    >>> print a.html('Test')
    <input class="field" id="field_title" name="title" placeholder="" type="text" value="Test"></input>
    <BLANKLINE>
    >>> print a.get_label()
    <label for="field_title">Title:<span class="field_required">*</span>
    </label>
    <BLANKLINE>
    >>> a.validate('')
    (False, gettext_lazy('This field is required.'))
    >>> a.validate('Hello')
    (True, 'Hello')
    >>> a.to_python('Hello')
    'Hello'
    >>> a = StringField(name='title', label='Title', required=True)
    >>> print a.html('')
    <input class="field" name="title" placeholder="" type="text" value=""></input>
    <BLANKLINE>
    >>> print a.get_label()
    <label>Title:<span class="field_required">*</span>
    </label>
    <BLANKLINE>
    >>> a.idtype = 'name'
    >>> print a.html('')
    <input class="field" id="field_title" name="title" placeholder="" type="text" value=""></input>
    <BLANKLINE>
    >>> print a.get_label()
    <label for="field_title">Title:<span class="field_required">*</span>
    </label>
    <BLANKLINE>
    >>> a = StringField(name='title', label='Title:', required=True, html_attrs={'class':'ffff'})
    >>> print a.html('')
    <input class="ffff field" name="title" placeholder="" type="text" value=""></input>
    <BLANKLINE>
    """

def test_unicode_field():
    """
    >>> a = UnicodeField(name='title', label='Title', required=True, id='field_title')
    >>> print a.html('Test')
    <input class="field" id="field_title" name="title" placeholder="" type="text" value="Test"></input>
    <BLANKLINE>
    >>> print a.get_label()
    <label for="field_title">Title:<span class="field_required">*</span>
    </label>
    <BLANKLINE>
    >>> a.validate('')
    (False, gettext_lazy('This field is required.'))
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
    <input class="field" id="field_password" name="password" placeholder="" type="password" value="Test"></input>
    <BLANKLINE>
    """

def test_hidden_field():
    """
    >>> a = HiddenField(name='id', id='field_id')
    >>> print a.html('Test')
    <input class="field" id="field_id" name="id" placeholder="" type="hidden" value="Test"></input>
    <BLANKLINE>
    """

def test_list_field():
    """
    >>> a = ListField(name='list', id='field_list')
    >>> print a.html(['a', 'b'])
    <input class="field" id="field_list" name="list" placeholder="" type="text" value="a b"></input>
    <BLANKLINE>
    >>> print a.validate('a b')
    (True, ['a', 'b'])
    >>> print a.validate('')
    (True, [])
    >>> a = ListField(name='list', id='field_list', delimeter=',')
    >>> print a.validate('a,b,c')
    (True, ['a', 'b', 'c'])
    >>> a = ListField(name='list', id='field_list', delimeter=',', datatype=int)
    >>> print a.validate('1,b,c')
    (False, "Can't convert '1,b,c' to ListField.")
    >>> print a.validate('1,2,3')
    (True, [1, 2, 3])
    """

def test_text_field():
    """
    >>> a = TextField(name='text', id='field_text')
    >>> print a.html('Test')
    <textarea class="field" cols id="field_text" name="text" placeholder="" rows="10">Test</textarea>
    <BLANKLINE>
    """

def test_textlines_field():
    """
    >>> a = TextLinesField(name='list', id='field_list')
    >>> print a.html(['a', 'b'])
    <textarea class="field" cols="40" id="field_list" name="list" placeholder="" rows="4">a
    b</textarea>
    <BLANKLINE>
    """

def test_bool_field():
    """
    >>> a = BooleanField(name='bool', id='field_bool')
    >>> print a.html('Test')
    <input checked class="checkbox" id="field_bool" name="bool" placeholder="" type="checkbox"></input>
    <BLANKLINE>
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
    <input class="field" id="field_int" name="int" placeholder="" type="text" value="Test"></input>
    <BLANKLINE>
    >>> print a.validate('')
    (True, 0)
    >>> print a.validate(None)
    (True, 0)
    >>> print a.validate('aaaa')
    (False, "Can't convert 'aaaa' to IntField.")
    >>> print a.validate('122')
    (True, 122)
    >>> a = BaseField(name='int', id='field_int', datatype=int)
    >>> print a.html('Test')
    <input class="field" id="field_int" name="int" placeholder="" type="text" value="Test"></input>
    <BLANKLINE>
    >>> print a.validate('122')
    (True, 122)
    """

def test_select_field():
    """
    >>> choices = [('a', 'AAA'), ('b', 'BBB')]
    >>> a = SelectField(name='select', id='field_select', default='a', choices=choices, validators=[IS_IN_SET(choices)])
    >>> print a.html('a')
    <select class="field" id="field_select" name="select" placeholder=""><option selected value="a">AAA</option>
    <BLANKLINE>
    <option value="b">BBB</option>
    </select>
    <BLANKLINE>
    >>> print a.validate('')
    (True, 'a')
    >>> print a.validate('aaaaaaa')
    (False, gettext_lazy('Select a valid choice. That choice is not one of the available choices.'))
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
    >>> a = RadioSelectField(name='select', id='field_select', default='a', choices=choices, validators=[IS_IN_SET(choices)])
    >>> print a.html('a')
    <label class="field" placeholder=""><input checked id="field_select" name="select" type="radio" value="a"></input>
    AAA</label>
    <label class="field" placeholder=""><input id="field_select" name="select" type="radio" value="b"></input>
    BBB</label>
    <BLANKLINE>
    >>> print a.validate('')
    (True, 'a')
    >>> print a.validate('aaaaaaa')
    (False, gettext_lazy('Select a valid choice. That choice is not one of the available choices.'))
    >>> print a.validate('b')
    (True, 'b')
    """

def test_file_field():
    """
    >>> a = FileField(name='file', id='field_file')
    >>> print a.html('a')
    <input class="field" id="field_file" name="file" placeholder="" type="file"></input>
    <BLANKLINE>
    """
    
def test_time_field():
    """
    >>> a = TimeField(name='time', id='field_time')
    >>> print a.html(datetime.time(14, 30, 59))
    <input class="field field_time" id="field_time" name="time" placeholder="" type="text" value="14:30:59"></input>
    <BLANKLINE>
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
    <input class="field field_date" id="field_date" name="date" placeholder="" type="text" value="2009-01-01"></input>
    <BLANKLINE>
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
    <input class="field field_datetime" id="field_datetime" name="datetime" placeholder="" type="text" value="2009-09-25 14:30:59"></input>
    <BLANKLINE>
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
    ...     title = StringField(lable='Title:')
    >>> form = F()
    >>> print form.form_begin
    <form action="" class="" method="POST">
    >>> class F(Form):
    ...     title = StringField(lable='Title:')
    ...     file = FileField()
    >>> form = F(action='post')
    >>> print form.form_begin
    <form action="post" class="" enctype="multipart/form-data" method="POST">
    >>> print form.form_end
    </form>
    """
    
#if __name__ == '__main__':
#    from uliweb.utils import date
#    
#    a = DateField(name='date', id='field_date')
#    print a.validate('2009/01/01')