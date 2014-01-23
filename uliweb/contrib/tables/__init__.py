from uliweb import functions

def get_table(tablename):
    Tables = functions.get_model('tables')
    return Tables.get_table(tablename)