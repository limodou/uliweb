#coding=utf-8
import os
import cgi
import datetime
import time
import copy
from validators import *
from uliweb.i18n import gettext_lazy as _
from uliweb.core.html import Buf, Tag, begin_tag, u_str
from widgets import *
from layout import *
from uliweb.utils.storage import Storage
from uliweb.utils import date
from uliweb.utils.common import request_url, safe_str, get_uuid

DEFAULT_FORM_CLASS = 'form'
REQUIRED_CAPTION = '*'
REQUIRED_CAPTION_AFTER = True
DEFAULT_ENCODING = 'utf-8'
DEFAULT_LABEL_DELIMETER = ':'

ERR_CONVERT = _("Can't convert %r to %s.")

class ReservedWordError(Exception):pass
class RuleNotFound(Exception):pass

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
        except KeyError as k:
            return None

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError as k:
            raise AttributeError(k)

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
        return self.get_label()

    def get_label(self, _class=None):

        if self.field.__class__ is BooleanField:
            delimeter = False
        else:
            delimeter = True
        return self.field.get_label(_class=_class, delimeter=delimeter)

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
    field_css_class = ''
    default_validators = []
    default_datatype = None
    creation_counter = 0
    type_name = 'str'

    def __init__(self, label='', default=None, required=False, validators=None,
        name='', html_attrs=None, help_string='', build=None, datatype=None,
        multiple=False, idtype=None, static=False, placeholder='',
        hidden=False, rules=None, **kwargs):
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
        self.hidden = hidden
        self.rules = rules or {}

        _cls = ''
        if '_class' in self.html_attrs:
            _cls = '_class'
        elif 'class' in self.html_attrs:
            _cls = 'class'
        if not _cls:
#            self.html_attrs['class'] = ' '.join([self.html_attrs.pop(_cls), self.field_css_class])
#        else:
            self.html_attrs['class'] = ' '.join([self.field_css_class])
        if placeholder:
            self.html_attrs['placeholder'] = placeholder
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

    def clone(self):
        b = object.__new__(self.__class__)
        b.__dict__ = copy.deepcopy(self.__dict__)
        return b

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
            return str('<span class="value">%s</span>' % safe_str(value))
        else:
            if self.hidden:
                build = Hidden
            else:
                build = self.build
            return str(build(name=self.name, value=value, id=self.id, **self.html_attrs))

    def get_label(self, delimeter=True, label=None, **kwargs):
        if label is None:
            if self.label is None:
                label = capitalize(self.name)
            else:
                label = self.label
        if not label:
            return ''
        if delimeter and DEFAULT_LABEL_DELIMETER:
            label += DEFAULT_LABEL_DELIMETER
        if self.required and not self.static:
            if REQUIRED_CAPTION_AFTER:
                label += str(Tag('span', REQUIRED_CAPTION, _class='field_required'))
            else:
                label = str(Tag('span', REQUIRED_CAPTION, _class='field_required')) + label
        return str(Tag('label', label, _for=self.id, newline=False, **kwargs))

    def get_help_string(self, **kwargs):
        if self.help_string:
#            return str(Tag('label', self.help_string, _for=self.id, **kwargs))
            return str(self.help_string)
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

    def validate(self, data, all_data=None):
        """
        if 'rule' in kwargs, then validate extra rules

        e.g.:
            rule= {'required':True, 'minlength':6}
        """

        all_data = all_data or {}

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

        msg = TEST_NOT_EMPTY()(v)
        if self.required:
            if msg:
                return False, msg
        else:
            if msg:
                return True, self.default

        try:
            if isinstance(data, list):
                v = []
                for i in data:
                    v.append(self.to_python(i))
                data = v
            else:
                data = self.to_python(data)
        except:
            return False, unicode(ERR_CONVERT) % (data, self.__class__.__name__)
        for v in self.get_validators():
            msg = v(data, all_data)
            if msg:
                return False, msg
        return True, data

    def get_validators(self):
        for v in self.default_validators + self.validators:
            yield v

    def __property_config__(self, form_class, field_name):
        self.form_class = form_class
        self.field_name = field_name
        if not self.name:
            self.name = field_name
        self.init_rules(self.rules)

    def init_rules(self, rules):
        #initial rules

        for k, v in rules.items():
            rule_message = ''
            x = k.split(':')
            if isinstance(v, (tuple, list)):
                rule_value = v[0]
                rule_message = v[1]
            else:
                rule_value = v
            if len(x) == 1:
                front = True
                end = True
                rule_name = k
            else:
                rule_name = x[0]
                if x[1] == 'front':
                    front = True
                    end = False
                else:
                    front = False
                    end = True
            if end:
                if rule_name == 'required':
                    self.required = True
                validator_cls = rules_mapping.get(rule_name)
                if validator_cls:
                    validator = validator_cls(rule_value, message=rule_message, field=self)
                    self.validators.append(validator)
                    if not rule_message:
                        rule_message = validator.get_message()
                else:
                    raise RuleNotFound('Rule is not found.')

            if front:
                r = self.form_class.front_rules['rules'].setdefault(self.name, {})
                r[rule_name] = rule_value
                if rule_message:
                    m = self.form_class.front_rules['messages'].setdefault(self.name, {})
                    m[rule_name] = rule_message


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
    default_datatype = str

    def __init__(self, label='', default='', required=False, validators=None, name='', html_attrs=None, help_string='', build=None, **kwargs):
        BaseField.__init__(self, label=label, default=default, required=required, validators=validators, name=name, html_attrs=html_attrs, help_string=help_string, build=build, **kwargs)

    def to_python(self, data):
        """
        Convert a data to python format.
        """
        if data is None:
            return ''
        if isinstance(data, unicode):
            data = data.encode(DEFAULT_ENCODING)
        else:
            data = str(data)
        return data

