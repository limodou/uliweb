#coding=utf-8
import os
import cgi
import datetime
import time
from validators import *
from uliweb.i18n import gettext_lazy as _
from uliweb.core.html import Buf, Tag, begin_tag, u_str
from widgets import *
from layout import *

DEFAULT_FORM_CLASS = 'form'
REQUIRED_CAPTION = '*'
REQUIRED_CAPTION_AFTER = True
DEFAULT_ENCODING = 'utf-8'
DEFAULT_LABEL_DELIMETER = ':'

class ReservedWordError(Exception):pass

__id = 0

def capitalize(s):
    t = s.split('_')
    return ' '.join([x.capitalize() for x in t])

def get_id():
    global __id
    __id += 1
    return __id

class D(dict):
    def __getattr__(self, key): 
        try: 
            return self[key]
        except KeyError, k: 
            return None
        
    def __setattr__(self, key, value): 
        self[key] = value
        
    def __delattr__(self, key):
        try: 
            del self[key]
        except KeyError, k: 
            raise AttributeError, k

def check_reserved_word(f):
    if f in dir(Form):
        raise ReservedWordError(
            "Cannot define property using reserved word '%s'. " % f
            )

###############################################################
# Form Helper
###############################################################

class FieldProxy(object):
    def __init__(self, form, field):
        self.form = form
        self.field = field
        
    @property
    def label(self):
        if self.field.__class__ is BooleanField:
            delimeter = False
        else:
            delimeter = True
        return self.field.get_label(_class='field', delimeter=delimeter)
    
    @property
    def help_string(self):
        return self.field.get_help_string(_class='description')
    
    @property
    def error(self):
        return self.form.errors.get(self.field.field_name, '')
    
    @property
    def html(self):
#        default = self.field.to_html(self.field.default)
        default = self.field.default
        return self.field.html(self.form.data.get(self.field.field_name, default), self.form.ok)
    
    def __str__(self):
        return self.html
    
    def _get_data(self):
        return self.form.data.get(self.field.name, self.field.default)
    
    def _set_data(self, value):
        self.form.data[self.field.name] = value
        
    data = property(_get_data, _set_data)
    
