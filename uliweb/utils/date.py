import time
import datetime

pytz = None

def use_tz():
    global pytz
    
    try:
        import pytz
    except:
        pytz = None

__timezone__ = None
__local_timezone__ = None

DEFAULT_DATETIME_INPUT_FORMATS = (
    '%Y-%m-%d %H:%M:%S',     # '2006-10-25 14:30:59'
    '%Y-%m-%d %H:%M',        # '2006-10-25 14:30'
    '%Y-%m-%d',              # '2006-10-25'
    '%Y/%m/%d %H:%M:%S',     # '2006/10/25 14:30:59'
    '%Y/%m/%d %H:%M',        # '2006/10/25 14:30'
    '%Y/%m/%d ',             # '2006/10/25 '
    '%m/%d/%Y %H:%M:%S',     # '10/25/2006 14:30:59'
    '%m/%d/%Y %H:%M',        # '10/25/2006 14:30'
    '%m/%d/%Y',              # '10/25/2006'
    '%m/%d/%y %H:%M:%S',     # '10/25/06 14:30:59'
    '%m/%d/%y %H:%M',        # '10/25/06 14:30'
    '%m/%d/%y',              # '10/25/06'
    '%H:%M:%S',              # '14:30:59'
    '%H:%M',                 # '14:30'
)

def set_timezone(tz):
    global __timezone__
    __timezone__ = timezone(tz)
    
def get_default_timezone():
    return __timezone__

def set_local_timezone(tz):
    global __local_timezone__
    __local_timezone__ = timezone(tz)
    
def get_default_local_timezone():
    return __local_timezone__

def timezone(tzname):
    if not tzname:
        return None
    if isinstance(tzname, (str, unicode)):
        if pytz:
            return pytz.timezone(tzname)
        else:
            #not pytz module imported, so just return None
            return None
    else:
        return tzname
    
def pick_timezone(*args):
    """
    >>> pick_timezone(None, 'Asia/Shanghai', None)
    <DstTzInfo 'Asia/Shanghai' LMT+8:06:00 STD>
    """
    for x in args:
        tz = timezone(x)
        if tz:
            return tz
    
def now(tzinfo=None):
    tz = pick_timezone(tzinfo, __local_timezone__, __timezone__)
    return datetime.datetime.now(tz)

def today(tzinfo=None):
    d = now(tzinfo)
    return to_date(d, tzinfo)

def to_timezone(dt, tzinfo=None):
    """
    Convert a datetime to timezone
    """
    tz = pick_timezone(tzinfo, __timezone__)
    if not tz:
        return dt
    dttz = getattr(dt, 'tzinfo', None)
    if not dttz:
        return tz.localize(dt)
    else:
        return dt.astimezone(tz)
    
def to_date(dt, tzinfo=None):
    """
    Convert a datetime to date with tzinfo
    """
    d = to_timezone(dt, tzinfo)
    return datetime.date(d.year, d.month, d.day)

def to_time(dt, tzinfo=None):
    """
    Convert a datetime to time with tzinfo
    """
    d = to_timezone(dt, tzinfo)
    return datetime.time(d.hour, d.minute, d.second, d.microsecond, tzinfo=d.tzinfo)

def to_datetime(dt, tzinfo=None, format=None):
    """
    Convert a date or time to datetime with tzinfo
    """
    if isinstance(dt, (str, unicode)):
        if not format:
            formats = DEFAULT_DATETIME_INPUT_FORMATS
        else:
            formats = list(format)
        d = None
        for fmt in formats:
            try:
                d = datetime.datetime(*time.strptime(dt, fmt)[:6])
            except ValueError:
                continue
        if not d:
            return None
    else:
        d = datetime.datetime(getattr(dt, 'year', 1970), getattr(dt, 'month', 1),
            getattr(dt, 'day', 1), getattr(dt, 'hour', 0), getattr(dt, 'minute', 0),
            getattr(dt, 'second', 0), getattr(dt, 'microsecond', 0))
        if getattr(dt, 'tzinfo', None):
            d = dt.tzinfo.localize(d)
    return to_timezone(d, tzinfo)

def __test():
    """
    >>> d = datetime.datetime(2009, 1, 2, 3, 4, 5)
    >>> tzname = 'Asia/Shanghai'
    >>> timezone(tzname)
    <DstTzInfo 'Asia/Shanghai' LMT+8:06:00 STD>
    >>> t = to_timezone(d, tzname)
    >>> t
    datetime.datetime(2009, 1, 2, 3, 4, 5, tzinfo=<DstTzInfo 'Asia/Shanghai' CST+8:00:00 STD>)
    >>> x = to_timezone(t, 'UTC')
    >>> x
    datetime.datetime(2009, 1, 1, 19, 4, 5, tzinfo=<UTC>)
    >>> to_date(t, tzname)
    datetime.date(2009, 1, 2)
    >>> to_date(t, 'UTC')
    datetime.date(2009, 1, 1)
    >>> to_time(t, tzname)
    datetime.time(3, 4, 5, tzinfo=<DstTzInfo 'Asia/Shanghai' CST+8:00:00 STD>)
    >>> to_time(t, 'UTC')
    datetime.time(19, 4, 5, tzinfo=<UTC>)
    >>> p = to_datetime(x)
    >>> p
    datetime.datetime(2009, 1, 1, 19, 4, 5, tzinfo=<UTC>)
    >>> to_datetime(x, tzname)
    datetime.datetime(2009, 1, 2, 3, 4, 5, tzinfo=<DstTzInfo 'Asia/Shanghai' CST+8:00:00 STD>)
    >>> to_datetime('2009-1-2 3:4:5', tzname)
    datetime.datetime(2009, 1, 2, 3, 4, 5, tzinfo=<DstTzInfo 'Asia/Shanghai' CST+8:00:00 STD>)
    """
    
#if __name__ == '__main__':
#    d = datetime.datetime(2009, 1, 2, 3, 4, 5)
#    tzname = 'Asia/Shanghai'
#    t = to_timezone(d, tzname)
#    print '1', repr(t), t.tzinfo
#    print '2', repr(t.astimezone(pytz.utc))
#    print '3', repr(to_timezone(t, tzname))
#    print '4', repr(t.astimezone(pytz.utc))