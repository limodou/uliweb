from uliweb.i18n import gettext_lazy as _

def __get_choices_keys(choices):
    if callable(choices):
        choices = choices()
    if isinstance(choices, dict):
        keys = set(choices.keys())
    elif isinstance(choices, (list, tuple)):
        keys = set([])
        for v in choices:
            if isinstance(v, (list, tuple)):
                keys.add(v[0])
            else:
                keys.add(v)
    else:
        raise Exception, _('Choices need a dict, tuple or list data.')
    return keys
    
def IS_IN_SET(choices):
    '''
    choices should be a list or a tuple, e.g. [1,2,3]
    '''
    def f(data):
        if data not in __get_choices_keys(choices):
            return _('Select a valid choice. That choice is not one of the available choices.')
    return f

def IS_IMAGE(size=None):
    def f(data):
        import Image
        try:
            try:
                image = Image.open(data.file)
                if size:
                    if image.size[0]>size[0] or image.size[1]>size[1]:
                        return _("The image file size exceeds the limit.")
            except Exception, e:
                return _("The file is not a valid image.")
        finally:
            data.file.seek(0)
    return f

def IS_PAST_DATE(date=None):
    """Used for test the date should less than some day"""
    def f(data, date=date):
        import datetime
        
        if isinstance(date, datetime.date):
            if not date:
                date = datetime.date.today()
        elif isinstance(date, datetime.datetime):
            if not date:
                date = datetime.datetime.now()
        else:
            return 'Not support this type %r' % data
        
        if data > date:
            return 'The date can not be greater than %s' % date
    return f
    