class UnicodeField(BaseField):
    type_name = 'unicode'

    def __init__(self, label='', default='', required=False, validators=None, name='', html_attrs=None, help_string='', build=None, **kwargs):
        BaseField.__init__(self, label=label, default=default, required=required, validators=validators, name=name, html_attrs=html_attrs, help_string=help_string, build=build, **kwargs)

    def to_python(self, data):
        """
        Convert a data to python format.
        """
        if data is None:
            return u''
        if isinstance(data, unicode):
            return data
        else:
            return unicode(data, DEFAULT_ENCODING)

class PasswordField(StringField):
    default_build = Password
    type_name = 'password'


class HiddenField(StringField):
    default_build = Hidden
    type_name = 'hidden'

class ListField(StringField):
    type_name = 'list'

    def __init__(self, label='', default=None, required=False, validators=None, name='', delimeter=', ', html_attrs=None, help_string='', build=None, datatype=None, **kwargs):
        BaseField.__init__(self, label=label, default=default, required=required, validators=validators, name=name, html_attrs=html_attrs, help_string=help_string, build=build, **kwargs)
        self.delimeter = delimeter
        self._default = default or []
        self.datatype = datatype

    def to_python(self, data):
        import re

        if issubclass(self.build, TextArea):
            result = [x for x in data.splitlines()]
        else:
            result = [x for x in re.split('[%s]+' % self.delimeter, data)]
        if self.datatype:
            if self.datatype is str:
                result = map(safe_str, result)
            else:
                result = map(self.datatype, result)
        return result

    def to_html(self, data):
        if issubclass(self.build, TextArea):
            return '\n'.join([u_str(x) for x in data])
        else:
            return self.delimeter.join([u_str(x) for x in data])

class TextField(StringField):
    default_build = TextArea
    type_name = 'text'

    def __init__(self, label='', default='', required=False, validators=None, name='', html_attrs=None, help_string='', build=None, rows=4, cols=None, convert_html=False, **kwargs):
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

    def to_python(self, data):
        """
        Convert a data to python format.
        """
        if data is None:
            return ''
        if isinstance(data, self.datatype):
            return data
        if self.datatype is unicode:
            return unicode(data, DEFAULT_ENCODING)
        else:
            return data.encode(DEFAULT_ENCODING)

class TextLinesField(TextField):
    type_name = 'lines'

    def __init__(self, label='', default=None, required=False, validators=None, name='', html_attrs=None, help_string='', build=None, datatype=str, rows=4, cols=None, **kwargs):
        TextField.__init__(self, label=label, default=default, required=required, validators=validators, name=name, html_attrs=html_attrs, help_string=help_string, build=build, rows=rows, cols=cols, **kwargs)
        self._default = default or []
        self.datatype = datatype

    def to_python(self, data):
        return [self.datatype(x) for x in data.splitlines()]

    def to_html(self, data):
        return '\n'.join([u_str(x) for x in data])

    def html(self, data='', py=True):
        if data is None:
            value = ''
        else:
            value = '\n'.join([u_str(x) for x in data])
        #add convert '&' to '&amp;' 2011-8-20 by limodou
        if self.convert_html:
            value = value.replace('&', '&amp;')
        return str(self.build(value, id='field_'+self.name, name=self.name, rows=self.rows, cols=self.cols, **self.html_attrs))

