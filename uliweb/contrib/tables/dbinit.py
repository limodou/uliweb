from uliweb.orm import get_model, __models__
import six

Tables = get_model('tables')
for tablename, v in six.iteritems(__models__):
    table = get_model(tablename)
    if hasattr(table, '__verbose_name__'):
        verbose_name = getattr(table, '__verbose_name__')
    else:
        verbose_name = tablename
       
    obj = Tables.get(Tables.c.table_name == tablename)
    if obj:
        obj.verbose_name = verbose_name
    else:
        obj = Tables(table_name=tablename, verbose_name=verbose_name)
    obj.save()
    six.print_('Process %s...[%s]' % (tablename, verbose_name))