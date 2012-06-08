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
    
#if __name__ == '__main__':
#    class TForm(Form):
#        pass
#    
#    form = TForm(html_attrs={'_class':'well form-inline'})
#    print form
#
#    form = TForm(form_class='well form-inline')
#    print form
#    