class BaseField(object):
    default_build = Text
    field_css_class = 'field'
    default_validators = []
    default_datatype = None
    creation_counter = 0

    def __init__(self, label='', default=None, required=False, validators=None, 
        name='', html_attrs=None, help_string='', build=None, datatype=None, 
        multiple=False, idtype=None, static=False, **kwargs):
        self.label = label
        self._default = default
        self.validators = validators or []
        self.name = name
        self.required = required
        self.kwargs = kwargs
        self.html_attrs = html_attrs or {}
        self.datatype = datatype or self.default_datatype
        self.idtype = idtype
        self.static = static
        _cls = ''
        if '_class' in self.html_attrs:
            _cls = '_class'
        elif 'class' in self.html_attrs:
            _cls = 'class'
        if _cls:
            self.html_attrs['class'] = ' '.join([self.html_attrs[_cls], self.field_css_class])
        else:
            self.html_attrs['class'] = ' '.join([self.field_css_class])
        
        self.multiple = multiple
        self.build = build or self.default_build
        self.help_string = help_string
        BaseField.creation_counter += 1
        self.creation_counter = BaseField.creation_counter
        if 'id' in self.kwargs:
            self._id = self.kwargs.pop('id')
        else:
            self._id = None

    def _get_default(self):
        return self._default
    default = property(_get_default)
    
    def to_python(self, data):
        """
        Convert a data to python format. 
        """
        if data is None:
            return data
        if self.datatype:
            return self.datatype(data)
        else:
            return data

    def html(self, data='', py=True):
        """
        Convert data to html value format.
        """
        if py:
            value = self.to_html(data)
        else:
            value = data
        if self.static:
            return str('<span class="value">%s</span>' % value)
        else:
            return str(self.build(name=self.name, value=value, id=self.id, **self.html_attrs))

    def get_label(self, delimeter=True, **kwargs):
        if not self.label:
            label = capitalize(self.name)
        else:
            label = self.label
        if not label:
            return ''
        if delimeter and DEFAULT_LABEL_DELIMETER:
            label += DEFAULT_LABEL_DELIMETER
        if self.required:
            if REQUIRED_CAPTION_AFTER:
                label += str(Tag('span', REQUIRED_CAPTION, _class='field_required'))
            else:
                label = str(Tag('span', REQUIRED_CAPTION, _class='field_required')) + label
        return str(Tag('label', label, _for=self.id, **kwargs))
    
    def get_help_string(self, **kwargs):
        if self.help_string:
            return str(Tag('label', self.help_string, _for=self.id, **kwargs))
        else:
            return ''
    
    @property
    def id(self):
        if self._id:
            return self._id
        else:
            if self.idtype == 'name':
                id = 'field_' + self.name
            elif self.idtype:
                id = 'field_' + str(get_id())
            else:
                id = None
            return id
        
    def parse_data(self, request, all_data):
        if not isinstance(request, (tuple, list)):
            request = [request]
        for r in request:
            v = None
            if self.multiple:
                if hasattr(r, 'getlist'):
                    func = getattr(r, 'getlist')
                else:
                    func = getattr(r, 'getall')
                v = all_data[self.name] = func(self.name)
            else:
                v = all_data[self.name] = r.get(self.name, None)
            if v is not None:
                break

    def get_data(self, all_data):
        return all_data.get(self.name, None)

    def to_html(self, data):
        if data is None:
            return ''
        return u_str(data)

    def validate(self, data):
        if hasattr(data, 'stream'):
            data.file = data.stream
            
        if hasattr(data, 'file'):
            if data.file:
                v = data.filename
            else:
                raise Exception, 'Unsupport type %s' % type(data)
        else:
            v = data
#        if v is None:
        if not v:
            if not self.required:
                return True, self.default
#                if self.default is not None:
#                    return True, self.default
#                else:
#                    return True, data
            else:
                return False, _('This field is required.')
        try:
            if isinstance(data, list):
                v = []
                for i in data:
                    v.append(self.to_python(i))
                data = v
            else:
                data = self.to_python(data)
        except:
            return False, "Can't convert %r to %s." % (data, self.__class__.__name__)
        for v in self.default_validators + self.validators:
            msg = v(data)
            if msg:
                return False, msg
        return True, data
    
    def __property_config__(self, form_class, field_name):
        self.form_class = form_class
        self.field_name = field_name
        if not self.name:
            self.name = field_name
    
    def __get__(self, model_instance, model_class):
        if model_instance is None:
            return self
        else:
            return FieldProxy(model_instance, self)
    
    def __set__(self, model_instance, value):
        raise Exception('Virtual property is read-only')
        
#    def _attr_name(self):
#        return '_' + self.name + '_'
#    
class StringField(BaseField):
    """
    >>> a = StringField(name='title', label='Title:', required=True, id='field_title')
    >>> print a.html('Test')
    <input class="field" id="field_title" name="title" type="text" value="Test"></input>
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
    >>> a = StringField(name='title', label='Title:', required=True)
    >>> print a.html('')
    <input class="field" name="title" type="text" value=""></input>
    <BLANKLINE>
    >>> print a.get_label()
    <label>Title:<span class="field_required">*</span>
    </label>
    <BLANKLINE>
    >>> a.idtype = 'name'
    >>> print a.html('')
    <input class="field" id="field_title" name="title" type="text" value=""></input>
    <BLANKLINE>
    >>> print a.get_label()
    <label for="field_title">Title:<span class="field_required">*</span>
    </label>
    <BLANKLINE>
    >>> a = StringField(name='title', label='Title:', required=True, html_attrs={'class':'ffff'})
    >>> print a.html('')
    <input class="ffff field" name="title" type="text" value=""></input>
    <BLANKLINE>
    """
    default_datatype = str
    def __init__(self, label='', default='', required=False, validators=None, name='', html_attrs=None, help_string='', build=None, **kwargs):
        BaseField.__init__(self, label=label, default=default, required=required, validators=validators, name=name, html_attrs=html_attrs, help_string=help_string, build=build, **kwargs)

    def to_python(self, data):
        """
        Convert a data to python format. 
        """
        data = data.strip()
        if isinstance(data, unicode):
            data = data.encode(DEFAULT_ENCODING)
        else:
            data = str(data)
        return data
    
