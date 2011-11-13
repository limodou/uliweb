#coding=utf-8
from __future__ import with_statement
from uliweb.i18n import gettext_lazy as _
from uliweb.form import SelectField, BaseField
import os, sys
import time
from uliweb.orm import get_model, Model, Result
import uliweb.orm as orm
from uliweb import redirect, json, functions
from uliweb.core.storage import Storage
from sqlalchemy.sql import Select
from uliweb.contrib.upload import FileServing, FilenameConverter

__default_fields_builds__ = {}
class __default_value__(object):pass

def get_fileds_builds(section='GENERIC_FIELDS_MAPPING'):
    if not __default_fields_builds__:
        from uliweb import settings
        from uliweb.utils.common import import_attr
        import uliweb.form as form
        
        if settings and section in settings:
            for k, v in settings[section].iteritems():
                if v.get('build', None):
                    v['build'] = import_attr(v['build'])
                __default_fields_builds__[getattr(form, k)] = v
    return __default_fields_builds__

def get_sort_field(model, sort_field='sort', order_name='asc'):
    from uliweb import request
    
    model = get_model(model)
    if request.values.getlist('sort'):
        sort_fields = request.values.getlist('sort')
        order_by = []
        orders = request.values.getlist('order')
        for i, f in enumerate(sort_fields):
            if orders[i] == 'asc':
                order_by.append(model.c[f])
            else:
                order_by.append(model.c[f].desc())
    else:
        order_by = None
        
    return order_by
    
class ReferenceSelectField(SelectField):
    def __init__(self, model, group_field=None, value_field='id', condition=None, query=None, label='', default=None, required=False, validators=None, name='', html_attrs=None, help_string='', build=None, empty='', **kwargs):
        super(ReferenceSelectField, self).__init__(label=label, default=default, choices=None, required=required, validators=validators, name=name, html_attrs=html_attrs, help_string=help_string, build=build, empty=empty, **kwargs)
        self.model = model
        self.group_field = group_field
        self.value_field = value_field
        self.condition = condition
        self.query = query
        
    def get_choices(self):
        if self.choices:
            if callable(self.choices):
                return self.choices()
            else:
                return self.choices
            
        model = get_model(self.model)
        if not self.group_field:
            if hasattr(model, 'Meta'):
                self.group_field = getattr(model.Meta, 'group_field', None)
            else:
                self.group_field = None
           
        if self.query:
            query = self.query
        else:
            query = model.all()
            if hasattr(model, 'Meta') and hasattr(model.Meta, 'order_by'):
                _order = model.Meta.order_by
                if not isinstance(_order, (list, tuple)):
                    _order = [model.Meta.order_by]
                for x in _order:
                    if x.startswith('-'):
                        f = model.c[x[1:]].desc()
                    else:
                        if x.startswith('+'):
                            x = x[1:]
                        f = model.c[x].asc()
                    query = query.order_by(f)
        if self.condition is not None:
            query = query.filter(self.condition)
        if self.group_field:
            query = query.order_by(model.c[self.group_field].asc())
        if self.group_field:
            r = [(x.get_display_value(self.group_field), getattr(x, self.value_field), unicode(x)) for x in query]
        else:
            r = [(getattr(x, self.value_field), unicode(x)) for x in query]
        return r
    
    def to_python(self, data):
        return int(data)

class ManyToManySelectField(ReferenceSelectField):
    def __init__(self, model, group_field=None, value_field='id', 
            condition=None, query=None, label='', default=[], 
            required=False, validators=None, name='', html_attrs=None, 
            help_string='', build=None, **kwargs):
        super(ManyToManySelectField, self).__init__(model=model, group_field=group_field, 
            value_field=value_field, condition=condition, query=query, label=label, 
            default=default, required=required, validators=validators, name=name, 
            html_attrs=html_attrs, help_string=help_string, build=build, 
            empty=None, multiple=True, **kwargs)
            
class RemoteField(BaseField):
    """
    Fetch remote data
    """
    def __init__(self, label='', default='', required=False, validators=None, name='', html_attrs=None, help_string='', build=None, alt='', url='', **kwargs):
        _attrs = {'url':url, 'alt':alt, '_class':'rselect'}
        _attrs.update(html_attrs or {})
        BaseField.__init__(self, label=label, default=default, required=required, validators=validators, name=name, html_attrs=_attrs, help_string=help_string, build=build, **kwargs)
            
def get_fields(model, fields, meta):
    if fields is not None:
        f = fields
    elif hasattr(model, meta):
        m = getattr(model, meta)
        if hasattr(m, 'fields'):
            f = m.fields
        else:
            f = model._fields_list
    else:
        f = model._fields_list
        
    fields_list = []
    for x in f:
        field = {}
        if isinstance(x, str):  #so x is field_name
            field['name'] = x
        elif isinstance(x, tuple):
            field['name'] = x[0]
            field['field'] = x[1]
        elif isinstance(x, dict):
            field = x.copy()
        else:
            raise Exception, 'Field definition is not right, it should be just like (field_name, form_field_obj)'
        
        if 'prop' not in field:
            if hasattr(model, field['name']):
                field['prop'] = getattr(model, field['name'])
            else:
                field['prop'] = None
        
        fields_list.append((field['name'], field))
    return fields_list

def get_layout(model, meta):
    f = None
    if hasattr(model, meta):
        m = getattr(model, meta)
        if hasattr(m, 'layout'):
            f = m.layout
    return f

def get_url(ok_url, *args, **kwargs):
    if callable(ok_url):
        return ok_url(*args, **kwargs)
    else:
        return ok_url.format(*args, **kwargs)

def to_json_result(success, msg='', d=None, **kwargs):
    t = {'success':success, 'message':str(msg), 'data':d}
    t.update(kwargs)
    return json(t)
    
def make_form_field(field, model, field_cls=None, builds_args_map=None):
    import uliweb.form as form
    
    field_type = None
    if 'field' in field and isinstance(field['field'], BaseField): #if the prop is already Form.BaseField, so just return it
        return field['field']
    
    prop = field['prop']
    label = field.get('verbose_name', None) or prop.verbose_name or prop.property_name
    hint = field.get('hint', '') or prop.hint
    kwargs = dict(label=label, name=prop.property_name, 
        required=prop.required, help_string=hint)
    
    v = prop.default_value()
#    if v is not None:
    kwargs['default'] = v
        
    if field['static']:
        field_type = form.StringField
        kwargs['required'] = False
        kwargs['static'] = True
        if prop.choices is not None:
            kwargs['choices'] = prop.get_choices()
        
    if field['hidden']:
        field_type = form.HiddenField
        
    if 'required' in field:
        kwargs['required'] = field['required']
        
    if field_cls:
        field_type = field_cls
    elif not field_type:
        cls = prop.__class__
        if cls is orm.BlobProperty:
            pass
        elif cls is orm.TextProperty:
            field_type = form.TextField
        elif cls is orm.CharProperty or cls is orm.StringProperty:
            if prop.choices is not None:
                field_type = form.SelectField
                kwargs['choices'] = prop.get_choices()
            else:
                field_type = form.UnicodeField
        elif cls is orm.BooleanProperty:
            field_type = form.BooleanField
        elif cls is orm.DateProperty:
#            if not prop.auto_now and not prop.auto_now_add:
            field_type = form.DateField
        elif cls is orm.TimeProperty:
#            if not prop.auto_now and not prop.auto_now_add:
            field_type = form.TimeField
        elif cls is orm.DateTimeProperty:
