import time, re
from datetime import tzinfo, timedelta, datetime, date, time as time_
from sorteddict import SortedDict

__timezone__ = None
__local_timezone__ = None
__timezones__ = SortedDict()

class DateError(Exception):pass
class TimeFormatError(Exception):pass

DEFAULT_DATETIME_INPUT_FORMATS = (
    '%Y-%m-%d %H:%M:%S',     # '2006-10-25 14:30:59'
    '%Y-%m-%d %H:%M:%S.%f',  # '2006-10-25 14:30:59.5200'
    '%Y-%m-%d %H:%M',        # '2006-10-25 14:30'
    '%Y-%m-%d',              # '2006-10-25'
    '%Y/%m/%d %H:%M:%S',     # '2006/10/25 14:30:59'
    '%Y/%m/%d %H:%M:%S.%f',  # '2006/10/25 14:30:59.5200'
    '%Y/%m/%d %H:%M',        # '2006/10/25 14:30'
    '%Y/%m/%d',              # '2006/10/25 '
    '%m/%d/%Y %H:%M:%S',     # '10/25/2006 14:30:59'
    '%m/%d/%Y %H:%M:%S.%f',  # '10/25/2006 14:30:59.5200'
    '%m/%d/%Y %H:%M',        # '10/25/2006 14:30'
    '%m/%d/%Y',              # '10/25/2006'
    '%m/%d/%y %H:%M:%S',     # '10/25/06 14:30:59'
    '%m/%d/%y %H:%M:%S.%f',  # '10/25/06 14:30:59.5200'
    '%m/%d/%y %H:%M',        # '10/25/06 14:30'
    '%m/%d/%y',              # '10/25/06'
    '%H:%M:%S',              # '14:30:59'
    '%H:%M',                 # '14:30'
)

ZERO = timedelta(0)

class UTCTimeZone(tzinfo):
    """UTC"""

    def utcoffset(self, dt):
        return ZERO

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return ZERO
    
    def __repr__(self):
        return '<tzinfo UTC>'

UTC = UTCTimeZone()

class FixedOffset(tzinfo):
    """Fixed offset in minutes east from UTC."""

    def __init__(self, offset, name):
        self.__offset = timedelta(minutes = offset)
        self.__name = name

    def utcoffset(self, dt):
        return self.__offset

    def tzname(self, dt):
        return self.__name

    def dst(self, dt):
        return ZERO
    
    def __repr__(self):
        return "<tzinfo %s>" % self.__name
    
for i in range(-12, 13):
    if i == 0:
        continue
    if i>0:
        k = 'GMT +%d' % i
    else:
        k = 'GMT %d' % i
    __timezones__[k] = FixedOffset(i*60, k)
    
__timezones__['UTC'] = UTC
re_timezone = re.compile(r'GMT\s?([+-]?)(\d+)', re.IGNORECASE)

def fix_gmt_timezone(tz):
    if isinstance(tz, (str, unicode)):
        b = re_timezone.match(tz)
        if b:
            n = b.group(2)
            if n == '0':
                return 'UTC'
            sign = b.group(1)
            if not sign:
                sign = '+'
            return 'GMT ' + sign + n
    return tz

def set_timezone(tz):
    global __timezone__
    __timezone__ = timezone(tz)
    
def get_timezone():
    return __timezone__

def set_local_timezone(tz):
    global __local_timezone__
    __local_timezone__ = timezone(tz)
    
def get_local_timezone():
    return __local_timezone__

def get_timezones():
    return __timezones__

def register_timezone(name, tz):
    __timezones__[name] = tz
    
def timezone(tzname):
    if not tzname:
        return None
    
    if isinstance(tzname, (str, unicode)):
        #not pytz module imported, so just return None
        tzname = fix_gmt_timezone(tzname)
        tz = __timezones__.get(tzname, None)
        if not tz:
            raise DateError, "Can't find tzname %s" % tzname
        return tz
    elif isinstance(tzname, tzinfo):
        return tzname
    else:
        raise DateError, "Unsupported tzname %r type" % tzname
    