class UnicodeField(BaseField):
    """
    >>> a = UnicodeField(name='title', label='Title:', required=True, id='field_title')
    >>> print a.html('Test')
    <input class="field" id="field_title" name="title" type="text" value="Test"></input>
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
    def __init__(self, label='', default='', required=False, validators=None, name='', html_attrs=None, help_string='', build=None, encoding='utf-8', **kwargs):
        BaseField.__init__(self, label=label, default=default, required=required, validators=validators, name=name, html_attrs=html_attrs, help_string=help_string, build=build, **kwargs)
        self.encoding = encoding

    def to_python(self, data):
        """
        Convert a data to python format. 
        """
        if data is None:
            return data
        data = data.strip()
        if isinstance(data, unicode):
            return data
        else:
            return unicode(data, self.encoding)
  
class PasswordField(StringField):
    """
    >>> a = PasswordField(name='password', label='Password:', required=True, id='field_password')
    >>> print a.html('Test')
    <input class="field" id="field_password" name="password" type="password" value="Test"></input>
    <BLANKLINE>
    """
    default_build = Password

class HiddenField(StringField):
    """
    >>> a = HiddenField(name='id', id='field_id')
    >>> print a.html('Test')
    <input class="field" id="field_id" name="id" type="hidden" value="Test"></input>
    <BLANKLINE>
    """
    default_build = Hidden

class ListField(StringField):
    """
    >>> a = ListField(name='list', id='field_list')
    >>> print a.html(['a', 'b'])
    <input class="field" id="field_list" name="list" type="text" value="a b"></input>
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
    def __init__(self, label='', default=None, required=False, validators=None, name='', delimeter=' ', html_attrs=None, help_string='', build=None, datatype=str, **kwargs):
        BaseField.__init__(self, label=label, default=default, required=required, validators=validators, name=name, html_attrs=html_attrs, help_string=help_string, build=build, **kwargs)
        self.delimeter = delimeter
        self._default = default or []
        self.datatype = datatype

    def to_python(self, data):
        if issubclass(self.build, TextArea):
            return [self.datatype(x) for x in data.splitlines()]
        else:
            return [self.datatype(x) for x in data.split(self.delimeter)]

    def to_html(self, data):
        if issubclass(self.build, TextArea):
            return '\n'.join([u_str(x) for x in data])
        else:
            return self.delimeter.join([u_str(x) for x in data])

class TextField(StringField):
    """
    >>> a = TextField(name='text', id='field_text')
    >>> print a.html('Test')
    <textarea class="field" cols="75" id="field_text" name="text" rows="10">Test</textarea>
    <BLANKLINE>
    
    """
    default_build = TextArea

    def __init__(self, label='', default='', required=False, validators=None, name='', html_attrs=None, help_string='', build=None, rows=10, cols=None, convert_html=False, **kwargs):
        BaseField.__init__(self, label=label, default=default, required=required, validators=validators, name=name, html_attrs=html_attrs, help_string=help_string, build=build, **kwargs)
        self.rows = rows
        self.cols = cols
        self.convert_html = convert_html
    
    def html(self, data='', py=True):
#        if py:
#            value = self.to_html(data)
#        else:
        value = data
        #add convert '&' to '&amp;' 2011-8-20 by limodou
        if self.convert_html:
            value = value.replace('&', '&amp;')
        return str(self.build(value, id='field_'+self.name, name=self.name, rows=self.rows, cols=self.cols, **self.html_attrs))