#            if not prop.auto_now and not prop.auto_now_add:
            field_type = form.DateTimeField
        elif cls is orm.DecimalProperty:
            field_type = form.StringField
            if prop.choices is not None:
                field_type = form.SelectField
                kwargs['choices'] = prop.get_choices()
        elif cls is orm.FloatProperty:
            field_type = form.FloatField
        elif cls is orm.IntegerProperty:
            if 'autoincrement' not in prop.kwargs:
                if prop.choices is not None:
                    field_type = form.SelectField
                    kwargs['choices'] = prop.get_choices()
                    kwargs['datetype'] = int
                else:
                    field_type = form.IntField
        elif cls is orm.ManyToMany:
            kwargs['model'] = prop.reference_class
            field_type = ManyToManySelectField
        elif cls is orm.ReferenceProperty or cls is orm.OneToOne:
            #field_type = form.IntField
            kwargs['model'] = prop.reference_class
            kwargs['value_field'] = prop.reference_fieldname
            field_type = ReferenceSelectField
        elif cls is orm.FileProperty:
            field_type = form.FileField
        else:
            raise Exception, "Can't support the Property [%s=%s]" % (field['name'], prop.__class__.__name__)
       
    if field_type:
        build_args = builds_args_map.get(field_type, {})
        #add settings.ini configure support
        #so you could add options in settings.ini like this
        #  [GENERIC_FIELDS_MAPPING]
        #  FormFieldClassName = {'build':'model.NewFormFieldTypeClassName', **other args}
        #  
        #  e.g.
        #  [GENERIC_FIELDS_MAPPING]
        #  DateField = {'build':'jquery.widgets.DatePicker'}
        if not build_args:
            build_args = get_fileds_builds().get(field_type, {})
        kwargs.update(build_args)
        f = field_type(**kwargs)
    
        return f

def make_view_field(field, obj=None, types_convert_map=None, fields_convert_map=None, value=__default_value__):
    from uliweb.utils.textconvert import text2html
    from uliweb.core.html import Tag
    from uliweb import settings
    
    old_value = value

    types_convert_map = types_convert_map or {}
    fields_convert_map = fields_convert_map or {}
    default_convert_map = {orm.TextProperty:lambda v,o:text2html(v)}
    
    if isinstance(field, dict) and 'prop' in field and field.get('prop'):
        prop = field['prop']
    else:
        prop = field
        
    #not real Property instance, then return itself, so if should return
    #just like {'label':xxx, 'value':xxx, 'display':xxx}
    if not isinstance(prop, orm.Property):  
        if old_value is __default_value__:
            value = prop.get('value', '')
        display = prop.get('display', '')
        label = prop.get('label', '') or prop.get('verbose_name', '')
        name = prop.get('name', '')
        convert = prop.get('convert', None)
    else:
        if old_value is __default_value__:
            if isinstance(obj, Model):
                value = prop.get_value_for_datastore(obj)
            else:
                value = obj[prop.property_name]
        display = prop.get_display_value(value)
        name = prop.property_name
        
        if isinstance(field, dict):
            initial = field.get('verbose_name', None)
        else:
            initial = ''
        label = initial or prop.verbose_name or prop.property_name
        
    if name in fields_convert_map:
        convert = fields_convert_map.get(name, None)
    else:
        if isinstance(prop, orm.Property):
            convert = types_convert_map.get(prop.__class__, None)
            if not convert:
                convert = default_convert_map.get(prop.__class__, None)
        
    if convert:
        display = convert(value, obj)
    else:
        if value is not None:
            if isinstance(prop, orm.ManyToMany):
                s = []
                #support value parameter, the old value is already stored in "old_value" variable
                if old_value is not __default_value__:
                    query = prop.reference_class.filter(prop.reference_class.c[prop.reversed_fieldname].in_(old_value))
                else:
                    query = getattr(obj, prop.property_name).all()
                for x in query:
                    if hasattr(x, 'get_url'):
                        s.append(x.get_url())
                    else:
                        url_prefix = settings.get_var('MODEL_URL/'+x.tablename)
                        if url_prefix:
                            if url_prefix.endswith('/'):
                                url_prefix = url_prefix[:-1]
                            s.append(str(Tag('a', unicode(x), href=url_prefix+'/'+str(x.id))))
                        else:
                            s.append(unicode(x))
                display = ' '.join(s)
            elif isinstance(prop, orm.ReferenceProperty) or isinstance(prop, orm.OneToOne):
                try:
                    if old_value is not __default_value__:
                        d = prop.reference_class.c[prop.reference_fieldname]
                        v = prop.reference_class.get(d==old_value)
                    if not isinstance(obj, Model):
                        d = prop.reference_class.c[prop.reference_fieldname]
                        v = prop.reference_class.get(d==value)
                    else:
                        v = getattr(obj, prop.property_name)
                except orm.Error:
                    display = obj.get_datastore_value(prop.property_name)
                    v = None
                if isinstance(v, Model):
                    if hasattr(v, 'get_url'):
                        display = v.get_url()
                    else:
                        url_prefix = settings.get_var('MODEL_URL/'+v.tablename)
                        if url_prefix:
                            if url_prefix.endswith('/'):
                                url_prefix = url_prefix[:-1]
                            display = str(Tag('a', unicode(v), href=url_prefix+'/'+str(v.id)))
                        else:
                            display = unicode(v)
                else:
                    display = str(v)
            elif isinstance(prop, orm.FileProperty):
                from uliweb.contrib.upload import get_url
                url = get_url(value)
                if url:
                    display = str(Tag('a', value, href=url))
                else:
                    display = ''
#            if isinstance(prop, orm.Property) and prop.choices is not None:
#                display = prop.get_display_value(value)
            if prop.__class__ is orm.TextProperty:
                display = text2html(value)
        
    if isinstance(display, unicode):
        display = display.encode('utf-8')
    if display is None:
        display = '&nbsp;'
        
    return Storage({'label':label, 'value':value, 'display':display, 'name':name})