class BooleanField(BaseField):
    default_build = Checkbox
    field_css_class = 'checkbox'
    type_name = 'bool'

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

    def validate(self, data, all_data=None):
        '''
        None data means False, so BooleanField need to override validate()
        '''
        if data is None:
            return True, False
        else:
            return super(BooleanField, self).validate(data, all_data)

class IntField(BaseField):
    default_build = Number
    type_name = 'int'

    def __init__(self, label='', default=0, required=False, validators=None, name='', html_attrs=None, help_string='', build=None, **kwargs):
        BaseField.__init__(self, label=label, default=default, required=required, validators=validators, name=name, html_attrs=html_attrs, help_string=help_string, build=build, **kwargs)

    def to_python(self, data):
        return int(float(data))

    def to_html(self, data):
        if data is None:
            return ''
        return str(data)

class FloatField(BaseField):
    type_name = 'float'

    def __init__(self, label='', default=0.0, required=False, validators=None, name='', html_attrs=None, help_string='', build=None, **kwargs):
        BaseField.__init__(self, label=label, default=default, required=required, validators=validators, name=name, html_attrs=html_attrs, help_string=help_string, build=build, **kwargs)

    def to_python(self, data):
        return float(data)

    def to_html(self, data):
        if data is None:
            return ''
        return str(data)

class SelectField(BaseField):
    default_build = Select
    type_name = 'select'

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
    default_build = RadioSelect
    type_name = 'radios'

class CheckboxSelectField(SelectField):
    default_build = CheckboxSelect
    type_name = 'checkboxes'

    def __init__(self, label='', default=None, choices=None, required=False, validators=None, name='', html_attrs=None, help_string='', build=None, multiple=None, **kwargs):
        multiple = multiple if multiple is not None else True
        SelectField.__init__(self, label=label, default=default, choices=choices, required=required, validators=validators, name=name, html_attrs=html_attrs, help_string=help_string, build=build, multiple=multiple, **kwargs)

class FileField(BaseField):
    default_build = File
    type_name = 'file'

    def __init__(self, label='', upload_to=None, upload_to_sub=None, **kwargs):
        BaseField.__init__(self, label=label, **kwargs)
        self.upload_to = upload_to
        self.upload_to_sub = upload_to_sub

    def to_python(self, data):
        d = D({})
        d['filename'] = os.path.basename(data.filename)
        d['file'] = data.file
        data.file.seek(0, os.SEEK_END)
        d['size'] = data.file.tell()
        data.file.seek(0, os.SEEK_SET)
        return d

    def html(self, data, py=True):
#        if py:
#            value = self.to_html(data)
#        else:
#            value = data
        return str(self.build(name=self.name, id=self.id, **self.html_attrs))

class ImageField(FileField):
    type_name = 'image'

    def __init__(self, label='', default='', required=False, validators=None, name='', html_attrs=None, help_string='', build=None, size=None, **kwargs):
        FileField.__init__(self, label=label, default=default, required=required, validators=validators, name=name, html_attrs=html_attrs, help_string=help_string, build=build, **kwargs)
        self.size = size
        self.validators.append(TEST_IMAGE(next=TEST_IMAGE_SIZE(size)))

class _BaseDatetimeField(StringField):
    time_func = 'to_date'

    def __init__(self, label='', default=None, required=False, validators=None, name='', html_attrs=None, help_string='', build=None, format=None, **kwargs):
        BaseField.__init__(self, label=label, default=default, required=required, validators=validators, name=name, html_attrs=html_attrs, help_string=help_string, build=build, **kwargs)
        self.format = format

    def _get_default(self):
        if self._default == 'now':
            return getattr(date, self.time_func)(date.now())
        else:
            return self._default
    default = property(_get_default)

    def to_python(self, data):
        try:
            return getattr(date, self.time_func)(data, format=self.format)
        except ValueError:
            raise Exception, _("The date is not a valid date format.")

    def to_html(self, data):
        if data:
            return date.to_string(data, timezone=False)
        else:
            return ''

class DateField(_BaseDatetimeField):
    field_css_class = 'field_date'
    type_name = 'date'

class TimeField(_BaseDatetimeField):
    field_css_class = 'field_time'
    time_func = 'to_time'
    type_name = 'time'

class DateTimeField(_BaseDatetimeField):
    field_css_class = 'field_datetime'
    time_func = 'to_datetime'
    type_name = 'datetime'

