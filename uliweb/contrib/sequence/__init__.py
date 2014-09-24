from uliweb import functions
from time import sleep

def get_sequence(key, default=1, step=1, retry_times=None, retry_waittime=None):
    from uliweb.orm import SaveError
    from uliweb import settings
    
    assert step > 0 and default > 0

    Sequence = functions.get_model('sequence')
    i = 0
    waittime = retry_waittime or settings.get_var('SEQUENCE/retry_waittime', 0.05)
    retry_times = retry_times or settings.get_var('SEQUENCE/retry_times', 3)
    while 1:
        try:
            row = Sequence.get(Sequence.c.key==key)
            if row:
                row.value = row.value + step
                row.save(version=True)
            else:
                row = Sequence(key=key, value=(default+step-1))
                row.save()
            break
        except SaveError:
            i += 1
            if i == retry_times:
                raise
            else:
                sleep(waittime)

    return row.value

def set_sequence(key, value):
    assert value > 0

    Sequence = functions.get_model('sequence')
    row = Sequence.get(Sequence.c.key==key)
    if row:
        row.value = value
        row.save(version=True)
    else:
        row = Sequence(key=key, value=value)
        row.save()
    return row
    