class AddView(object):
    success_msg = _('The information has been saved successfully!')
    fail_msg = _('There are somethings wrong.')
    builds_args_map = {}
    
    def __init__(self, model, ok_url=None, ok_template=None, form=None, success_msg=None, fail_msg=None, 
        data=None, default_data=None, fields=None, form_cls=None, form_args=None,
        static_fields=None, hidden_fields=None, pre_save=None, post_save=None,
        post_created_form=None, layout=None, file_replace=True, template_data=None, 
        success_data=None, meta='AddForm', get_form_field=None, post_fail=None,
        types_convert_map=None, fields_convert_map=None):

        self.model = get_model(model)
        self.meta = meta
        self.ok_url = ok_url
        self.ok_template = ok_template
        if success_msg:
            self.success_msg = success_msg
        if fail_msg:
            self.fail_msg = fail_msg
        self.data = data or {}
        self.template_data = template_data or {}
        
        #default_data used for create object
        self.default_data = default_data or {}
        self.get_form_field = get_form_field
        self.layout = layout
        self.fields = fields
        self.form_cls = form_cls
        self.form_args = form_args or {}
        self.static_fields = static_fields or []
        self.hidden_fields = hidden_fields or []
        self.pre_save = pre_save
        self.post_save = post_save
        self.post_created_form = post_created_form
        self.post_fail = post_fail
        self.file_replace = file_replace
        self.success_data = success_data
        self.types_convert_map = types_convert_map
        self.fields_convert_map = fields_convert_map
        self.form = self.make_form(form)
        
    def get_fields(self):
        f = []
        for field_name, prop in get_fields(self.model, self.fields, self.meta):
            d = prop.copy()
            d['static'] = field_name in self.static_fields
            d['hidden'] = field_name in self.hidden_fields
            f.append(d)
            
        return f
    
    def get_layout(self):
        if self.layout:
            return self.layout
        if hasattr(self.model, self.meta):
            m = getattr(self.model, self.meta)
            if hasattr(m, 'layout'):
                return getattr(m, 'layout')
            
    def prepare_static_data(self, data):
        """
        If user defined static fields, then process them with visiable value
        """
        d = data.copy()
        for f in self.get_fields():
            if f['static'] and f['name'] in d:
                d[f['name']] = make_view_field(f, None, self.types_convert_map, self.fields_convert_map, d[f['name']])['display']
        return d
    
    def make_form(self, form):
        from uliweb.form import Form, Submit
        
        if form:
            return form
        
        if self.form_cls:
            class DummyForm(self.form_cls):pass
            if not hasattr(DummyForm, 'form_buttons'):
                DummyForm.form_buttons = Submit(value=_('Create'), _class=".submit")
           
        else:
            class DummyForm(Form):
                form_buttons = Submit(value=_('Create'), _class=".submit")
            
        #add layout support
        layout = self.get_layout()
        DummyForm.layout = layout
        
        for f in self.get_fields():
            flag = False
            if self.get_form_field:
                field = self.get_form_field(f['name'])
                if field:
                    flag = True
            if not flag:
                field = make_form_field(f, self.model, builds_args_map=self.builds_args_map)
            
            if field:
                DummyForm.add_field(f['name'], field, True)
        
        if self.post_created_form:
            self.post_created_form(DummyForm, self.model)
            
        return DummyForm(data=self.data, **self.form_args)
    
    def process_files(self, data):
        flag = False
    
        fields_list = self.get_fields()
        for f in fields_list:
            if isinstance(f['prop'], orm.FileProperty):
                if f['name'] in data and data[f['name']]:
                    fobj = data[f['name']]
                    data[f['name']] = functions.save_file(fobj['filename'], fobj['file'], replace=self.file_replace)
                    flag = True
                    
        return flag
    
    def on_success_data(self, obj):
        if self.success_data is True:
            return obj.to_dict()
        elif callable(self.success_data):
            return self.success_data(obj)
        else:
            return None
    
    def on_success(self, d, json_result=False):
        from uliweb import response

        if self.pre_save:
            self.pre_save(d)
            
        r = self.process_files(d)
        obj = self.save(d)
        
        if self.post_save:
            self.post_save(obj, d)
                
        if json_result:
            return to_json_result(True, self.success_msg, self.on_success_data(obj))
        else:
            flash = functions.flash
            flash(self.success_msg)
            if self.ok_url:
                return redirect(get_url(self.ok_url, id=obj.id))
            else:
                response.template = self.ok_template
                return d
        
    def on_fail(self, d, json_result=False):
        import logging
        
        log = logging.getLogger('uliweb.app')
        log.debug(self.form.errors)
        if json_result:
            return to_json_result(False, self.fail_msg, self.form.errors)
        else:
            flash = functions.flash
            flash(self.fail_msg, 'error')
            return d
    
    def init_form(self):
        if not self.form:
            self.form = self.make_form()
            
    def display(self, json_result=False):
        d = self.template_data.copy()
        d.update({'form':self.form})
        return d
    
    def execute(self, json_result=False):
        from uliweb import request
        
        flag = self.form.validate(request.values, request.files)
        if flag:
            d = self.default_data.copy()
            d.update(self.form.data)
            return self.on_success(d, json_result)
        else:
            d = self.template_data.copy()
            data = self.prepare_static_data(self.form.data)
            self.form.bind(data)
            d.update({'form':self.form})
            if self.post_fail:
                self.post_fail(d)
            return self.on_fail(d, json_result)
        
    def run(self, json_result=False):
        from uliweb import request
        
        if request.method == 'POST':
            return self.execute(json_result)
        else:
            data = self.prepare_static_data(self.form.data)
            self.form.bind(data)
            return self.display(json_result)
        
    def save(self, data):
        obj = self.model(**data)
        obj.save()
        
#        self.save_manytomany(obj, data)
        return obj
        
    def save_manytomany(self, obj, data):
        #process manytomany property
        for k, v in obj._manytomany.iteritems():
            if k in data:
                value = data[k]
                if value:
                    getattr(obj, k).add(*value)

class EditView(AddView):
    success_msg = _('The information has been saved successfully!')
    fail_msg = _('There are somethings wrong.')
    builds_args_map = {}
    
    def __init__(self, model, ok_url=None, condition=None, obj=None, meta='EditForm', **kwargs):
        self.model = get_model(model)
        self.condition = condition
        self.obj = obj or self.query()
        
        AddView.__init__(self, model, ok_url, meta=meta, **kwargs)
        
        #set obj to form.object
        self.form.object = self.obj
        
    def display(self, json_result=False):
        d = self.template_data.copy()
        d.update({'form':self.form, 'object':self.obj})
        return d
    
    def execute(self, json_result=False):
        from uliweb import request
        
        flag = self.form.validate(request.values, request.files)
        if flag:
            d = self.default_data.copy()
            d.update(self.form.data)
            return self.on_success(d, json_result)
        else:
            d = self.template_data.copy()
            
            new_d = self.prepare_static_data(self.form.data)
            self.form.bind(new_d)
            
            d.update({'form':self.form, 'object':self.obj})
            if self.post_fail:
                self.post_fail(d, self.obj)
            return self.on_fail(d, json_result)

    def on_success(self, d, json_result):
        from uliweb import response
        
        if self.pre_save:
            self.pre_save(self.obj, d)
        #process file field
        r = self.process_files(d)
        r = self.save(self.obj, d) or r
        if self.post_save:
            r = self.post_save(self.obj, d) or r
        
        if r:
            msg = self.success_msg
        else:
            msg = _("The object has not been changed.")
        
        if json_result:
            return to_json_result(True, msg, self.on_success_data(self.obj), modified=r)
        else:
            flash = functions.flash
            flash(msg)
            if self.ok_url:
                return redirect(get_url(self.ok_url, self.obj.id))
            else:
                response.template = self.ok_template
                return d
            
    def on_fail(self, d, json_result=False):
        import logging
        
        log = logging.getLogger('uliweb.app')
        log.debug(self.form.errors)
        if json_result:
            return to_json_result(False, self.fail_msg, self.form.errors)
        else:
            flash = functions.flash
            flash(self.fail_msg, 'error')
            return d

    def prepare_static_data(self, data):
        """
        If user defined static fields, then process them with visiable value
        """
        d = self.obj.to_dict()
        d.update(data.copy())
        for f in self.get_fields():
            if f['static'] and f['name'] in d:
                v = make_view_field(f, self.obj, self.types_convert_map, self.fields_convert_map, d[f['name']])
                d[f['name']] = v['display']
        return d

    def run(self, json_result=False):
        from uliweb import request
        
        if request.method == 'POST':
            return self.execute(json_result)
        else:
            d = self.prepare_static_data(self.form.data)
            self.form.bind(d)
            return self.display(json_result)
        
    def save(self, obj, data):
        obj.update(**data)
        r = obj.save()
#        r1 = self.save_manytomany(obj, data)
#        return r or r1
        return r
        
    def save_manytomany(self, obj, data):
        #process manytomany property
        r = False
        for k, v in obj._manytomany.iteritems():
            if k in data:
                field = getattr(obj, k)
                value = data[k]
                if value:
                    r = getattr(obj, k).update(*value) or r
                else:
                    getattr(obj, k).clear()
        return r
        
    def query(self):
        return self.model.get(self.condition)
    
    def make_form(self, form):
        from uliweb.form import Form, Submit
        
        if form:
            return form

        if self.form_cls:
            class DummyForm(self.form_cls):pass
            if not hasattr(DummyForm, 'form_buttons'):
                DummyForm.form_buttons = Submit(value=_('Save'), _class=".submit")
           
        else:
            class DummyForm(Form):
                form_buttons = Submit(value=_('Save'), _class=".submit")
            
        fields_list = self.get_fields()
        fields_name = [x['name'] for x in fields_list]