class FormMetaclass(type):
    def __init__(cls, name, bases, dct):
        cls.fields = {}
        cls.fields_list = []
        cls.rules = dct.get('rules', {})

        for base in bases[:1]:
            if hasattr(base, 'fields'):
                for name, field in base.fields.iteritems():
                    new_field = field.clone()
                    cls.add_field(name, new_field)

        fields_list = [(k, v) for k, v in dct.items() if isinstance(v, BaseField)]
        fields_list.sort(lambda x, y: cmp(x[1].creation_counter, y[1].creation_counter))
        for (field_name, obj) in fields_list:
            cls.add_field(field_name, obj)


class FormBuild(object):
    def __str__(self):
        buf = []
        for x in ['pre_html', 'begin', 'body', 'buttons_line', 'end', 'post_html']:
            t = getattr(self, x)
            if t:
                buf.append(str(t))
        return '\n'.join(buf)

fields_mapping = {
    'str':StringField,
    'select':SelectField,
    'text':TextField,
    'unicode':UnicodeField,
    'lines':TextLinesField,
    'password':PasswordField,
    'hidden':HiddenField,
    'int':IntField,
    'list':ListField,
    'radios':RadioSelectField,
    'image':ImageField,
    'float':FloatField,
    'file':FileField,
    'bool':BooleanField,
    'checkboxes':CheckboxSelectField,
    'date':DateField,
    'time':TimeField,
    'datetime':DateTimeField,
}

rules_mapping = {
    'required':TEST_NOT_EMPTY,
    'email':TEST_EMAIL,
    'url':TEST_URL,
    'equalTo':TEST_EQUALTO,
    'in':TEST_IN,
    'image':TEST_IMAGE,
    'minlength':TEST_MINLENGTH,
    'maxlength':TEST_MAXLENGTH,
    'rangelength':TEST_RANGELENGTH,
    'min':TEST_MIN,
    'max':TEST_MAX,
    'range':TEST_RANGE,
    'date':TEST_DATE,
    'datetime':TEST_DATETIME,
    'time':TEST_TIME,
    'number':TEST_NUMBER,
    'digits':TEST_DIGITS,
}

class Form(object):

    __metaclass__ = FormMetaclass

    layout_class = BootstrapLayout
    layout = None
    layout_class_args = {}
    fieldset = False
    form_action = ''
    form_method = 'POST'
    form_buttons = None
    form_title = None
    form_class = None
    form_id = 'form_' + get_uuid()[:5]
    rules = {}
    front_rules = {'rules':{}, 'messages':{}}

    def __init__(self, action=None, method=None, buttons=None,
            validators=None, html_attrs=None, data=None, errors=None,
            idtype='name', title='', vars=None, layout=None,
            id=None, _class='', **kwargs):
        self.form_action = action or self.form_action or request_url()
        self.form_method = method or self.form_method
        self.form_title = title or self.form_title
        self.form_class = _class or self.form_class
        self.kwargs = kwargs
        buttons = buttons or self.form_buttons or [str(Button(value=_('Submit'), _class="btn btn-primary", name="submit", type="submit"))]
        if buttons:
            if isinstance(buttons, (tuple, list)):
                self._buttons = list(buttons)
            else:
                self._buttons = [buttons]
        self.validators = validators or []
        self.html_attrs = html_attrs or {}
        if '_class' in self.html_attrs:
            self.html_attrs['class'] = self.html_attrs.pop('_class')

        self.idtype = idtype
        self.layout = layout or self.layout
        self.vars = vars
        for name, obj in self.fields_list:
            obj.idtype = self.idtype

        if self.form_class:
            self.html_attrs['class'] = self.form_class# + ' ' + DEFAULT_FORM_CLASS

        if 'class' not in self.html_attrs:
            self.html_attrs['class'] = ''

        self.form_class = self.html_attrs.get('class')
        self.form_id = id or self.html_attrs.get('id') or self.form_id

        self.bind(data or {}, errors or {})
        self.__init_validators()
        self.ok = True

    @classmethod
    def add_field(cls, field_name, field, attribute=False):
        if isinstance(field, BaseField):
            check_reserved_word(field_name)
            cls.fields[field_name] = field
            rules = cls.rules.get(field_name)
            if rules:
                field.rules.update(rules)
            field.__property_config__(cls, field_name)
            if attribute:
                setattr(cls, field_name, field)
            cls.fields_list.append((field_name, field))

    def __init_validators(self):
        for k, obj in self.fields.items():
            func = getattr(self, 'validate_%s' % obj.field_name, None)
            if func and callable(func):
                obj.validators.insert(0, func)

        func = getattr(self, 'form_validate', None)
        if func and callable(func):
            self.validators.append(func)

    def validate(self, *data):
        old_data = self.data.copy()
        all_data = {}
        for k, v in self.fields.items():
            #skip static field
            if not v.static:
                v.parse_data(data, all_data)

        errors = D({})
        new_data = {}

        #gather all fields
        for field_name, field in self.fields.items():
            new_data[field_name] = field.get_data(all_data)

        #validate and gather the result
        # result = D({})
        result = D(new_data.copy())
        for field_name, field in self.fields.items():
            flag, value = field.validate(new_data[field_name], result)
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

        #the data of static field will be put into parsed data
        for k, v in self.fields.items():
            if v.static and k in old_data:
                self.data[k] = old_data[k]
        return self.ok

    def __str__(self):
        return self.html()

    def _repr_html_(self):
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
        return '</form>\n'

    def get_buttons(self):
        return self._buttons

    def bind(self, data=None, errors=None):
        if data is not None:
            self.data = data
        if errors is not None:
            self.errors = errors

    def html(self):
        cls = get_form_layout_class(self.layout_class)
        layout = cls(self, self.layout, **self.layout_class_args)
        pre_html = self.pre_html() if hasattr(self, 'pre_html') else ''
        body = layout.html()
        post_html = self.post_html() if hasattr(self, 'post_html') else ''
        return ''.join([str(x) for x in [pre_html,body,post_html]])

    @property
    def build(self):
        cls = get_form_layout_class(self.layout_class)
        layout = cls(self, self.layout, **self.layout_class_args)
        result = FormBuild()
        result.pre_html = self.pre_html() if hasattr(self, 'pre_html') else ''
        result.begin = layout.begin()
        result.body = layout.hiddens() + layout.body()
        result.buttons = layout.buttons()
        result.buttons_line = layout.buttons_line()
        result.end = layout.end()
        result.post_html = self.post_html() if hasattr(self, 'post_html') else ''
        return result


