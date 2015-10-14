from uliweb import Finder, UliwebError, settings
from uliweb.utils.common import import_attr

validators = Finder('VALIDATORS')

def get_form(formcls):
    """
    get form class according form class path or form class object
    """
    from uliweb.form import Form
    import inspect
    
    if inspect.isclass(formcls) and issubclass(formcls, Form):
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

def startup_installed(sender):
    from uliweb import settings
    import uliweb.form.uliform as form
    from uliweb.utils.common import import_attr

    for k, v in settings.get_var('FORM_FIELDS_MAP', {}).items():
        form.fields_mapping[k] = import_attr(v)