#        if 'id' not in fields_name:
#            d = {'name':'id', 'prop':self.model.id, 'static':False, 'hidden':False}
#            fields_list.insert(0, d)
#            fields_name.insert(0, 'id')
        
        data = self.obj.to_dict(fields_name, convert=False).copy()
        data.update(self.data)
        
        #add layout support
        layout = self.get_layout()
        DummyForm.layout = layout

        for f in fields_list:
            if f['name'] == 'id':
                f['hidden'] = True
            elif isinstance(f['prop'], orm.IntegerProperty) and 'autoincrement' in f['prop'].kwargs:
                f['hidden'] = True
                
            flag = False
            if self.get_form_field:
                field = self.get_form_field(f['name'], self.obj)
                if field:
                    flag = True
            if not flag:
                field = make_form_field(f, self.model, builds_args_map=self.builds_args_map)
            
            if field:
                DummyForm.add_field(f['name'], field, True)
                
                if isinstance(f['prop'], orm.ManyToMany):
                    value = getattr(self.obj, f['name']).ids()
                    data[f['name']] = value
        
        if self.post_created_form:
            self.post_created_form(DummyForm, self.model, self.obj)
        
        return DummyForm(data=data, **self.form_args)

from uliweb.core import uaml
from uliweb.core.html import begin_tag, end_tag, u_str

class DetailWriter(uaml.Writer):
    def __init__(self, get_field):
        self.get_field = get_field
        
    def do_static(self, indent, value, **kwargs):
        name = kwargs.get('name', None)
        if name:
            f = self.get_field(name)
            f['display'] = f['display'] or '&nbsp;'
            return indent * ' ' + '<div class="static"><label>%(label)s:</label><span class="value">%(display)s</span></div>' % f
        else:
            return ''
        
    def do_td_field(self, indent, value, **kwargs):
        name = kwargs.pop('name', None)
        if name:
            f = self.get_field(name)
            f['display'] = f['display'] or '&nbsp;'
            if 'width' not in kwargs:
                kwargs['width'] = 200
            td = begin_tag('td', **kwargs) + u_str(f['display']) + end_tag('td')
            return '<th align=right width=200>%(label)s</th>' % f + td
        else:
            return '<th>&nbsp;</th><td>&nbsp;</td>'
        
        
class DetailLayout(object):
    def __init__(self, layout_file, get_field, model=None, writer=None):
        self.layout_file = layout_file
        self.writer = writer or DetailWriter(get_field)
        self.model = model
        
    def get_text(self):
        from uliweb import application
        f = file(application.get_file(self.layout_file, dir='templates'), 'rb')
        text = f.read()
        f.close()
        return text
    
    def __str__(self):
        return str(uaml.Parser(self.get_text(), self.writer))

class DetailTableLayout(object):
    def __init__(self, layout, get_field, model=None):
        self.layout = layout
        self.get_field = get_field
        self.model = model
        
    def line(self, fields, n):
        from uliweb.core.html import Tag
        
        _x = 0
        for _f in fields:
            if isinstance(_f, (str, unicode)):
                _x += 1
            elif isinstance(_f, dict):
                _x += _f.get('colspan', 1)
            else:
                raise Exception, 'Colume definition is not right, only support string or dict'
        
        tr = Tag('tr')
        with tr:
            for x in fields:
                _span = n / _x
                if isinstance(x, (str, unicode)):
                    f = self.get_field(x)
                elif isinstance(x, dict):
                    f = self.get_field(x['name'])
                    _span = _span * x.get('colspan', 1)
                
                with tr.td(colspan=_span, width='%d%%' % (100*_span/n,)):
                    with tr.div:
                        with tr.span(_class='view-label'):
                            tr << '<b>' + f['label'] + ': </b>'
                        with tr.span(_class='view-content'):
                            tr << f['display']
                
        return tr
        
    def render(self):
        from uliweb.core.html import Buf
        from uliweb.form.layout import min_times

        m = []
        for line in self.layout:
            if isinstance(line, (tuple, list)):
                _x = 0
                for f in line:
                    if isinstance(f, (str, unicode)):
                        _x += 1
                    elif isinstance(f, dict):
                        _x += f.get('colspan', 1)
                    else:
                        raise Exception, 'Colume definition is not right, only support string or dict'
                m.append(_x)
            else:
                m.append(1)
        n = min_times(m)
        
        buf = Buf()
        table = None
        fieldset = None
        first = True
        for fields in self.layout:
            if not isinstance(fields, (tuple, list)):
                if fields.startswith('--') and fields.endswith('--'):
                    #THis is a group line
                    if table:
                        buf << '</tbody></table>'
                    if fieldset:
                        buf << '</fieldset>'
                    title = fields[2:-2].strip()
                    if title:
                        fieldset = True
                        buf << '<fieldset><legend>%s</legend>' % title
                    
                    buf << '<table class="table width100"><tbody>'
                    table = True
                    first = False
                    continue
                else:
                    fields = [fields]
            if first:
                first = False
                buf << '<table class="table width100"><tbody>'
                table = True
            buf << self.line(fields, n)
        #close the tags
        if table:
            buf << '</tbody></table>'
        if fieldset:
            buf << '</fieldset>'
            
        return buf
    
    def __str__(self):
        return str(self.render())
    
class DetailView(object):
    def __init__(self, model, condition=None, obj=None, fields=None, 
        types_convert_map=None, fields_convert_map=None, table_class_attr='table width100',
        layout_class=None, layout=None, template_data=None, meta='DetailView'):
        self.model = get_model(model)
        self.meta = meta
        self.condition = condition
        if not obj:
            self.obj = self.query()
        else:
            self.obj = obj
        
        self.fields = fields
        self.types_convert_map = types_convert_map or {}
        self.fields_convert_map = fields_convert_map or {}
        self.table_class_attr = table_class_attr
        self.layout = layout or get_layout(model, meta)
        self.layout_class = layout_class
        if isinstance(self.layout, (str, unicode)):
            self.layout_class = layout_class or DetailLayout
        elif isinstance(self.layout, (tuple, list)):
            self.layout_class = layout_class or DetailTableLayout
        self.template_data = template_data or {}
        self.result_fields = Storage({})
        self.r = self.result_fields
        
    def run(self):
        view_text = self.render(self.obj)
        result = self.template_data.copy()
        result.update({'object':self.obj, 'view':''.join(view_text), 'view_obj':self})
        return result
    
    def query(self):
        return self.model.get(self.condition)
    
    def render(self, obj):
        if self.layout:
            fields = dict(get_fields(self.model, self.fields, self.meta))
            def get_field(name):
                prop = fields[name]
                return make_view_field(prop, obj, self.types_convert_map, self.fields_convert_map)
            
            return str(self.layout_class(self.layout, get_field, self.model))
        else:
            return self._render(obj)
        
    def _render(self, obj):
        view_text = ['<table class="%s">' % self.table_class_attr]
        for field_name, prop in get_fields(self.model, self.fields, self.meta):
            field = make_view_field(prop, obj, self.types_convert_map, self.fields_convert_map)
            if field:
                view_text.append('<tr><th align="right" width=150>%s</th><td>%s</td></tr>' % (field["label"], field["display"]))
                self.result_fields[field_name] = field
                
        view_text.append('</table>')
        return view_text

