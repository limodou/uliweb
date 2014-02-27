from uliweb import functions

__tables__ = {}

def get_table(tablename):
    Tables = functions.get_model('tables')
    
    if tablename not in __tables__:
        table = Tables.get_table(tablename)
        __tables__[tablename] = table
        return table
    else:
        return __tables__[tablename]