def get_field_cls(type, default=None):
    return fields_mapping.get(type, default or StringField)

def make_field(type, **kwargs):
    """
    According field information creating Field instance
    """
    cls = get_field_cls(type)
    return cls(**kwargs)

def make_form(fields=None, layout=None, layout_class=None, base_class=None,
              get_form_field=None, name=None, rules=None, **kwargs):
    """
    Make a from according dict data:

    {'fields':[
            {'name':'name', 'type':'str', 'label':'label,
                'rules':{
                        'required':
                        'email'
                        'required:back|front' #back means server side, front means front side
                    }
            ...},
            ...
        ],
    #layout_class should be defined in settings.ini, just like
    #[FORM_LAYOUT_CLASSES]
    #bs3 = '#{appname}.form_help.Bootstrap3Layout'
    #is also can be a Layout Class
    #default is BootstrapLayout
    'layout_class':'bs3',
    'layout':{
        'rows':[
            '-- legend title --',
            'field_name',
            ['group_fieldname', 'group_fieldname']
            {'name':'name', 'colspan':3}
        ],
    }
    'base_class':'form class if not existed, then use Form'
    }

    get_form_field is a callback function, used to defined customized field class
    if has name then it'll be cached
    """
    from uliweb.utils.sorteddict import SortedDict

    get_form_field = get_form_field or (lambda name, f:None)

    #make fields
    props = SortedDict({})
    for f in fields or []:
        if isinstance(f, BaseField):
            props[f.name] = get_form_field(f.name, f) or f
        else:
            props[f['name']] = get_form_field(f['name'], f) or make_field(**f)

    #set other props
    if layout:
        props['layout'] = layout
    if layout_class:
        props['layout_class'] = layout_class
    if rules:
        props['rules'] = rules
    layout_class_args = kwargs.pop('layout_class_args', None)
    if layout_class_args:
        props['layout_class_args'] = layout_class_args

    cls = type(name or 'MakeForm_', (base_class or Form,), props)
    return cls

def get_form(formcls):
    """
    get form class according form class path or form class object
    """
    from uliweb.utils.common import get_configrable_object

    return get_configrable_object(formcls, 'FORMS', Form)

def get_form_layout_class(form_layout_class):
    """
    Get form layout class according form_layout_class path or layout class object
    """
    from uliweb.utils.common import get_configrable_object

    return get_configrable_object(form_layout_class, 'FORM_LAYOUT_CLASSES', Layout)