class DeleteView(object):
    success_msg = _('The object has been deleted successfully!')

    def __init__(self, model, ok_url='', fail_url='', condition=None, obj=None, pre_delete=None, post_delete=None, validator=None):
        self.model = get_model(model)
        self.condition = condition
        self.obj = obj
        self.validator = validator
        if not obj:
            self.obj = self.model.get(self.condition)
        else:
            self.obj = obj
        
        self.ok_url = ok_url
        self.fail_url = fail_url
        self.pre_delete = pre_delete
        self.post_delete = post_delete
        
    def run(self, json_result=False):
        flash = functions.flash

        if self.validator:
            msg = self.validator(self.obj)
            if msg:
                if json_result:
                    return to_json_result(False, msg)
                else:
                    flash(msg, 'error')
                    return redirect(self.fail_url)
                
        if self.pre_delete:
            self.pre_delete(self.obj)
        self.delete(self.obj)
        if self.post_delete:
            self.post_delete()
        
        if json_result:
            return to_json_result(True, self.success_msg)
        else:
            flash(self.success_msg)
            return redirect(self.ok_url)
    
    def delete(self, obj):
        if obj:
            self.delete_manytomany(obj)
            obj.delete()
        
    def delete_manytomany(self, obj):
        for k, v in obj._manytomany.iteritems():
            getattr(obj, k).clear()
  
class GenericFileServing(FileServing):
    options = {
        'x_sendfile' : ('GENERIC/X_SENDFILE', None),
        'x_header_name': ('GENERIC/X_HEADER_NAME', None),
        'x_file_prefix': ('GENERIC/X_FILE_PREFIX', '/gdownload'),
        'to_path': ('GENERIC/TO_PATH', './files'),
        'buffer_size': ('GENERIC/BUFFER_SIZE', 4096),
        '_filename_converter': ('UPLOAD/FILENAME_CONVERTER',  FilenameConverter),
    }

