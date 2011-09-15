from uliweb.utils import date
from datetime import datetime

def test():
    """
    >>> date.get_timezones().keys()
    ['GMT -12', 'GMT -11', 'GMT -10', 'GMT -9', 'GMT -8', 'GMT -7', 'GMT -6', 'GMT -5', 'GMT -4', 'GMT -3', 'GMT -2', 'GMT -1', 'GMT +1', 'GMT +2', 'GMT +3', 'GMT +4', 'GMT +5', 'GMT +6', 'GMT +7', 'GMT +8', 'GMT +9', 'GMT +10', 'GMT +11', 'GMT +12', 'UTC']
    >>> date.timezone('GMT +8') # doctest:+ELLIPSIS
    <tzinfo GMT +8>
    >>> GMT8 = date.timezone('GMT +8')
    >>> d = datetime(2011, 9, 13, 20, 14, 15, tzinfo=GMT8)
    >>> date.to_timezone(d, date.UTC).isoformat() 
    '2011-09-13T12:14:15+00:00'
    >>> date.to_datetime('2011-9-13 20:14:15', tzinfo=date.UTC)
    datetime.datetime(2011, 9, 13, 20, 14, 15, tzinfo=<tzinfo UTC>)
    >>> d = date.to_datetime('2011-9-13 20:14:15', tzinfo=GMT8)
    >>> d
    datetime.datetime(2011, 9, 13, 20, 14, 15, tzinfo=<tzinfo GMT +8>)
    >>> c = datetime(2011, 9, 13, 20, 14, 15)
    >>> date.to_datetime(c, tzinfo=GMT8)
    datetime.datetime(2011, 9, 13, 20, 14, 15, tzinfo=<tzinfo GMT +8>)
    >>> date.to_datetime(d, tzinfo=date.UTC)
    datetime.datetime(2011, 9, 13, 12, 14, 15, tzinfo=<tzinfo UTC>)
    >>> date.set_timezone(date.UTC)
    >>> date.to_datetime(d)
    datetime.datetime(2011, 9, 13, 12, 14, 15, tzinfo=<tzinfo UTC>)
    >>> date.to_date('2011-9-13 20:14:15')
    datetime.date(2011, 9, 13)
    >>> date.to_datetime('2011-9-13 20:14:15')
    datetime.datetime(2011, 9, 13, 20, 14, 15, tzinfo=<tzinfo UTC>)
    >>> date.to_date('2011-9-13 20:14:15', tzinfo=date.UTC)
    datetime.date(2011, 9, 13)
    >>> date.to_time('2011-9-13 20:14:15')
    datetime.time(20, 14, 15, tzinfo=<tzinfo UTC>)
    >>> date.to_time('2011-9-13 20:14:15', tzinfo=date.UTC)
    datetime.time(20, 14, 15, tzinfo=<tzinfo UTC>)
    >>> date.to_string(date.to_date('2011-9-13 20:14:15'))
    '2011-09-13'
    >>> date.to_string(date.to_datetime('2011-9-13 20:14:15'))
    '2011-09-13 20:14:15 UTC'
    >>> date.to_string(date.to_time('2011-9-13 20:14:15'))
    '20:14:15'
    >>> date.to_timezone(None)
    >>> date.to_datetime(None)
    >>> date.to_date(None)
    >>> date.to_time(None)
    >>> date.set_local_timezone('GMT +8')
    >>> date.to_local(d)
    datetime.datetime(2011, 9, 13, 20, 14, 15, tzinfo=<tzinfo GMT +8>)
    >>> date.fix_gmt_timezone('GMT8')
    'GMT +8'
    >>> date.fix_gmt_timezone('GMT-8')
    'GMT -8'
    >>> date.fix_gmt_timezone('GMT+8')
    'GMT +8'
    >>> date.fix_gmt_timezone('gmt -8')
    'GMT -8'
    >>> date.fix_gmt_timezone('gmt -0')
    'UTC'
    >>> date.fix_gmt_timezone('asia/shanghai')
    'asia/shanghai'
    >>> date.timezone('gmt8')
    <tzinfo GMT +8>
    """