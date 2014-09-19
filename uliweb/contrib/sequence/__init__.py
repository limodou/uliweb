from uliweb import functions

def get_sequence(key, default=1, step=1):
    from uliweb.orm import SaveError
    
    assert step > 0 and default > 0

    Sequence = functions.get_model('sequence')
    row = Sequence.get(Sequence.c.key==key)
    if row:
        row.value = row.value + step
        i = 0
        while i<3:
            try:
                row.save(version=True)
                break
            except SaveError:
                i += 1
                if i == 3:
                    raise
    else:
        row = Sequence(key=key, value=(default+step-1))
        row.save()
    return row.value

def set_sequence(key, value):
    from uliweb.orm import SaveError
    
    assert value > 0

    Sequence = functions.get_model('sequence')
    row = Sequence.get(Sequence.c.key==key)
    if row:
        row.value = value
        i = 0
        while i<3:
            try:
                row.save(version=True)
                break
            except SaveError:
                i += 1
    else:
        row = Sequence(key=key, value=value)
        row.save()
    return row
    