class SimpleListView(object):
    def __init__(self, fields=None, query=None, cache_file=None, 
        pageno=0, rows_per_page=10, id='listview_table', fields_convert_map=None, 
        table_class_attr='table', table_width=False, pagination=True, total_fields=None, 
        template_data=None, default_column_width=100, total=None, manual=False):
        """
        Pass a data structure to fields just like:
            [
                {'name':'field_name', 'verbose_name':'Caption', 'width':100},
                ...
            ]
        
        total_fields definition:
            ['field1', 'field2']
            
            or 
            
            [{'name':'fields', 'cal':'sum' or 'avg', 'render':str function(value, total_sum)]
        """
        self.fields = fields
        self._query = query
        self.pageno = pageno
        self.rows_per_page = rows_per_page
        self.rows_num = 0
        self.id = id
        self.table_class_attr = table_class_attr
        self.fields_convert_map = fields_convert_map or {}
        self.cache_file = cache_file
        self.total = total or 0
        self.table_width = table_width
        self.pagination = pagination
        self.create_total_infos(total_fields)
        self.template_data = template_data or {}
        self.default_column_width = default_column_width
        self.manual = manual
        self.downloader = GenericFileServing()
        
    def create_total_infos(self, total_fields):
        if total_fields:
            self.total_fields = {}
            for x in total_fields['fields']:
                if isinstance(x, (str, unicode)):
                    self.total_fields[x] = {}
                elif isinstance(x, dict):
                    self.total_fields[x['name']] = x
                else:
                    raise Exception, "Can't support this type (%r) at define total_fields for field %s" % (type(x), x)
            total_fields['fields']
            self.total_field_name = total_fields.get('total_field_name', _('Total'))
        else:
            self.total_fields = {}
            self.total_field_name = None
        self.total_sums = {}
            
    def cal_total(self, table, record):
        if self.total_fields:
            for f in self.total_fields:
                if isinstance(record, (tuple, list)):
                    i = table['fields'].index(f)
                    v = record[i]
                elif isinstance(record, dict):
                    v = record.get(f)
                else:
                    v = getattr(record, f)
                self.total_sums[f] = self.total_sums.setdefault(f, 0) + v
                
    def get_total(self, table):
        s = []
        if self.total_fields:
            for i, f in enumerate(table['fields']):
                if i == 0:
                    v = self.total_field_name
                else:
                    if f in self.total_fields:
                        v = self.total_sums.get(f, 0)
                        #process cal and render
                        x = self.total_fields[f]
                        cal = x.get('cal', 'sum')
                        if cal == 'sum':
                            pass
                        elif cal == 'avg':
                            v = v * 1.0 / self.rows_num
                        else:
                            raise Exception, "Don't support this cal type [%s]" % cal
                        render = x.get('render', None)
                        if render:
                            v = render(v, self.total_sums)
                        else:
                            v = str(v)
                    else:
                        v = ''
                s.append(v)
        return s

    def render_total(self, table, json=False):
        s = []
        if self.total_fields:
            if json:
                for v in self.get_total(table):
                    v = str(v)
                    s.append(v)
            else:
                s.append('<tr class="sum">')
                for v in self.get_total(table):
                    v = str(v) or '&nbsp;'
                    s.append('<td>%s</td>' % v)
                s.append('</tr>')
        return s
    
    def query_all(self):
        return self.query_range(0, pagination=False)
    
    def query(self):
        return self.query_range(self.pageno, self.pagination)
    
    def query_range(self, pageno=0, pagination=True):
        if callable(self._query):
            query_result = self._query()
        else:
            query_result = self._query
            
        def repeat(data, begin, n):
            result = []
            no_data_flag = False
            i = 0
            while (begin > 0 and i < begin) or (begin == -1):
                try:
                    result.append(data.next())
                    i += 1
                    n += 1
                except StopIteration:
                    no_data_flag = True
                    break
            return no_data_flag, n, result
        
        if self.manual:
            if isinstance(query_result, (list, tuple)):
                if not self.total:
                    self.total = len(query_result)
                return query_result
            else:
                if not self.total:
                    flag, self.total, result = repeat(query_result, -1, self.total)
                else:
                    result = query_result
                return result
        else:
            self.total = 0
            if pagination:
                if isinstance(query_result, (list, tuple)):
                    self.total = len(query_result)
                    result = query_result[pageno*self.rows_per_page : (pageno+1)*self.rows_per_page]
                    return result
                else:
                    #first step, skip records before pageno*self.rows_per_page
                    flag, self.total, result = repeat(query_result, pageno*self.rows_per_page, self.total)
                    if flag:
                        return []
                    
                    #second step, get the records
                    flag, self.total, result = repeat(query_result, self.rows_per_page, self.total)
                    if flag:
                        return result
                    
                    #third step, skip the rest records, and get the really total
                    flag, self.total, r = repeat(query_result, -1, self.total)
                    return result
            else:
                if isinstance(query_result, (list, tuple)):
                    self.total = len(query_result)
                    return query_result
                else:
                    flag, self.total, result = repeat(query_result, -1, self.total)
                    return result
        
    def download(self, filename, timeout=3600, action=None, query=None, fields_convert_map=None, type=None, domain=None):
        """
        Default domain option is PARA/DOMAIN
        """
        from uliweb import settings
        
        if fields_convert_map is not None:
            fields_convert_map = fields_convert_map 
        else:
            fields_convert_map = self.fields_convert_map
        
        t_filename = self.get_real_file(filename)
        if os.path.exists(t_filename):
            if timeout and os.path.getmtime(t_filename) + timeout > time.time():
                return self.downloader.download(filename, action)
            
        table = self.table_info()
        if not query:
            query = self.query_all()
        if not type:
            type = os.path.splitext(filename)[1]
            if type:
                type = type[1:]
            else:
                type = 'csv'
        if type in ('xlt', 'xls'):
            if not domain:
                domain = settings.get_var('PARA/DOMAIN')
            return self.download_xlt(filename, query, table, action, fields_convert_map, domain, not_tempfile=bool(timeout))
        else:
            return self.download_csv(filename, query, table, action, fields_convert_map, not_tempfile=bool(timeout))
       
    def get_data(self, query, table, fields_convert_map, encoding='utf-8', plain=True):
        from uliweb.utils.common import safe_unicode

        fields_convert_map = fields_convert_map or {}
        d = self.fields_convert_map.copy() 
        d.update(fields_convert_map)
        
        def get_value(name, value, record):
            convert = d.get(name)
            if convert:
                value = convert(value, record)
            return safe_unicode(value, encoding)
        
        for record in query:
            self.cal_total(table, record)
            row = []
            if not isinstance(record, (orm.Model, dict)):
                if not isinstance(record, (tuple, list)):
                    record = list(record)
                record = dict(zip(table['fields'], record))
                
            for i, x in enumerate(table['fields_list']):
                name = x['name']
                if isinstance(record, dict):
                    value = get_value(name, record[name], record)
                elif isinstance(record, orm.Model):
                    if plain:
                        if hasattr(record, name):
                            value = safe_unicode(record.get_display_value(name), encoding)
                        else:
                            value = ''
                    else:
                        if hasattr(record.__class__, name):
                            field = getattr(record.__class__, name)
                        else:
                            field = x
                        v = make_view_field(field, record, fields_convert_map=d)
                        value = safe_unicode(v['display'], encoding)
                row.append(value)
                
            yield row
        total = self.get_total(table)
        if total:
            row = []
            for x in total:
                v = x
                if isinstance(x, str):
                    v = safe_unicode(x, encoding)
                row.append(v)
            yield row

    def get_real_file(self, filename):
        t_filename = self.downloader.get_filename(filename)
        return t_filename
    
    def get_download_file(self, filename, not_tempfile):
        import tempfile
        
        t_filename = self.get_real_file(filename)
        dirname = os.path.dirname(t_filename)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        #bfile is display filename
        bfile = os.path.basename(t_filename)
        #tfile is template filename and it's the real filename
        if not not_tempfile:
            tfile = tempfile.NamedTemporaryFile(suffix = ".tmp", prefix = bfile+'_', dir=dirname, delete = False)
        else:
            tfile = open(t_filename, 'wb')
        #ufile is internal url filename
        ufile = os.path.join(os.path.dirname(filename), os.path.basename(tfile.name))
        return tfile, bfile, ufile
    
    def download_xlt(self, filename, data, table, action, fields_convert_map=None, domain=None, not_tempfile=False):
        from uliweb.utils.xlt import ExcelWriter
        from uliweb import request, settings
        
        fields_convert_map = fields_convert_map or {}
        tfile, bfile, ufile = self.get_download_file(filename, not_tempfile)
        if not domain:
            domain = settings.get_var('GENERIC/DOWNLOAD_DOMAIN', request.host_url)
        default_encoding = settings.get_var('GLOBAL/DEFAULT_ENCODING', 'utf-8')
        w = ExcelWriter(header=table['fields_list'], data=self.get_data(data, 
            table, fields_convert_map, default_encoding, plain=False), 
            encoding=default_encoding, domain=domain)
        w.save(tfile.name)
        return self.downloader.download(bfile, action=action, x_filename=ufile, 
            real_filename=tfile.name)
        
    def download_csv(self, filename, data, table, action, fields_convert_map=None, not_tempfile=False):
        from uliweb import settings
        from uliweb.utils.common import simple_value, safe_unicode
        import csv
        
        fields_convert_map = fields_convert_map or {}
        tfile, bfile, ufile = self.get_download_file(filename, not_tempfile)

        encoding = settings.get_var('GENERIC/CSV_ENCODING', sys.getfilesystemencoding() or 'utf-8')
        default_encoding = settings.get_var('GLOBAL/DEFAULT_ENCODING', 'utf-8')
        with tfile as f:
            w = csv.writer(f)
            row = [safe_unicode(x, default_encoding) for x in table['fields_name']]
            w.writerow(simple_value(row, encoding))
            for row in self.get_data(data, table, fields_convert_map, default_encoding):
                w.writerow(simple_value(row, encoding))
        return self.downloader.download(bfile, action=action, x_filename=ufile, 
            real_filename=tfile.name)
        
    def json(self):
        return self.run(head=False, body=True, json_body=True)

    def run(self, head=True, body=True, json_body=False):
        #create table header
        table = self.table_info()
            
        query = self.query()
        result = self.template_data.copy()
        if head:
            result.update(self.render(table, head=head, body=body, query=query))
        else:
            result.update(self.render(table, head=head, body=body, query=query, json_body=json_body))
        return result

    def render(self, table, head=True, body=True, query=None, json_body=False):
        """
        table is a dict, just like
        table = {'fields_name':[fieldname,...],
            'fields_list':[{'name':fieldname,'width':100,'align':'left'},...],
            'total':10,
        """
        result = {}
        s = []
        if head:
            if self.table_width:
                width = ' width="%dpx"' % table['width']
            else:
                width = ''
                
            s = ['<table class="%s" id=%s%s>' % (self.table_class_attr, self.id, width)]
            s.append('<thead>')
            s.extend(self.create_table_head(table))
            s.append('</thead>')
            s.append('<tbody>')
            result = {'info':{'total':self.total, 'rows_per_page':self.rows_per_page, 'pageno':self.pageno, 'id':self.id}}
            
        if body:
            #create table body
            self.rows_num = 0
            for record in query:
                self.rows_num += 1
                
                r = []
                if not isinstance(record, dict):
                    record = dict(zip(table['fields'], record))
                r = []
                for i, x in enumerate(table['fields_list']):
                    v = self.make_view_field(x, record, self.fields_convert_map)
                    r.append((x['name'], v['display']))
                    
                if json_body:
                    _r = self.json_body_render(r)
                    if 'id' not in _r and hasattr(record, 'id'):
                        _r['id'] = getattr(record, 'id')
                    s.append(_r)
                else:
                    s.extend(self.default_body_render(r))
                self.cal_total(table, record)
            if json_body:
                total = self.render_total(table, json_body)
                if total:
                    s.append(dict(zip(table['fields'], total)))
                return {'total':self.total, 'rows':s}
            else:
                s.extend(self.render_total(table))
        
        if head:
            s.append('</tbody>')
            s.append('</table>')
        
        result['table'] = '\n'.join(s)
        return result
    
    def json_body_render(self, record):
        return dict(record)
        
    def default_body_render(self, record):
        from uliweb.core.html import Tag
        
        s = ['<tr>']
        for n, f in record:
            s.append(str(Tag('td', f)))
        s.append('</tr>')
        return s

    def make_view_field(self, field, record, fields_convert_map):
        fields_convert_map = fields_convert_map or {}
        convert = None
        name = field['name']
        label = field.get('verbose_name', None) or field['name']
        if name in fields_convert_map:
            convert = fields_convert_map.get(name, None)
        value = record[name]
            
        if convert:
            display = convert(value, record)
        else:
            display = value
            
        if isinstance(display, unicode):
            display = display.encode('utf-8')
        if display is None:
            display = '&nbsp;'
            
        return {'label':label, 'value':value, 'display':display}
        
    def create_table_head(self, table):
        from uliweb.core.html import Tag
        from uliweb.utils.common import simple_value

        s = []
        fields = []
        max_rowspan = 0
        for i, f in enumerate(table['fields_name']):
            _f = list(f.split('/'))
            max_rowspan = max(max_rowspan, len(_f))
            fields.append((_f, i))
        
        def get_field(fields, i, m_rowspan):
            f_list, col = fields[i]
            field = {'name':f_list[0], 'col':col, 'width':table['fields_list'][col].get('width', 0), 'colspan':1, 'rowspan':1, 'title':table['fields_list'][col].get('help_string', '')}
            if len(f_list) == 1:
                field['rowspan'] = m_rowspan
            return field
        
        def remove_field(fields, i):
            del fields[i][0][0]
        
        def clear_fields(fields):
            for i in range(len(fields)-1, -1, -1):
                if len(fields[i][0]) == 0:
                    del fields[i]
                    
        n = len(fields)
        y = 0
        while n>0:
            i = 0
            s.append('<tr>')
            while i<n:
                field = get_field(fields, i, max_rowspan-y)
                remove_field(fields, i)
                j = i + 1
                while j<n:
                    field_n = get_field(fields, j, max_rowspan-y)
                    if simple_value(field['name']) == simple_value(field_n['name']) and field['rowspan'] == field_n['rowspan']:
                        #combine
                        remove_field(fields, j)
                        field['colspan'] += 1
                        field['width'] += field_n['width']
                        j += 1
                    else:
                        break
                kwargs = {}
                kwargs['align'] = 'left'
                if field['colspan'] > 1:
                    kwargs['colspan'] = field['colspan']
                    kwargs['align'] = 'center'
                if field['rowspan'] > 1:
                    kwargs['rowspan'] = field['rowspan']
                kwargs['width'] = field['width']
                if not kwargs['width']:
                    kwargs['width'] = self.default_column_width
                _f = table['fields_list'][field['col']]
                kwargs['field'] = _f['name']
                if kwargs.get('rowspan', 1) + y != max_rowspan:
                    kwargs.pop('width', None)
                    kwargs.pop('field', None)
                
