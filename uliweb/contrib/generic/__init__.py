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
                parameters['fields_convert_map'] = t
            elif isinstance(_f, dict):
                t = {}
                for k, v in _f.items():
                    if isinstance(v, str):
                        t[k] = getattr(self, '_convert_{}'.format(v))
                    elif callable(v):
                        t[k] = v
                    else:
                        raise ValueError("Fields convert function should be str or callable, but %r found" % type(func))
                parameters['fields_convert_map'] = t

    def _list_view(self, model, **kwargs):
        """
        :param model:
        :param fields_convert_map: it's different from ListView
        :param kwargs:
        :return:
        """
        self._process_fields_convert_map(kwargs)

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


    def _list(self, model, queryview=None, **kwargs):
        from uliweb import request, json, CONTENT_TYPE_JSON
        from sqlalchemy import and_

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

        #get list view
        view = self._list_view(model=model, **kwargs)

        if 'data' in request.values:
            return json(view.json(), content_type=CONTENT_TYPE_JSON)
        elif 'download' in request.GET:
            filename = 'download.xls'
            kw = {}
            kw['action'] = kwargs.get('download_action', 'download')
            kw['timeout'] = 0
            kw['query'] = kwargs.get('download_query', kwargs.get('query'))
            kw['fields_convert_map'] = kwargs.get('download_fields_convert_map',
                                                  kwargs.get('fields_convert_map'))
            kw['domain'] = kwargs.get('download_domain')
            return view.download(filename, **kw)
        else:
            result = view.run()
            if queryview:
                result.update({'query_form':queryview.form})
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