class TextLinesField(TextField):
    """
    >>> a = TextLinesField(name='list', id='field_list')
    >>> print a.html(['a', 'b'])
    <textarea class="field" cols="40" id="field_list" name="list" rows="4">a
    b</textarea>
    <BLANKLINE>
    """
    def __init__(self, label='', default=None, required=False, validators=None, name='', html_attrs=None, help_string='', build=None, datatype=str, rows=4, cols=40, **kwargs):
        TextField.__init__(self, label=label, default=default, required=required, validators=validators, name=name, html_attrs=html_attrs, help_string=help_string, build=build, rows=rows, cols=cols, **kwargs)
        self._default = default or []
        self.datatype = datatype

    def to_python(self, data):
        return [self.datatype(x) for x in data.splitlines()]

    def to_html(self, data):
        if data is None:
            return ''
        return '\n'.join([u_str(x) for x in data])

class BooleanField(BaseField):
    """
    >>> a = BooleanField(name='bool', id='field_bool')
    >>> print a.html('Test')
    <input checked class="checkbox" id="field_bool" name="bool" type="checkbox"></input>
    <BLANKLINE>
    >>> print a.validate('on')
    (True, True)
    >>> print a.validate('')
    (True, False)
    >>> print a.validate(None)
    (True, False)
    
    """
    default_build = Checkbox
    field_css_class = 'checkbox'
    
    def __init__(self, label='', default=False, name='', html_attrs=None, help_string='', build=None, required=False, **kwargs):
        BaseField.__init__(self, label=label, default=default, required=False, validators=None, name=name, html_attrs=html_attrs, help_string=help_string, build=build, **kwargs)

    def to_python(self, data):
        if data.lower() in ('on', 'true', 'yes', 'ok'):
            return True
        else:
            return False

    def html(self, data, py=True):
        if data:
            return str(self.build(checked=None, id='field_'+self.name, name=self.name, **self.html_attrs))
        else:
            return str(self.build(id='field_'+self.name, name=self.name, **self.html_attrs))

    def to_html(self, data):
        if data is True:
            return 'on'
        else:
            return ''

class IntField(BaseField):
    """
    >>> a = IntField(name='int', id='field_int')
    >>> print a.html('Test')
    <input class="field" id="field_int" name="int" type="text" value="Test"></input>
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
    <input class="field" id="field_int" name="int" type="text" value="Test"></input>
    <BLANKLINE>
    >>> print a.validate('122')
    (True, 122)

    """
    def __init__(self, label='', default=0, required=False, validators=None, name='', html_attrs=None, help_string='', build=None, **kwargs):
        BaseField.__init__(self, label=label, default=default, required=required, validators=validators, name=name, html_attrs=html_attrs, help_string=help_string, build=build, **kwargs)

    def to_python(self, data):
        return int(data)

    def to_html(self, data):
        if data is None:
            return ''
        return str(data)

class FloatField(BaseField):
    def __init__(self, label='', default=0.0, required=False, validators=None, name='', html_attrs=None, help_string='', build=None, **kwargs):
        BaseField.__init__(self, label=label, default=default, required=required, validators=validators, name=name, html_attrs=html_attrs, help_string=help_string, build=build, **kwargs)

    def to_python(self, data):
        return float(data)

    def to_html(self, data):
        if data is None:
            return ''
        return str(data)