#                else:
#                    kwargs['width'] = '100'
#                if kwargs.get('rowspan', 1) + y == max_rowspan:
#                    kwargs['title'] = field['title']
                s.append(str(Tag('th', field['name'], **kwargs)))
                
                i = j
            clear_fields(fields)
            s.append('</tr>\n')
            n = len(fields)
            y += 1
            
        return s
        
    def get_columns(self):
        from uliweb.utils.common import simple_value
    
        table = self.table_info()
        
        columns = []
        fields = []
        max_rowspan = 0
        for i, f in enumerate(table['fields_name']):
            _f = list(f.split('/'))
            max_rowspan = max(max_rowspan, len(_f))
            fields.append((_f, i))
        
        def get_field(fields, i, m_rowspan):
            f_list, col = fields[i]
            field = {'name':f_list[0], 'col':col, 'width':table['fields_list'][col].get('width', 0), 'colspan':1, 'rowspan':1, 'title':table['fields_list'][col].get('help_string', '')}
            if len(f_list) == 1:
                field['rowspan'] = m_rowspan
            return field
        
        def remove_field(fields, i):
            del fields[i][0][0]
        
        def clear_fields(fields):
            for i in range(len(fields)-1, -1, -1):
                if len(fields[i][0]) == 0:
                    del fields[i]
                    
        n = len(fields)
        y = 0
        while n>0:
            s = []
            i = 0
            while i<n:
                field = get_field(fields, i, max_rowspan-y)
                remove_field(fields, i)
                j = i + 1
                while j<n:
                    field_n = get_field(fields, j, max_rowspan-y)
                    if simple_value(field['name']) == simple_value(field_n['name']) and field['rowspan'] == field_n['rowspan']:
                        #combine
                        remove_field(fields, j)
                        field['colspan'] += 1
                        field['width'] += field_n['width']
                        j += 1
                    else:
                        break
                _f = table['fields_list'][field['col']].copy()
                kwargs = {}
                kwargs['field'] = _f.pop('name')
                _f.pop('verbose_name', None)
                _f.pop('prop', None)
                kwargs['title'] = simple_value(field['name'])
                span = False
                if field['colspan'] > 1:
                    kwargs['colspan'] = field['colspan']
                    span = True
                if field['rowspan'] > 1:
                    kwargs['rowspan'] = field['rowspan']
                    span = True
                #find the bottom column
                if kwargs.get('rowspan', 1) + y != max_rowspan:
                    _f.pop('width', None)
                    kwargs.pop('field', None)
                    _f.pop('title', None)
                else:
                    kwargs['width'] = _f.pop('width', self.default_column_width)
                kwargs.update(_f)
                s.append(kwargs)
                
                i = j
            clear_fields(fields)
            n = len(fields)
            y += 1
            columns.append(s)
            
        return columns

    def table_info(self):
        t = {'fields_name':[], 'fields':[]}
        t['fields_list'] = self.fields
        
        w = 0
        for x in self.fields:
            t['fields_name'].append(x['verbose_name'])
            t['fields'].append(x['name'])
            w += x.get('width', 0)
            
        t['width'] = w
        return t
    
