def get_form(formcls):
    """
    get form class according form class path or form class object
    """
    from uliweb.form import Form
    from uliweb.utils.common import import_attr
    from uliweb import UliwebError, settings
    import types
    
    if isinstance(formcls, types.ClassType) and issubclass(formcls, Form):
        return formcls
    elif isinstance(formcls, (str, unicode)):
        path = settings.FORMS.get(formcls)
        if path:
            _cls = import_attr(path)
            return _cls
        else:
            raise UliwebError("Can't find formcls name %s in settings.FORMS" % formcls)
    else:
        raise UliwebError("formcls should be Form class object or string path format, but %r found!" % formcls)
        