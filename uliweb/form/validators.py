from uliweb.i18n import gettext_lazy as _
import re

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
        from PIL import Image
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
    
def IS_LENGTH_LESSTHAN(length):
    """
    Validate the length of value should be less than specified range, not include the
    length.
    """
    def f(data, length=length):
        if not (len(data) < length):
            return _('The length of data should be less than %d.' % length)
    return f
    
def IS_LENGTH_GREATTHAN(length):
    """
    Validate the length of value should be less than specified range, not include the
    length.
    """
    def f(data, length=length):
        if not (len(data) > length):
            return _('The length of data should be great than %d.' % length)
    return f

def IS_LENGTH_BETWEEN(min, max):
    """
    Validate the length of value should be between in specified range, not include
    min and max.
    """
    def f(data, min=min, max=max):
        if not (min < len(data) < max):
            return _('The length of data should be bwtween in (%s, %s).' % (min, max))
    return f

r_url = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

def IS_URL(data):
    """
    Validate if the data is a valid url
    """
    b = r_url.match(data)
    if not b:
        return _('The input value is not a valid url')