class SelectField(BaseField):
    """
    >>> choices = [('a', 'AAA'), ('b', 'BBB')]
    >>> a = SelectField(name='select', id='field_select', default='a', choices=choices, validators=[IS_IN_SET(choices)])
    >>> print a.html('a')
    <select class="field" id="field_select" name="select"><option selected value="a">AAA</option>
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
    default_build = Select

    def __init__(self, label='', default=None, choices=None, required=False, validators=None, name='', html_attrs=None, help_string='', build=None, empty='', size=10, **kwargs):
        BaseField.__init__(self, label=label, default=default, required=required, validators=validators, name=name, html_attrs=html_attrs, help_string=help_string, build=build, **kwargs)
        self.choices = choices or []
        self.empty = empty
        self.size = size
        if self.multiple:
            self._default = default or []
        else:
            self._default = default or None
            
#        if self.choices:
#            self._default = default or self.choices[0][0]
#        self.validators.append(IS_IN_SET(lambda :self.get_choices()))

    def get_choices(self):
        if callable(self.choices):
            return self.choices()
        else:
            return self.choices
        
    def html(self, data='', py=True):
#        if py:
#            value = self.to_html(data)
#        else:
#            value = data
        choices = self.get_choices()[:]
        if (self.empty is not None) and (not self.multiple):
            group = False
            if choices:
                if len(choices[0]) > 2:
                    group = True
                    c = [(x[1], x[2]) for x in choices]
                else:
                    c = choices
                if (not self.default in dict(c)):
                    if group:
                        choices.insert(0, (choices[0][0], '', self.empty))
                    else:
                        choices.insert(0, ('', self.empty))
        return str(self.build(choices, data, id=self.id, name=self.name, multiple=self.multiple, size=self.size, **self.html_attrs))

class RadioSelectField(SelectField):
    """
    >>> choices = [('a', 'AAA'), ('b', 'BBB')]
    >>> a = RadioSelectField(name='select', id='field_select', default='a', choices=choices, validators=[IS_IN_SET(choices)])
    >>> print a.html('a')
    <input checked id="radio_1" name="select" type="radio" value="a"></input>
    <label for="radio_1">AAA</label>
    <input id="radio_2" name="select" type="radio" value="b"></input>
    <label for="radio_2">BBB</label>
    <BLANKLINE>
    >>> print a.validate('')
    (True, 'a')
    >>> print a.validate('aaaaaaa')
    (False, gettext_lazy('Select a valid choice. That choice is not one of the available choices.'))
    >>> print a.validate('b')
    (True, 'b')
    
    """
    default_build = RadioSelect
    
class FileField(BaseField):
    """
    >>> a = FileField(name='file', id='field_file')
    >>> print a.html('a')
    <input class="field" id="field_file" name="file" type="file"></input>
    <BLANKLINE>
    """
    
    default_build = File
    
    def to_python(self, data):
        d = D({})
        d['filename'] = os.path.basename(data.filename)
        d['file'] = data.file
#        data.file.seek(0, os.SEEK_END)
#        d['length'] = data.file.tell()
#        data.file.seek(0, os.SEEK_SET)
        return d
    
    def html(self, data, py=True):
#        if py:
#            value = self.to_html(data)
#        else:
#            value = data
        return str(self.build(name=self.name, id=self.id, **self.html_attrs))
    
class ImageField(FileField):
    
    def __init__(self, label='', default=None, required=False, validators=None, name='', html_attrs=None, help_string='', build=None, size=None, **kwargs):
        BaseField.__init__(self, label=label, default=default, required=required, validators=validators, name=name, html_attrs=html_attrs, help_string=help_string, build=build, **kwargs)
        self.size = size
        self.validators.append(IS_IMAGE(self.size))
    
DEFAULT_DATE_INPUT_FORMATS = (
    '%Y-%m-%d', '%m/%d/%Y', '%m/%d/%y', '%Y/%m/%d',  # '2006-10-25', '10/25/2006', '10/25/06'
    '%b %d %Y', '%b %d, %Y',            # 'Oct 25 2006', 'Oct 25, 2006'
    '%d %b %Y', '%d %b, %Y',            # '25 Oct 2006', '25 Oct, 2006'
    '%B %d %Y', '%B %d, %Y',            # 'October 25 2006', 'October 25, 2006'
    '%d %B %Y', '%d %B, %Y',            # '25 October 2006', '25 October, 2006'
)
class DateField(StringField):
    """
    >>> a = DateField(name='date', id='field_date')
    >>> print a.html(datetime.date(2009, 1, 1))
    <input class="field field_date" id="field_date" name="date" type="text" value="2009-01-01"></input>
    <BLANKLINE>
    >>> print a.validate('2009-01-01')
    (True, datetime.date(2009, 1, 1))
    >>> print a.validate('2009/01/01')
    (True, datetime.date(2009, 1, 1))
    >>> a = DateField(name='date', id='field_date', default='now')
    """
    field_css_class = 'field field_date'

    def __init__(self, label='', default=None, required=False, validators=None, name='', html_attrs=None, help_string='', build=None, format=None, **kwargs):
        BaseField.__init__(self, label=label, default=default, required=required, validators=validators, name=name, html_attrs=html_attrs, help_string=help_string, build=build, **kwargs)
        if not format:
            self.formats = DEFAULT_DATE_INPUT_FORMATS
        else:
            self.formats = format
            if not isinstance(format, (list, tuple)):
                self.formats = [format]

    def _get_default(self):
        if self._default == 'now':
            return datetime.date(*datetime.datetime.now().timetuple()[:3])
        else:
            return self._default
    default = property(_get_default)

    def to_python(self, data):
        for format in self.formats:
            try:
                return datetime.date(*time.strptime(data, format)[:3])
            except ValueError:
                continue
        raise Exception, _("The date is not a valid date format.")
    
    def to_html(self, data):
        if data:
            return data.strftime(self.formats[0])
        else:
            return ''
    
DEFAULT_TIME_INPUT_FORMATS = (
    '%H:%M:%S',     # '14:30:59'
    '%H:%M',        # '14:30'
)
class TimeField(StringField):
    """
    >>> a = TimeField(name='time', id='field_time')
    >>> print a.html(datetime.time(14, 30, 59))
    <input class="field field_time" id="field_time" name="time" type="text" value="14:30:59"></input>
    <BLANKLINE>
    >>> print a.validate('14:30:59')
    (True, datetime.time(14, 30, 59))
    >>> print a.validate('14:30')
    (True, datetime.time(14, 30))
    >>> print a.validate('')
    (True, None)
    >>> a = TimeField(name='time', id='field_time', default='now')
    """
    field_css_class = 'field field_time'
    
    def __init__(self, label='', default=None, required=False, validators=None, name='', html_attrs=None, help_string='', build=None, format=None, **kwargs):
        BaseField.__init__(self, label=label, default=default, required=required, validators=validators, name=name, html_attrs=html_attrs, help_string=help_string, build=build, **kwargs)
        if not format:
            self.formats = DEFAULT_TIME_INPUT_FORMATS
        else:
            self.formats = format
            if not isinstance(format, (list, tuple)):
                self.formats = [format]
        self._default = default

    def _get_default(self):
        if self._default == 'now':
            return datetime.time(*datetime.datetime.now().timetuple()[3:6])
        else:
            return self._default
    default = property(_get_default)
    
    def to_python(self, data):
        for format in self.formats:
            try:
                return datetime.time(*time.strptime(data, format)[3:6])
            except ValueError:
                continue
        raise Exception, _("The time is not a valid time format.")
    
    def to_html(self, data):
        if data:
            return data.strftime(self.formats[0])
        else:
            return ''

DEFAULT_DATETIME_INPUT_FORMATS = ["%s %s" % (x, y)
    for x in DEFAULT_DATE_INPUT_FORMATS
        for y in DEFAULT_TIME_INPUT_FORMATS]
        
class DateTimeField(StringField):
    """
    >>> a = DateTimeField(name='datetime', id='field_datetime')
    >>> print a.html(datetime.datetime(2009, 9, 25, 14, 30, 59))
    <input class="field field_datetime" id="field_datetime" name="datetime" type="text" value="2009-09-25 14:30:59"></input>
    <BLANKLINE>
    >>> print a.validate('2009-09-25 14:30:59')
    (True, datetime.datetime(2009, 9, 25, 14, 30, 59))
    >>> print a.validate('2009-09-25 14:30')
    (True, datetime.datetime(2009, 9, 25, 14, 30))
    >>> print a.validate('')
    (True, None)
    """
    field_css_class = 'field field_datetime'
    
    def __init__(self, label='', default=None, required=False, validators=None, name='', html_attrs=None, help_string='', build=None, format=None, **kwargs):
        BaseField.__init__(self, label=label, default=default, required=required, validators=validators, name=name, html_attrs=html_attrs, help_string=help_string, build=build, **kwargs)
        if not format:
            self.formats = DEFAULT_DATETIME_INPUT_FORMATS
        else:
            self.formats = format
            if not isinstance(format, (list, tuple)):
                self.formats = [format]
        self._default = default

    def _get_default(self):
        if self._default == 'now':
            return datetime.datetime.now()
        else:
            return self._default
    default = property(_get_default)
    
    def to_python(self, data):
        for format in self.formats:
            try:
                return datetime.datetime(*time.strptime(data, format)[:6])
            except ValueError:
                continue
        raise Exception, _("The datetime is not a valid datetime format.")
    
    def to_html(self, data):
        if data:
            return data.strftime(self.formats[0])
        else:
            return ''

#Only support single root derive
class FormMetaclass(type):
    def __init__(cls, name, bases, dct):
        cls.fields = {}
        cls.fields_list = []
        
        for base in bases[:1]:
            if hasattr(base, 'fields'):
                for name, field in base.fields.iteritems():
                    cls.add_field(name, field)
        
        fields_list = [(k, v) for k, v in dct.items() if isinstance(v, BaseField)]
        fields_list, dct.items()
        fields_list.sort(lambda x, y: cmp(x[1].creation_counter, y[1].creation_counter))
        for (field_name, obj) in fields_list:
            cls.add_field(field_name, obj)

class Form(object):
    """
    >>> class F(Form):
    ...     title = StringField(lable='Title:')
    >>> form = F()
    >>> print form.form_begin
    <form class="form" action="" method="POST">
    >>> class F(Form):
    ...     title = StringField(lable='Title:')
    ...     file = FileField()
    >>> form = F(action='post')
    >>> print form.form_begin
    <form class="form" action="post" enctype="multipart/form-data" method="POST">
    >>> print form.form_end
    </form>
    """

    __metaclass__ = FormMetaclass

    layout_class = YamlLayout
    layout = None
    layout_class_args = {}
    fieldset = False
    form_action = ''
    form_method = 'POST'
    form_buttons = None
    form_title = None

    def __init__(self, action=None, method=None, buttons=None, 
            validators=None, html_attrs=None, data={}, errors={}, 
            idtype='name', title='', vars=None, layout=None, **kwargs):
        self.form_action = action or self.form_action
        self.form_method = method or self.form_method
        self.form_title = title or self.form_title
        self.kwargs = kwargs
        self._buttons = buttons or self.form_buttons
        self.validators = validators or []
        self.html_attrs = html_attrs or {}
        self.idtype = idtype
        self.layout = layout or self.layout
        self.vars = vars
        for name, obj in self.fields_list:
            obj.idtype = self.idtype
        if '_class' in self.html_attrs:
            self.html_attrs['_class'] = self.html_attrs['_class'] + ' ' + DEFAULT_FORM_CLASS
        else:
            self.html_attrs['_class'] = DEFAULT_FORM_CLASS
            
        self.bind(data, errors)
        self.__init_validators()
        self.ok = True
        
    @classmethod
    def add_field(cls, field_name, field, attribute=False):
        if isinstance(field, BaseField):
            check_reserved_word(field_name)
            cls.fields[field_name] = field
            field.__property_config__(cls, field_name)
            if attribute:
                setattr(cls, field_name, field)
            cls.fields_list.append((field_name, field))
        
    def __init_validators(self):
        for k, obj in self.fields.items():
            func = getattr(self, 'validate_%s' % obj.field_name, None)
            if func and callable(func):
                obj.validators.append(func)
                
        func = getattr(self, 'form_validate', None)
        if func and callable(func):
            self.validators.append(func)

    def validate(self, *data):
        old_data = self.data.copy()
        all_data = {}
        for k, v in self.fields.items():
            v.parse_data(data, all_data)

        errors = D({})
        new_data = {}

        #gather all fields
        for field_name, field in self.fields.items():
            new_data[field_name] = field.get_data(all_data)

        #validate and gather the result
        result = D({})
        for field_name, field in self.fields.items():
            flag, value = field.validate(new_data[field_name])
            if not flag:
                if isinstance(value, dict):
                    errors.update(value)
                else:
                    errors[field_name] = value
            else:
                result[field_name] = value

        if not errors and self.validators:
            #validate global
            for v in self.validators:
                r = v(result)
                if r:
                    errors.update(r)

        if errors:
            self.ok = False
            self.errors = errors
            self.data = new_data
        else:
            self.ok = True
            self.errors = {}
            self.data = result
            
        for k, v in self.fields.iteritems():
            if v.static and k in old_data:
                self.data[k] = old_data[k]
        return self.ok

    def __str__(self):
        return self.html()
    
    @property
    def form_begin(self):
        args = self.html_attrs.copy()
        args['action'] = self.form_action
        args['method'] = self.form_method
        for field_name, field in self.fields.items():
            if isinstance(field, FileField):
                args['enctype'] = "multipart/form-data"
                break
        return begin_tag('form', **args)
    
    @property
    def form_end(self):
        return '</form>'
    
    def get_buttons(self):
        b = Buf()
        if self._buttons is None:
            b << [Submit(value=_('Submit'), _class="button", name="submit")]
        else:
            b << self._buttons
        return str(b)
    
    def bind(self, data=None, errors=None):
        if data is not None:
            self.data = data
        if errors is not None:
            self.errors = errors
            
#        self.f = D({})
#        for name, obj in self.fields_list:
#            f = FieldProxy(self, obj)
#            setattr(self, name, f)
#            self.f[name] = f

#    def __template__(self, name):
#        result = []
#        if hasattr(self, 'pre_html'):
#            result.append(self.pre_html())
#        result.append('{{<< %s}}' % name)
#        if hasattr(self, 'post_html'):
#            result.append(self.post_html())
#        
#        return ''.join(result)
    
    def html(self):
        result = []
        if hasattr(self, 'pre_html'):
            result.append(self.pre_html())
        cls = self.layout_class
        layout = cls(self, self.layout, **self.layout_class_args)
        result.append(str(layout))
        if hasattr(self, 'post_html'):
            result.append(self.post_html())
        return ''.join(result)

def test():
    """
    >>> class F(Form):
    ...     title = StringField(label='Title:', required=True, help_string='Title help string')
    ...     content = TextField(label='Content:')
    ...     password = PasswordField(label='Password:')
    ...     age = IntField(label='Age:')
    ...     id = HiddenField()
    ...     tag = ListField(label='Tag:')
    ...     public = BooleanField(label='Public:')
    ...     format = SelectField(label='Format:', choices=[('rst', 'reStructureText'), ('text', 'Plain Text')], default='rst')
    ...     radio = RadioSelectField(label='Radio:', choices=[('rst', 'reStructureText'), ('text', 'Plain Text')], default='rst')
    ...     file = FileField(label='file')
    >>> f = F()
    >>> class F(Form):
    ...     title = StringField(label='Title:', required=True, help_string='Title help string')
    """

#if __name__ == '__main__':
#    import doctest
#    doctest.testmod()
