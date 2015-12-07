from uliweb.i18n import gettext_lazy as _, LazyString
import re
from uliweb.utils import date

class RuleNotRight(Exception):pass

class Validator(object):
    default_message = _('There is an error!')

    def __init__(self, args=None, message=None, extra=None, next=None, field=None):
        self.message = message or self.default_message
        self.extra = extra or {}
        self.args = args
        self.next = next
        self.result = None
        self.field = field
        self.init()

    def get_message(self):
        if isinstance(self.message, LazyString):
            message = unicode(self.message)
        else:
            message = self.message
        return message.format(**self.extra)

    def validate(self, data, all_data=None):
        return True

    def init(self):
        if self.field:
            self.extra['label'] = self.field.label

    def __call__(self, data, all_data=None):
        self.result = data
        if not self.validate(data, all_data):
            return self.get_message()
        if self.next:
            return self.next(self.result)

class TEST_IN(Validator):
    default_message = _('The value is not in choices.')

    def init(self):
        super(TEST_IN, self).init()

        choices = self.args

        if callable(choices):
            choices = choices()
        if isinstance(choices, dict):
            self.keys = choices
        elif isinstance(choices, (list, tuple)):
            keys = set([])
            for v in choices:
                if isinstance(v, (list, tuple)):
                    keys.add(v[0])
                else:
                    keys.add(v)
            self.keys = keys

    def validate(self, data, all_data=None):
        return data in self.keys

class TEST_IMAGE(Validator):
    default_message = _('The file is not a valid image file.')

    def validate(self, data, all_data=None):
        from PIL import Image
        try:
            try:
                if isinstance(data, (str, unicode)):
                    _file = data
                else:
                    _file = data.file
                image = Image.open(_file)
                self.result = image
                return True
            except Exception as e:
                return False
        finally:
            data.file.seek(0)

class TEST_IMAGE_SIZE(Validator):
    default_message = _('The image file size exceeds the limit {size!r}.')

    def init(self):
        super(TEST_IMAGE_SIZE, self).init()
        self.extra['size'] = self.args

    def validate(self, data, all_data=None):
        size = self.args
        image = data

        if size and image.size[0]>size[0] or image.size[1]>size[1]:
            return False
        else:
            return True

class TEST_EQUALTO(Validator):
    default_message = _('Please enter the same value to {target}.')

    def init(self):
        super(TEST_EQUALTO, self).init()
        if isinstance(self.args, (tuple, list)):
            self.extra['target'] = self.args[1]
            self.args = self.args[0]
        else:
            self.extra['target'] = self.args

    def validate(self, data, all_data=None):
        return data == all_data.get(self.args)

class TEST_MINLENGTH(Validator):
    default_message = _('Please enter at least {minlength} characters.')

    def init(self):
        super(TEST_MINLENGTH, self).init()
        self.extra['minlength'] = self.args

    def validate(self, data, all_data=None):
        return len(data)>=self.args

class TEST_MAXLENGTH(Validator):
    default_message = _('Please enter no more than {maxlength} characters.')

    def init(self):
        super(TEST_MAXLENGTH, self).init()
        self.extra['maxlength'] = self.args

    def validate(self, data, all_data=None):
        return len(data)<=self.args

class TEST_RANGELENGTH(Validator):
    default_message = _('Please enter a value between {minlength} and {maxlength} characters long.')

    def init(self):
        super(TEST_RANGELENGTH, self).init()
        self.extra['minlength'], self.extra['maxlength'] = self.args

    def validate(self, data, all_data=None):
        _len = len(data)
        return self.args[0] <= _len <= self.args[1]

class TEST_MIN(Validator):
    default_message = _('Please enter a value greater than or equal to {min}.')

    def init(self):
        super(TEST_MIN, self).init()
        self.extra['min'] = self.args

    def validate(self, data, all_data=None):
        return data>=self.args

class TEST_MAX(Validator):
    default_message = _('Please enter a value less than or equal to {max}.')

    def init(self):
        super(TEST_MAX, self).init()
        self.extra['max'] = self.args

    def validate(self, data, all_data=None):
        return data<=self.args

class TEST_RANGE(Validator):
    default_message = _('Please enter a value between %(min)d and %(max)d.')

    def init(self):
        super(TEST_RANGE, self).init()
        self.extra['min'], self.extra['max'] = self.args

    def validate(self, data, all_data=None):
        return self.args[0] <= data <= self.args[1]

class TEST_DATE(Validator):
    default_message = _('Please enter a valid date.')

    def validate(self, data, all_data=None):
        return bool(date.to_date(data))

class TEST_DATETIME(Validator):
    default_message = _('Please enter a valid datetime.')

    def validate(self, data, all_data=None):
        return bool(date.to_datetime(data))

class TEST_TIME(Validator):
    default_message = _('Please enter a valid time.')

    def validate(self, data, all_data=None):
        return bool(date.to_time(data))

r_url = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

class TEST_URL(Validator):
    default_message = _('Please enter a valid URL.')

    def validate(self, data, all_data=None):
        return bool(r_url.match(data))

r_email = re.compile(r'^(\w)+(\.\w+)*@(\w)+((\.\w+)+)$')

class TEST_EMAIL(Validator):
    default_message = _('Please enter a valid email address.')

    def validate(self, data, all_data=None):
        return bool(r_email.match(data))

r_number = re.compile(r'^(-?\d+)(\.\d+)?$')
class TEST_NUMBER(Validator):
    default_message = _('Please enter a valid number.')

    def validate(self, data, all_data=None):
        return bool(r_number.match(data))

class TEST_DIGITS(Validator):
    default_message = _('Please enter only digits.')

    def validate(self, data, all_data=None):
        return data.isdigit()

class TEST_NOT_EMPTY(Validator):
    default_message = _('This field is required.')

    def validate(self, data, all_data=None):
        return data or (isinstance(data, (str, unicode)) and data.strip())
