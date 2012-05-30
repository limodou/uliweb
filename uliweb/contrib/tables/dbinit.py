from uliweb.orm import get_model, __models__

Tables = get_model('tables')
for tablename, v in __models__.iteritems():
    table = get_model(tablename)
    if hasattr(table, '__verbose_name__'):
        verbose_name = getattr(table, '__verbose_name__')
    else:
        verbose_name = tablename
       
    obj = Tables.get(Tables.c.tablename == tablename)
    if obj:
        obj.verbose_name = verbose_name
    else:
        obj = Tables(tablename=tablename, verbose_name=verbose_name)
    obj.save()
    print 'Process %s...[%s]' % (tablename, verbose_name)