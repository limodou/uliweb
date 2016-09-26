#coding=utf8
from uliweb import functions, url_for
import logging
from forms import QueryForm

log = logging.getLogger(__name__)
class Default(object):pass

class MultiView(object):
    """
    Multi View Class

    Support: list, add, delete, edit, detail, etc
    """

    def _process_fields_convert_map(self, parameters):
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
            parameters['fields_convert_map'] = self._get_fields_convert_map(_f)


    def _get_fields_convert_map(self, fields):
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
        _f = fields
        if isinstance(_f, list):
            t = {}
            for k in _f:
                if isinstance(k, str):
                    t[k] = getattr(self, '_convert_{}'.format(k))
                elif isinstance(k, (tuple, list)):
                    name = k[0]
                    func = k[1]
                    if isinstance(func, str):
                        t[name] = getattr(self, '_convert_{}'.format(func))
                    elif callable(func):
                        t[name] = func
                    else:
                        raise ValueError("Fields convert function should be str or callable, but %r found" % type(func))
                else:
                    raise ValueError("Fields convert element should be str or tuple or list, but %r found" % type(k))
        elif isinstance(_f, dict):
            t = {}
            for k, v in _f.items():
                if isinstance(v, str):
                    t[k] = getattr(self, '_convert_{}'.format(v))
                elif callable(v):
                    t[k] = v
                else:
                    raise ValueError("Fields convert function should be str or callable, but %r found" % type(func))
        return t

    def _list_view(self, model, **kwargs):
        """
        :param model:
        :param fields_convert_map: it's different from ListView
        :param kwargs:
        :return:
        """
        view =  functions.ListView(model, **kwargs)
        return view


    def _query_view(self, model, **kwargs):
        """
        :param model:
        :return: (query, condition)

        Default use QueryForm
        """
        QueryForm = functions.get_form('QueryForm')

        if 'form_cls' not in kwargs:
            kwargs['form_cls'] = QueryForm
        query = functions.QueryView(model, **kwargs)
        return query


    def _list(self, model, queryview=None, queryform=None, **kwargs):
        from uliweb import request, json, CONTENT_TYPE_JSON
        from sqlalchemy import and_
        from uliweb.utils.generic import get_sort_field

        if queryview:
            queryview.run()
            condition = queryview.get_condition()
        else:
            condition = None

        if 'condition' in kwargs:
            condition = and_(condition, kwargs['condition'])
            kwargs['condition'] = condition
        else:
            kwargs['condition'] = condition

        #process order
        if 'order_by' not in kwargs:
            order_by = get_sort_field(model)
            if order_by is not None:
                kwargs['order_by'] = order_by

        self._process_fields_convert_map(kwargs)
        downloads = {}
        downloads['filename'] = kwargs.pop('download_filename', 'download.xlsx')
        downloads['action'] = kwargs.pop('download_action', 'download')
        downloads['fields_convert_map'] = kwargs.pop('download_fields_convert_map',
                                                  kwargs.get('fields_convert_map'))
        downloads['domain'] = kwargs.pop('download_domain', '')
        downloads['timeout'] = 0
        downloads.update(kwargs.pop('download_kwargs', {}))
        self._process_fields_convert_map(downloads)

        #get list view
        view = self._list_view(model=model, **kwargs)

        if 'data' in request.values:
            return json(view.json(), content_type=CONTENT_TYPE_JSON)
        elif 'download' in request.GET:
            return view.download(**downloads)
        else:
            result = view.run()
            if queryview:
                result.update({'query_form':queryform or queryview.form})
            else:
                result.update({'query_form':''})
            result.update({'table':view})
            return result

    def _view(self, model, obj, **kwargs):
        self._process_fields_convert_map(kwargs)

        view = functions.DetailView(model, obj=obj, **kwargs)
        return view.run()

    def _add(self, model, json_result=False, **kwargs):
        self._process_fields_convert_map(kwargs)

        view = functions.AddView(model, **kwargs)
        return view.run(json_result=json_result)

    def _edit(self, model, obj, json_result=False, **kwargs):
        self._process_fields_convert_map(kwargs)

        view = functions.EditView(model, obj=obj, **kwargs)
        return view.run(json_result=json_result)

    def _delete(self, model, obj, json_result=False, **kwargs):
        view = functions.DeleteView(model, obj=obj, **kwargs)
        return view.run(json_result=json_result)

    def _select_list(self, queryview=None, download_filename=None, **kwargs):
        from uliweb import request, json

        if queryview:
            queryview.run()
            condition = queryview.get_condition()
        else:
            condition = None

        if 'condition' in kwargs:
            condition = and_(condition, kwargs['condition'])
            kwargs['condition'] = condition
        else:
            kwargs['condition'] = condition

        view = functions.SelectListView(**kwargs)
        if 'data' in request.values:
            return json(view.json())
        elif 'download' in request.GET:
            filename = download_filename or 'download.xls'
            kwargs.setdefault('action', 'download')
            kwargs.setdefault('timeout', 0)
            return view.download(filename, **kwargs)
        else:
            result = view.run()
            if queryview:
                result.update({'query_form':queryview.form})
            else:
                result.update({'query_form':''})
            result.update({'table':view})
            return result

    def _search(self, model, condition=None, search_field='name', value_field='id', label_field=None):
        """
        Default search function
        :param search_field: Used for search field, default is 'name'
        :param value_field: Used for id field, default is id
        :param label_field: Used for label field, default is None, then it'll use unicode() function
        """
        from uliweb import json, request

        name = request.GET.get('term', '')
        M = functions.get_model(model)

        def _v(label_field):
            if label_field:
                return lambda x: getattr(x, label_field)
            else:
                return lambda x: unicode(x)

        v_field = request.values.get('label', 'title')
        v_func = _v(label_field)
        if name:
            if condition is None:
                condition = M.c[search_field].like('%' + name + '%')
            result = [{'id': getattr(obj, value_field), v_field: v_func(obj)}
                      for obj in M.filter(condition)]
        else:
            result = []
        return json(result)


def get_model_columns(model, fields=None, meta='Table'):
    """
    Get fields info according model class, the fields just like ListView fields definition
    :param fields: A list
    :param meta: if no fields, it'll use meta
    """
    from copy import deepcopy

    fields = fields or []
    model = functions.get_model(model)

    if not fields:
        if hasattr(model, meta):
            fields = getattr(model, meta).fields
        else:
            fields = [x for x, y in model._fields_list]

    fields_list = []
    for x in fields:
        if isinstance(x, (str, unicode)):
            f = get_grid_column(model, x)
        elif isinstance(x, dict):
            name = x['name']
            f = deepcopy(x)
            if 'title' not in x:
                f.update(get_grid_column(model, name))
        else:
            raise ValueError("Field should be string or dict type, but {!r} found".format(x))
        fields_list.append(f)
    return fields_list

def get_grid_column(model, name):
    field = getattr(model, name, None)
    d = {'name':name, 'title':name}
    if field:
        d = {'name': name, 'title': field.verbose_name or field.name}
    return d