class ListView(SimpleListView):
    def __init__(self, model, condition=None, query=None, pageno=0, order_by=None, 
        fields=None, rows_per_page=10, types_convert_map=None, pagination=True,
        fields_convert_map=None, id='listview_table', table_class_attr='table', table_width=True,
        total_fields=None, template_data=None, default_column_width=100, 
        meta='Table'):
        """
        If pageno is None, then the ListView will not paginate 
        """
        self.model = get_model(model)
        self.meta = meta
        self.condition = condition
        self.pageno = pageno
        self.order_by = order_by
        self.fields = fields
        self.rows_per_page = rows_per_page
        self.types_convert_map = types_convert_map
        self.fields_convert_map = fields_convert_map
        self.id = id
        self.rows_num = 0
        self._query = query
        self.table_width = table_width
        self.table_class_attr = table_class_attr
        self.total = 0
        self.pagination = pagination
        self.create_total_infos(total_fields)
        self.template_data = template_data or {}
        self.default_column_width = default_column_width
        self.downloader = GenericFileServing()
        
        self.init()
        
    def init(self):
        if not self.id:
            self.id = self.model.tablename
        
        #create table header
        self.table = self.table_info()
        
    def run(self, head=True, body=True, json_body=False):
        query = self.query()
        result = self.template_data.copy()
        if head:
            result.update(self.render(self.table, query, head=head, body=body))
        else:
            result.update(self.render(self.table, query, head=head, body=body, json_body=json_body))
        return result
    
    def query(self):
        if self._query is None or isinstance(self._query, (orm.Result, Select)): #query result
            offset = self.pageno*self.rows_per_page
            limit = self.rows_per_page
            query = self.query_model(self.model, self.condition, offset=offset, limit=limit, order_by=self.order_by)
            if isinstance(query, Select):
                self.total = self.model.count(query._whereclause)
            else:
                self.total = query.count()
        else:
            query = self.query_range(self.pageno, self.pagination)
        return query
    
    def json(self):
        return self.run(head=False, body=True, json_body=True)

    def get_field_display(self, record, field_name):
        if hasattr(self.model, field_name):
            field = getattr(self.model, field_name)
        else:
            for x in self.table['fields_list']:
                if x['name'] == field_name:
                    field = x
        v = make_view_field(field, record, self.types_convert_map, self.fields_convert_map)
        return v
    
    def render(self, table, query, head=True, body=True, json_body=False):
        """
        table is a dict, just like
        table = {'fields_name':[fieldname,...],
            'fields_list':[{'name':fieldname,'width':100,'align':'left'},...],
            'count':10,
        """
        from uliweb.orm import do_
        result = {'total':self.total, 'table_id':self.id, 'pageno':self.pageno+1,
            'page_rows':self.rows_per_page}
        s = []
        if head:
            if self.table_width:
                width = ' width="%dpx"' % table['width']
            else:
                width = ''
            s = ['<table class="%s" id=%s%s>' % (self.table_class_attr, self.id, width)]
            s.append('<thead>')
            s.extend(self.create_table_head(table))
            s.append('</thead>')
            s.append('<tbody>')
        
        if body:
            self.rows_num = 0
            #create table body
            if isinstance(query, Select):
                query = do_(query)
            for record in query:
                self.rows_num += 1
                r = []
                for i, x in enumerate(table['fields_list']):
                    if hasattr(self.model, x['name']):
                        field = getattr(self.model, x['name'])
                    else:
                        field = x
                    v = make_view_field(field, record, self.types_convert_map, self.fields_convert_map)
                    r.append((x['name'], v['display']))
                    
                if json_body:
                    _r = self.json_body_render(r)
                    if 'id' not in _r and hasattr(record, 'id'):
                        _r['id'] = getattr(record, 'id')
                    s.append(_r)
                else:
                    s.extend(self.default_body_render(r))
                self.cal_total(table, record)
            if json_body:
                total = self.render_total(table, json_body)
                if total:
                    s.append(dict(zip(table['fields'], total)))
                result['rows'] = s
            else:
                s.extend(self.render_total(table))
            
        if head:
            s.append('</tbody>')
            s.append('</table>')
        
        if not json_body:
            result['table'] = '\n'.join(s)
        return result
    
    def objects(self):
        """
        Return a generator of all processed data, it just like render
        but it'll not return a table or json format data but just
        data. And the data will be processed by fields_convert_map if passed.
        """
        query = self.query()
        for record in query:
            self.rows_num += 1
            r = {}
            for i, x in enumerate(self.table['fields_list']):
                if hasattr(self.model, x['name']):
                    field = getattr(self.model, x['name'])
                else:
                    field = x
                v = make_view_field(field, record, self.types_convert_map, self.fields_convert_map)
                r[x['name']] = v['display']
            yield r
        
    def query_all(self):
        """
        Query all records without limit and offset.
        """
        return self.query_model(self.model, self.condition, order_by=self.order_by)
    
    def query_model(self, model, condition=None, offset=None, limit=None, order_by=None, fields=None):
        """
        Query all records with limit and offset, it's used for pagination query.
        """
        if self._query is not None:
            query = self._query
            if condition is not None and isinstance(query, Result):
                query = query.filter(condition)
        else:
            query = model.filter(condition)
        if self.pagination:
            if offset is not None:
                query.offset(int(offset))
            if limit is not None:
                query.limit(int(limit))
        if order_by is not None:
            if isinstance(order_by, (tuple, list)):
                for order in order_by:
                    query.order_by(order)
            else:
                query.order_by(order_by)
        return query
        
    def table_info(self):
        t = {'fields_name':[], 'fields_list':[], 'fields':[]}
    
        if self.fields:
            fields = self.fields
        elif hasattr(self.model, self.meta):
            fields = getattr(self.model, self.meta).fields
        else:
            fields = [x for x, y in self.model._fields_list]
            
        def get_table_meta_field(name):
            if hasattr(self.model, self.meta):
                for f in getattr(self.model, self.meta).fields:
                    if isinstance(f, dict):
                        if name == f['name']:
                            return f
                    elif isinstance(f, str):
                        return None
            
        w = 0
        fields_list = []
        for x in fields:
            if isinstance(x, (str, unicode)):
                name = x
                d = {'name':x}
                f = get_table_meta_field(name)
                if f:
                    d = f
            elif isinstance(x, dict):
                name = x['name']
                d = x
            if 'verbose_name' not in d:
                if hasattr(self.model, name):
                    d['verbose_name'] = getattr(self.model, name).verbose_name or name
                else:
                    d['verbose_name'] = name
            t['fields_list'].append(d)
            t['fields_name'].append(d['verbose_name'])
            t['fields'].append(name)
            w += d.get('width', 100)
            
        t['width'] = w
        return t
    
class QueryView(object):
    success_msg = _('The information has been saved successfully!')
    fail_msg = _('There are somethings wrong.')
    builds_args_map = {}
    meta = 'QueryForm'
    
    def __init__(self, model, ok_url, form=None, success_msg=None, fail_msg=None, 
        data=None, fields=None, form_cls=None, form_args=None,
        static_fields=None, hidden_fields=None, post_created_form=None, 
        layout=None, get_form_field=None, links=None):

        self.model = model
        self.ok_url = ok_url
        self.form = form
        if success_msg:
            self.success_msg = success_msg
        if fail_msg:
            self.fail_msg = fail_msg
        self.data = data or {}
        self.get_form_field = get_form_field
        
        #default_data used for create object
#        self.default_data = default_data or {}
        
        self.fields = fields or []
        self.form_cls = form_cls
        self.form_args = form_args or {}
        self.static_fields = static_fields or []
        self.hidden_fields = hidden_fields or []
        self.post_created_form = post_created_form
        self.links = links or []
        
        #add layout support
        self.layout = layout
        
    def get_fields(self):
        f = []
        for field_name, prop in get_fields(self.model, self.fields, self.meta):
            d = prop.copy()
            d['static'] = field_name in self.static_fields
            d['hidden'] = field_name in self.hidden_fields
            d['required'] = False
            f.append(d)
        return f
    
    def get_layout(self):
        if self.layout:
            return self.layout
        if hasattr(self.model, self.meta):
            m = getattr(self.model, self.meta)
            if hasattr(m, 'layout'):
                return getattr(m, 'layout')
    
    def make_form(self):
        import uliweb.form as form
        from uliweb.form.layout import QueryLayout
        
        if self.form:
            return self.form
        
        if isinstance(self.model, str):
            self.model = get_model(self.model)
            
        if self.form_cls:
            class DummyForm(self.form_cls):pass
            if not hasattr(DummyForm, 'form_buttons'):
                DummyForm.form_buttons = form.Submit(value=_('Query'), _class=".submit")
            if not hasattr(DummyForm, 'layout_class'):
                DummyForm.layout_class = QueryLayout
            if not hasattr(DummyForm, 'form_method'):
                DummyForm.form_method = 'GET'
#            if not hasattr(DummyForm, 'form_action') or not DummyForm.form_action:
#                DummyForm.form_action = request.path
        else:
            class DummyForm(form.Form):
                layout_class = QueryLayout
                form_method = 'GET'
                form_buttons = form.Submit(value=_('Query'), _class=".submit")
#                form_action = request.path
            
        #add layout support
        layout = self.get_layout()
        DummyForm.layout = layout
        
        for f in self.get_fields():
            flag = False
            if self.get_form_field:
                field = self.get_form_field(f['name'])
                if field:
                    flag = True
            if not flag:
                field = make_form_field(f, self.model, builds_args_map=self.builds_args_map)
            if field:
                DummyForm.add_field(f['name'], field, True)
        
        if self.post_created_form:
            self.post_created_form(DummyForm, self.model)
            
        form = DummyForm(data=self.data, **self.form_args)
        form.links = self.links
        return form
    
    def run(self):
        from uliweb import request
        
        if isinstance(self.model, str):
            self.model = get_model(self.model)
            
        flash = functions.flash
        
        if not self.form:
            self.form = self.make_form()
        
        flag = self.form.validate(request.values)
        if flag:
#            d = self.default_data.copy()
            if self.data:
                for k, v in self.data.iteritems():
                    if not self.form.data.get(k):
                        self.form.data[k] = v
            return self.form.data.copy()
        else:
            return {}
        
