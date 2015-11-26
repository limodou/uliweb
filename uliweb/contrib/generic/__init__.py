#coding=utf8
from uliweb import functions, url_for
import logging
from forms import QueryForm

log = logging.getLogger(__name__)

class _not_implemented(object):
    def __get__(self, inst, cls):
        raise NotImplementedError

class MultiView(object):
    """
    Multi View Class

    Support: list, add, delete, edit, detail, etc

    You should config it before use it
    """

    _model = _not_implemented()

    ######################################
    #query
    ######################################
    class QueryConfig(object):
        fields = []
        #query field format
        # [
        #   {   'name':<name>,
        #       'label':None or <label>, if None it'll search model to get field verbose_name
        #       'type':None or Field type, if None it'll search model to guess field type,
        #       'field':None or Field instance,
        #       'kwargs':<kwargs> extra parameters,
        #       'like': '%_' or '%_%' or '_%' different like mode
        #       'op': 'gt', 'lt', 'ge', 'ne'
        #       'render': function(model, name, value, values) used to create condition
        #   }
        # ]
        form_cls = QueryForm

    _query_parameters = ['fields', 'layout', 'form_cls']

    class ListConfig(object):
        pagination = True
        id = 'listview_table'
        meta = 'Table'

    _list_parameters = ['condition', 'order_by', 'group_by', 'having',
                        'pagination', 'fields', 'fields_convert_map', 'id',
                        'meta'
                        ]

    class ViewConfig(object):
        meta = 'DetailView'

    _view_parameters = ['fields', 'fields_convert_map',
                       'layout_class', 'layout',
                       'meta'
                       ]

    class AddConfig(object):
        meta = 'AddForm'
        version = False

    _add_parameters = ['default_data', 'fields', 'static_fields',
                        'fields_convert_map', 'hidden_fields',
                        'layout_class', 'layout', 'rules',
                        'file_replace', 'version',
                        'meta'
                       ]

    class EditConfig(object):
        meta = 'EditForm'
        version = False

    _edit_parameters = ['default_data', 'fields', 'static_fields',
                        'fields_convert_map', 'hidden_fields',
                        'layout_class', 'layout', 'rules',
                        'file_replace', 'version',
                        'meta'
                       ]


    @classmethod
    def _get_arg(cls, value, property_name, klass=None):
        """
        If value is None, then use property_name of current instance
        :param value: argument value
        :param property_name: default property name, if value is None, then use property value
        :return: value or property value, if not defined property, it'll raise Exception
        """
        return value if value is not None else getattr(klass or cls, property_name)

    def _make_form_field(self, model, field):
        from uliweb.utils.generic import make_form_field
        from uliweb.form import get_field_cls

        if isinstance(field, str):
            return field, make_form_field(field, model, use_default_value=False)
        elif isinstance(field, dict):
            if 'field' in field:
                return field['name'], field['field']
            else:
                _type = field.get('type')
                if _type:
                    field_cls = get_field_cls(_type)
                else:
                    field_cls = None
                field['extra'] = field.get('kwargs', {})
                return field['name'], make_form_field(field, model=model,
                                                      use_default_value=False,
                                                      field_cls=field_cls)
        else:
            raise ValueError("Field type is not right, should be str or dict, but %r found" % type(field))

    def _make_query_form_fields(self, model, condition_fields):
        _fields = []
        for f in condition_fields or []:
            name, field = self._make_form_field(model, f)
            _fields.append((name, field))
        return _fields

    def _make_like(self, column, format, value):
        """
        make like condition
        :param column: column object
        :param format: '%_' '_%' '%_%'
        :param value: column value
        :return: condition object
        """
        c = []
        if format.startswith('%'):
            c.append('%')
        c.append(value)
        if format.endswith('%'):
            c.append('%')
        return column.like(''.join(c))

    def _make_op(self, column, op, value):
        """
        make op condition
        :param column: column object
        :param op: gt >, lt <, ge >=, ne !=, le <=, eq ==, in in_,
        :param value: volumn value
        :return: condition object
        """
        if not op:
            return None
        if op == 'gt':
            return column>value
        elif op == 'lt':
            return column<value
        elif op == 'ge':
            return column>=value
        elif op == 'le':
            return column<=value
        elif op == 'eq':
            return column==value
        elif op == 'ne':
            return column!=value
        elif op == 'in':
            return column.in_(value)
        else:
            raise KeyError('Not support this op[%s] value' % op)

    def _get_query_condition(self, model, fields, values):
        from sqlalchemy import true, and_

        condition = true()

        for v in fields:
            if isinstance(v, (tuple, list)):
                v = {'name':v[0]}
            elif not isinstance(v, dict):
                v = {'name':v}
            name = v['name']
            if name in values:
                render = v.get('render')
                value = values[name]
                if not value:
                    continue
                _cond = None
                if render:
                    _cond = render(model, name, value, values)
                else:
                    column = model.c[name]
                    if 'like' in v:
                        _cond = self._make_like(column, v['like'], value)
                    elif 'op' in v:
                        _cond = self._make_op(column, v['op'], value)
                    else:
                        if isinstance(value, (tuple, list)):
                            _cond = column.in_(value)
                        else:
                            _cond = column==value
                if _cond is not None:
                    condition = and_(_cond, condition)

        log.debug("condition=%s", condition)
        return condition

    def _process_condition(self, model, condition, parameters, post_condition=None):
        from sqlalchemy import and_

        #if there is condition in parameters, then it'll be default condition
        #and it'll combine with condition object
        if 'condition' in parameters:
            cond = and_(condition, parameters['condition'])
        else:
            cond = condition

        if post_condition:
            cond = post_condition(model, cond)

        if cond is not None:
            parameters['condition'] = cond

    def _process_fields_convert_map(self, parameters, prefix=''):
        """
        process fields_convert_map, ListView doesn't support list type but dict

        fields_convert_map should be define as list or dict
        for list, it can be:
            [name, name, ...]
            [(name, func), (name, func), ...] if func is str, it'll be the property name of class
        for dict, it can be:
            {'name':func, ...}
        :param model: model object
        :param parameters:
        :param prefix: it'll used to combine prefix+_convert_xxx to get convert function
            from class
        :return:
        """
        if 'fields_convert_map' in parameters:
            _f = parameters.get('fields_convert_map')
            if isinstance(_f, list):
                t = {}
                for k in _f:
                    if isinstance(k, str):
                        t[k] = getattr(self, '{0}_convert_{1}'.format(prefix, k))
                    elif isinstance(k, (tuple, list)):
                        name = k[0]
                        func = k[1]
                        if isinstance(func, str):
                            t[name] = getattr(self, '{0}_convert_{1}'.format(prefix, func))
                        elif callable(func):
                            t[name] = func
                        else:
                            raise ValueError("Fields convert function should be str or callable, but %r found" % type(func))
                    else:
                        raise ValueError("Fields convert element should be str or tuple or list, but %r found" % type(k))
                parameters['fields_convert_map'] = t
            elif isinstance(_f, dict):
                t = {}
                for k, v in _f.items():
                    if isinstance(v, str):
                        t[k] = getattr(self, '{0}_convert_{1}'.format(prefix, v))
                    elif callable(v):
                        t[k] = v
                    else:
                        raise ValueError("Fields convert function should be str or callable, but %r found" % type(func))
                parameters['fields_convert_map'] = t

    def _collect_parameters(self, para_list, parameters, meta_cls):
        parameters = parameters or {}

        if isinstance(meta_cls, str):
            meta_cls = getattr(self, meta_cls)
        meta = meta_cls()

        para = {}
        for k in para_list:
            try:
                para[k] = getattr(meta, k, None)
            except NotImplementedError:
                raise ValueError("Property %s is not implemented yet in class %r" % (k, meta_cls.__name__))

        para.update(parameters)
        return para

    @classmethod
    def _get_model(cls, model=None):
        return functions.get_model(cls._get_arg(model, '_model'))

    @classmethod
    def _get_object(cls, key, model=None):
        _model = cls._get_model(model)
        return _model.get(key)

    def _get_list_view(self, model, condition=None, parameters=None, config=None, post_condition=None,
                       prefix_of_convert_func_name=''):
        """
        :param model:
        :param fields_convert_map: it's different from ListView
        :param kwargs:
        :return:
        """
        para = self._collect_parameters(self._list_parameters, parameters,
                                        config or self.ListConfig)

        self._process_fields_convert_map(para, prefix=prefix_of_convert_func_name)

        #process condition
        self._process_condition(model, condition, para, post_condition)

        log.debug("List parameters is %r", para)
        view =  functions.ListView(model, **para)
        return view





    def _default_query(self, model, parameters=None, meta_cls=None):
        """
        :param model:
        :param meta_cls: config meta class object or string name
        :param parameters: query parameters
        :return: (query, condition)
        """
        #get query parameters
        if not parameters and not meta_cls:
            return None, None

        #get model
        model = self._get_model(model)

        para = self._collect_parameters(self._query_parameters, parameters, meta_cls)
        condition_fields = para.pop('fields', [])

        #get query
        layout = para['layout']
        if not layout:
            layout = []
            for x in para.get('fields') or {}:
                if isinstance(x, str):
                    layout.append(x)
                else:
                    layout.append(x['name'])

        para['fields'] = self._make_query_form_fields(model, condition_fields)

        log.debug("Query config parameters is %r", para)

        query = functions.QueryView(model, **para)

        #get query value
        query_value = query.run()

        #get query condition
        condition = self._get_query_condition(model, fields=condition_fields,
                                              values=query_value)

        return query, condition


    def _list(self, model=None,
                      query_parameters=None,
                      query_config='QueryConfig',
                      list_parameters=None,
                      list_config='ListConfig',
                      post_condition=None):
        from uliweb import request, json

        #get model
        model = self._get_model(model)

        #get query instance and condition
        query_inst, _cond = self._default_query(model, query_parameters, query_config)

        #get list view
        view = self._get_list_view(model=model,
                                   condition=_cond,
                                   parameters=list_parameters,
                                   config=list_config)

        if 'data' in request.values:
            return json(view.json())
        else:
            result = view.run()
            if query_inst:
                result.update({'query_form':query_inst.form})
            else:
                result.update({'query_form':''})
            result.update({'table':view})
            return result

    def _view(self, model=None, obj=None,
                    config='ViewConfig', **parameters):
        para = self._collect_parameters(self._view_parameters, parameters, config)

        self._process_fields_convert_map(para)

        view = functions.DetailView(self._get_model(model),
                                    obj=obj,
                                    **para)
        return view.run()

    def _add(self, model, json_result=False, **kwargs):

        self._process_fields_convert_map(kwargs)

        view = functions.AddView(model, **kwargs)
        return view.run(json_result=json_result)

    def _edit(self, model=None, ok_url=None, obj=None,
                    config='EditConfig', json_result=False, **parameters):
        para = self._collect_parameters(self._edit_parameters, parameters, config)
        para['ok_url'] = ok_url

        self._process_fields_convert_map(para)

        json_result = self._get_arg(json_result, 'json_result', config)
        view = functions.EditView(self._get_model(model),
                                    obj=obj,
                                    **para)
        return view.run(json_result=json_result)



