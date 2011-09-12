import datetime
import uliweb.utils.date as date
from uliweb.i18n import ungettext, ugettext

def timesince(d, now=None, pos=True, flag=False):
    """
    pos means calculate which direction, pos = True, now - d, pos = False, d - now
    flag means return value type, True will return since, message and Flase return message
    >>> d = datetime.datetime(2009, 10, 1, 12, 23, 19)
    >>> now = datetime.datetime(2009, 10, 1, 12, 24, 19)
    >>> timesince(d, now, True)
    u'1 minute ago'
    >>> now = datetime.datetime(2009, 10, 1, 12, 24, 30)
    >>> timesince(d, now, True)
    u'1 minute ago'
    >>> now = datetime.datetime(2009, 9, 28, 12, 24, 30)
    >>> timesince(d, now, True)
    u'2 days, 23 hours later'
    >>> now = datetime.datetime(2009, 10, 3, 12, 24, 30)
    >>> timesince(d, now, True)
    u'2 days ago'
    """
    if not d:
        if flag:
            return 0, ''
        else:
            return ''
    chunks = (
      (60 * 60 * 24 * 365, lambda n: ungettext('year', 'years', n)),
      (60 * 60 * 24 * 30, lambda n: ungettext('month', 'months', n)),
      (60 * 60 * 24 * 7, lambda n : ungettext('week', 'weeks', n)),
      (60 * 60 * 24, lambda n : ungettext('day', 'days', n)),
      (60 * 60, lambda n: ungettext('hour', 'hours', n)),
      (60, lambda n: ungettext('minute', 'minutes', n))
    )

    if not now:
        now = date.now()
    else:
        now = date.to_datetime(now)
    d = date.to_datetime(d)
    
    delta = now - (d - datetime.timedelta(0, 0, d.microsecond))
    oldsince = since = delta.days * 24 * 60 * 60 + delta.seconds
    
    suffix = ''
    if pos:
        if since > 0:
            suffix = ugettext(' ago')
        elif since < 0:
            suffix = ugettext(' later')
            since *= -1
    
    for i, (seconds, name) in enumerate(chunks):
        count = since // seconds
        if count != 0:
            break
    s = ('%(number)d %(type)s') % {'number': count, 'type': name(count)}
    if i + 1 < len(chunks):
        # Now get the second item
        seconds2, name2 = chunks[i + 1]
        count2 = (since - (seconds * count)) // seconds2
        if count2 != 0:
            s += (', %(number)d %(type)s') % {'number': count2, 'type': name2(count2)}
    #if flag==True, then return twe elements (since, message) 
    if flag:
        return oldsince, s + suffix
    else:
        return s + suffix
    