def pick_timezone(*args):
    for x in args:
        tz = timezone(x)
        if tz:
            return tz
    
def now(tzinfo=None):
    tz = pick_timezone(tzinfo, __timezone__)
    return datetime.now(tz)

def today(tzinfo=None):
    d = now(tzinfo)
    return to_date(d, tzinfo)

def to_timezone(dt, tzinfo=None):
    """
    Convert a datetime to timezone
    """
    if not dt:
        return dt
    tz = pick_timezone(tzinfo, __timezone__)
    if not tz:
        return dt
    dttz = getattr(dt, 'tzinfo', None)
    if not dttz:
        return dt.replace(tzinfo=tz)
    else:
        return dt.astimezone(tz)
    
def to_date(dt, tzinfo=None, format=None):
    """
    Convert a datetime to date with tzinfo
    """
    d = to_datetime(dt, tzinfo, format)
    if not d:
        return d
    return date(d.year, d.month, d.day)

def to_time(dt, tzinfo=None, format=None):
    """
    Convert a datetime to time with tzinfo
    """
    d = to_datetime(dt, tzinfo, format)
    if not d:
        return d
    return time_(d.hour, d.minute, d.second, d.microsecond, tzinfo=d.tzinfo)

def to_datetime(dt, tzinfo=None, format=None):
    """
    Convert a date or time to datetime with tzinfo
    """
    if not dt:
        return dt
    
    tz = pick_timezone(tzinfo, __timezone__)
    
    if isinstance(dt, (str, unicode)):
        if not format:
            formats = DEFAULT_DATETIME_INPUT_FORMATS
        else:
            formats = list(format)
        d = None
        for fmt in formats:
            try:
                d = datetime.strptime(dt, fmt)
            except ValueError:
                continue
        if not d:
            return None
        d = d.replace(tzinfo=tz)
    else:
        d = datetime(getattr(dt, 'year', 1970), getattr(dt, 'month', 1),
            getattr(dt, 'day', 1), getattr(dt, 'hour', 0), getattr(dt, 'minute', 0),
            getattr(dt, 'second', 0), getattr(dt, 'microsecond', 0))
        if not getattr(dt, 'tzinfo', None):
            d = d.replace(tzinfo=tz)
        else:
            d = d.replace(tzinfo=dt.tzinfo)
    return to_timezone(d, tzinfo)

def to_local(dt, tzinfo=None):
    tz = pick_timezone(tzinfo, __local_timezone__)
    return to_datetime(dt, tzinfo=tz)

def to_string(dt, microsecond=False, timezone=True):
    if isinstance(dt, datetime):
        format = '%Y-%m-%d %H:%M:%S'
        if microsecond:
            format += '.%f'
        if timezone:
            format += ' %Z'
        return dt.strftime(format).rstrip()
    elif isinstance(dt, date):
        return dt.strftime('%Y-%m-%d')
    elif isinstance(dt, time_):
        format = '%H:%M:%S'
        if microsecond:
            format += '.%f'
        return dt.strftime(format)

re_time = re.compile(r'(\d+)([s|ms|h|m])')
def parse_time(t):
    """
    Parse string time format to microsecond
    """
    if isinstance(t, (str, unicode)):
        b = re_time.match(t)
        if b:
            v, unit = int(b.group(1)), b.group(2)
            if unit == 's':
                return v*1000
            elif unit == 'm':
                return v*60*1000
            elif unit == 'h':
                return v*60*60*1000
            else:
                return v
        else:
            raise TimeFormatError(t)
    elif isinstance(t, (int, long)):
        return t
    else:
        raise TimeFormatError(t)

    
#if __name__ == '__main__':
#    GMT8 = timezone('GMT +8')
#    d = to_datetime('2011-9-13 20:14:15', tzinfo=GMT8)
#    print repr(d)
#    set_timezone(UTC)
#    print repr(to_datetime(d))
#    set_local_timezone('GMT +8')
#    print get_local_timezone()
#    print repr(to_local(d))