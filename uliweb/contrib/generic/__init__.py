#coding=utf8
from uliweb import functions
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
    class _query_config(object):
        url = ''
        fields = _not_implemented()
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
        layout = _not_implemented()
        url_func = 'list'
        form_cls = QueryForm

    class _list_config(object):
        condition = None
        query = None
        order_by = None
        group_by = None
        having = None
        pagination = True
        fields = None
        fields_convert_map = None
        id = 'listview_table'
        meta = 'Table'

    _query_parameters = ['url', 'fields', 'layout', 'url_func', 'form_cls']
    _list_parameters = ['condition', 'query', 'order_by', 'group_by', 'having',
                        'pagination', 'fields', 'fields_convert_map', 'id',
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

    def _get_query_view(self, model=None, url=None, fields=None, layout=None, form_cls=None):
        _fields = self._make_query_form_fields(model, fields)
        query = functions.QueryView(model, ok_url=url, fields=_fields, layout=layout,
                                    form_cls=form_cls)
        return query

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

    def _make_query_form_fields(self, model, fields):
        _fields = []
        for f in fields:
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
            if not isinstance(v, dict):
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

    def _process_fields_convert_map(self, model, parameters):
        #process field_convert_map, ListView doesn't support list type but dict
        if 'fields_convert_map' in parameters:
            _f = parameters.get('fields_convert_map')
            if isinstance(_, list):
                t = {}
                for k in _f:
                    t[k] = getattr(self, '_convert_{}'.format(k))
                parameters['fields_convert_map'] = t


    def _get_list_view(self, model, condition, parameters, meta_cls, post_condition=None):
        """
        :param model:
        :param fields_convert_map: it's different from ListView
        :param kwargs:
        :return:
        """
        para = self._collect_parameters(self._list_parameters, parameters,
                                        meta_cls or self._list_config)

        #process field_convert_map, ListView doesn't support list type but dict
        _fields_convert_map = para.get('fields_convert_map')

        if _fields_convert_map:
            if isinstance(_fields_convert_map, list):
                t = {}
                for k in _fields_convert_map:
                    t[k] = getattr(self, '_convert_{}'.format(k))
                para['fields_convert_map'] = t

        #process condition
        self._process_condition(model, condition, para, post_condition)

        log.debug("List parameters is %r", para)
        view =  functions.ListView(model, **para)
        return view

    def _get_url(self, function='', url='', **kwargs):
        def _f(func=function, url=url, kwargs=kwargs):
            from uliweb import url_for

            kwargs = kwargs or {}
            if func:
                return url_for(getattr(self.__class__, function, **kwargs))
            else:
                return url_for(url, **kwargs)
        return _f

    def _collect_parameters(self, para_list, parameters, meta_cls):
        if parameters:
            _g = parameters.get
            def _get(key):
                return self._get_arg(_g(key), key, meta_cls or self)
        else:
            if isinstance(meta_cls, str):
                meta_cls = getattr(self, meta_cls)
            meta = meta_cls()
            def _get(key):
                return getattr(meta, key, None)

        para = {}
        for k in para_list:
            para[k] = _get(k)
        return para

    @classmethod
    def _get_model(cls, model=None):
        return functions.get_model(cls._get_arg(model, '_model'))

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

        para = self._collect_parameters(self._query_parameters, parameters, meta_cls)

        log.debug("Query config parameters is %r", para)

        #get query
        layout = para['layout']
        if not layout:
            layout = []
            for x in para['fields']:
                if isinstance(x, str):
                    layout.append(x)
                else:
                    layout.append(x['name'])

        query = self._get_query_view(model=model,
                         url=self._get_url(function=para['url_func'], url=para['url']),
                         fields=para['fields'],
                         layout=layout,
                         form_cls=para['form_cls'])

        #get query value
        query_value = query.run()

        #get query condition
        condition = self._get_query_condition(model, fields=para['fields'],
                                              values=query_value)

        return query, condition


    def _default_list(self, model=None,
                      query_config=None,
                      query_config_name=None,
                      list_config=None,
                      list_config_name=None,
                      post_condition=None):
        from uliweb import request, json

        #get parameters
        _model = self._get_arg(model, '_model')

        #get model
        model = functions.get_model(_model)

        #get query instance and condition
        query_inst, _cond = self._default_query(model, query_config, query_config_name)

        #get list view
        view = self._get_list_view(model=model,
                                   condition=_cond,
                                   parameters=list_config,
                                   meta_cls=list_config_name)
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
