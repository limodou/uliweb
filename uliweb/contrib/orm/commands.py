import os, sys
import re
import datetime
from decimal import Decimal
from uliweb.core.commands import Command, get_answer, CommandManager
from optparse import make_option
from uliweb.utils.common import log, is_pyfile_exist
from sqlalchemy.types import *
from sqlalchemy import MetaData, Table
from sqlalchemy.engine.reflection import Inspector
from uliweb.orm import get_connection, set_auto_set_model, do_
import inspect
from time import time

def get_engine(options, global_options):
    from uliweb.manage import make_simple_application
    settings = {'ORM/DEBUG_LOG':False, 'ORM/AUTO_CREATE':False, 'ORM/AUTO_DOTRANSACTION':False}
    app = make_simple_application(apps_dir=global_options.apps_dir, 
        settings_file=global_options.settings, 
        local_settings_file=global_options.local_settings,
        default_settings=settings)
    #because set_auto_set_model will be invoked in orm initicalization, so
    #below setting will be executed after Dispatcher started
    #set_auto_set_model(True)
    engine_name = options.engine
    engine = get_connection(engine_name=engine_name)
    engine.engine_name = engine_name
    if global_options.verbose:
        print_engine(engine)
        
    return engine

def print_engine(engine):
    url = re.sub(r'(?<=//)(.*?):.*@', r'\1:***@', str(engine.url))
    print 'Connection [Engine:%s]:%s' % (engine.engine_name, url)
    print
    
def reflect_table(engine, tablename):
    meta = MetaData()
    table = Table(tablename, meta)
    insp = Inspector.from_engine(engine)
    insp.reflecttable(table, None)
    return table

def get_tables(apps_dir, apps=None, engine_name=None, tables=None,
    settings_file='settings.ini', local_settings_file='local_settings.ini'):
    from uliweb.core.SimpleFrame import get_apps, get_app_dir
    from uliweb import orm
    from StringIO import StringIO
    
    engine = orm.engine_manager[engine_name]
    e = engine.options['connection_string']
    
    old_models = orm.__models__.keys()
    tables_map = {}
    try:
        for tablename, m in engine.models.items():
            try:
                x = orm.get_model(tablename, engine_name)
            except:
                print "Error on Model [%s]" % tablename
                raise
            tables_map[x.tablename] = tablename
    except:
        print "Problems to models like:", list(set(old_models) ^ set(orm.__models__.keys()))
        raise
    
    if apps:
        t = {}
        for tablename, m in engine.metadata.tables.items():
            if hasattr(m, '__appname__') and m.__appname__ in apps:
                table = engine.metadata.tables[tablename]
                table.__appname__ = m.__appname__
                t[tables_map.get(tablename, tablename)] = table
    elif tables:
        t = {}
        for tablename in tables:
            if tablename in engine.metadata.tables:
                table = engine.metadata.tables[tablename]
                table.__appname__ = engine.metadata.tables[tablename].__appname__
                t[tables_map.get(tablename, tablename)] = table
            else:
                print "Table [%s] can't be found, it'll be skipped." % tablename
    else:
        t = {}
        for tablename, m in engine.metadata.tables.items():
            table = engine.metadata.tables[tablename]
            table.__appname__ = m.__appname__
            t[tables_map.get(tablename, tablename)] = table
     
    return t

def get_sorted_tables(tables):
    def _cmp(x, y):
        return cmp(x[1].__appname__, y[1].__appname__)
    
    return sorted(tables.items(), cmp=_cmp)
    
def dump_table(table, filename, con, std=None, delimiter=',', format=None, 
    encoding='utf-8', inspector=None, engine_name=None):
    from uliweb.utils.common import str_value
    from StringIO import StringIO
    import csv
    
    b = time()
    if not std:
        if isinstance(filename, (str, unicode)):
            std = open(filename, 'w')
        else:
            std = filename
    else:
        std = sys.stdout
    #add inspector table columns process, will not use model fields but database fields
    if inspector:
        meta = MetaData()
        table = Table(table.name, meta)
        inspector.reflecttable(table, None)
        
    result = do_(table.select(), engine_name)
    fields = [x.name for x in table.c]
    if not format:
        print >>std, ' '.join(fields)
    elif format == 'txt':
        print >>std, ','.join(fields)
    n = 0
    if format == 'txt':
        fw = csv.writer(std, delimiter=delimiter)
    for r in result:
        n += 1
        if not format:
            print >>std, r
        elif format == 'txt':
            fw.writerow([str_value(x, encoding=encoding, newline_escape=True) for x in r])
        else:
            raise Exception, "Can't support the text format %s" % format
  
    return 'OK (%d/%lfs)' % (n, time()-b)

def load_table(table, filename, con, delimiter=',', format=None, 
    encoding='utf-8', delete=True, bulk=100, engine_name=None):
    import csv
    from uliweb.utils.date import to_date, to_datetime
    
    if not os.path.exists(filename):
        return "Skipped (data not found)"

    table = reflect_table(con, table.name)
    
    if delete:
        do_(table.delete(), engine_name)
    
    b = time()
    bulk = max(1, bulk)
    f = fin = open(filename, 'rb')
    try:
        first_line = f.readline()
        if first_line.startswith('#'):
            first_line = first_line[1:]
        fields = first_line.strip().split()
        n = 0
        count = 0
        if format:
            fin = csv.reader(f, delimiter=delimiter)
            
        buf = []
        for line in fin:
            try:
                n += 1
                count += 1
                if not format:
                    line = eval(line.strip())
                record = dict(zip(fields, line))
                params = {}
                for c in table.c:
                    if c.name in record:
                        if not format:
                            params[c.name] = record[c.name]
                        else:
                            if record[c.name] == 'NULL':
                                params[c.name] = None
                            else:
                                if isinstance(c.type, String):
                                    params[c.name] = unicode(record[c.name], encoding)
                                elif isinstance(c.type, Date):
                                    params[c.name] = to_date(to_datetime(record[c.name]))
                                elif isinstance(c.type, DateTime):
                                    params[c.name] = to_datetime(record[c.name])
                                else:
                                    params[c.name] = record[c.name]
                buf.append(params)
                if count >= bulk:
                    do_(table.insert(), engine_name, args=buf)
                    count = 0
                    buf = []
            except:
                log.error('Error: Line %d' % n)
                raise
        
        if buf:
            do_(table.insert(), engine_name, args=buf)
            
        return 'OK (%d/%lfs)' % (n, time()-b)
    finally:
        f.close()
  
def show_table(name, table, i, total):
    """
    Display table info,
    name is tablename
    table is table object
    i is current Index
    total is total of tables
    """
    return '[%d/%d, %s] %s' % (i+1, total, table.__appname__, name)

class SQLCommandMixin(object):
    option_list = [
        make_option('--engine', dest='engine', default='default',
            help='Select database engine.'),
    ]
    has_options = True

class SyncdbCommand(SQLCommandMixin, Command):
    name = 'syncdb'
    help = 'Sync models with database. But all models should be defined in settings.ini.'
    
    def handle(self, options, global_options, *args):
        engine = get_engine(options, global_options)
        
        tables = get_sorted_tables(get_tables(global_options.apps_dir, 
            engine_name=options.engine, settings_file=global_options.settings, 
            local_settings_file=global_options.local_settings))
        _len = len(tables)
        for i, (name, t) in enumerate(tables):
            exist = engine.dialect.has_table(engine.connect(), t.name)
            created = False
            if t.__mapping_only__:
                msg = 'SKIPPED(Mapping Table)'
            else:
                if not exist:
                    t.create(engine)
                    created = True
                    msg = 'CREATED'
                else:
                    msg = 'EXISTED'
            if created or global_options.verbose:
                print '[%s] Creating %s...%s' % (options.engine, show_table(name, t, i, _len), msg)

class ResetCommand(SQLCommandMixin, Command):
    name = 'reset'
    args = '<appname, appname, ...>'
    help = 'Reset the apps models(drop and recreate). If no apps, then reset the whole database.'
    check_apps = True
    
    def handle(self, options, global_options, *args):

        if args:
            message = """This command will drop all tables of app [%s], are you sure to reset""" % ','.join(args)
        else:
            message = """This command will drop whole database, are you sure to reset"""
        get_answer(message)
        
        engine = get_engine(options, global_options)
        
        tables = get_sorted_tables(get_tables(global_options.apps_dir, args, 
            engine_name=options.engine, settings_file=global_options.settings, 
            local_settings_file=global_options.local_settings))
        _len = len(tables)
        for i, (name, t) in enumerate(tables):
            if t.__mapping_only__:
                msg = 'SKIPPED(Mapping Table)'
            else:
                t.drop(engine, checkfirst=True)
                t.create(engine)
                msg = 'SUCCESS'
            if global_options.verbose:
                print '[%s] Resetting %s...%s' % (options.engine, show_table(name, t, i, _len), msg)

class ResetTableCommand(SQLCommandMixin, Command):
    name = 'resettable'
    args = '<tablename, tablename, ...>'
    help = 'Reset the tables(drop and recreate). If no tables, then will do nothing.'
    
    def handle(self, options, global_options, *args):

        if not args:
            print "Failed! You should pass one or more tables name."
            sys.exit(1)

        message = """This command will drop all tables [%s], are you sure to reset""" % ','.join(args)
        get_answer(message)
        
        engine = get_engine(options, global_options)
        
        tables = get_sorted_tables(get_tables(global_options.apps_dir, 
            tables=args, engine_name=options.engine, 
            settings_file=global_options.settings, 
            local_settings_file=global_options.local_settings))
        _len = len(tables)
        for i, (name, t) in enumerate(tables):
            if t.__mapping_only__:
                msg = 'SKIPPED(Mapping Table)'
            else:
                t.drop(engine, checkfirst=True)
                t.create(engine)
                msg = 'SUCCESS'
            if global_options.verbose:
                print '[%s] Resetting %s...%s' % (options.engine, show_table(name, t, i, _len), msg)

class DropTableCommand(SQLCommandMixin, Command):
    name = 'droptable'
    args = '<tablename, tablename, ...>'
    help = 'Drop the tables. If no tables, then will do nothing.'
    
    def handle(self, options, global_options, *args):

        if not args:
            print "Failed! You should pass one or more tables name."
            sys.exit(1)

        message = """This command will drop all tables [%s], are you sure to drop""" % ','.join(args)
        get_answer(message)
        
        engine = get_engine(options, global_options)
        
        tables = get_sorted_tables(get_tables(global_options.apps_dir, 
            tables=args, engine_name=options.engine, 
            settings_file=global_options.settings, 
            local_settings_file=global_options.local_settings))
        _len = len(tables)
        for i, (name, t) in enumerate(tables):
            if t.__mapping_only__:
                msg = 'SKIPPED(Mapping Table)'
            else:
                t.drop(engine, checkfirst=True)
                msg = 'SUCCESS'
            if global_options.verbose:
                print '[%s] Dropping %s...%s' % (options.engine, show_table(name, t, i, _len), msg)

class SQLCommand(SQLCommandMixin, Command):
    name = 'sql'
    args = '<appname, appname, ...>'
    help = 'Display the table creation sql statement. If no apps, then process the whole database.'
    check_apps = True
    
    def handle(self, options, global_options, *args):
        from sqlalchemy.schema import CreateTable, CreateIndex
        
        engine = get_engine(options, global_options)
        
        tables = get_sorted_tables(get_tables(global_options.apps_dir, args, 
            engine_name=options.engine, settings_file=global_options.settings, 
            local_settings_file=global_options.local_settings))
        for name, t in tables:
            if t.__mapping_only__:
                continue
            
            print "%s;" % str(CreateTable(t).compile(dialect=engine.dialect)).rstrip()
            for x in t.indexes:
                print "%s;" % CreateIndex(x)
            
class SQLTableCommand(SQLCommandMixin, Command):
    name = 'sqltable'
    args = '<tablename, tablename, ...>'
    help = 'Display the table creation sql statement.'
    
    def handle(self, options, global_options, *args):
        from sqlalchemy.schema import CreateTable, CreateIndex
        
        engine = get_engine(options, global_options)
        
        tables = get_sorted_tables(get_tables(global_options.apps_dir, 
            tables=args, engine_name=options.engine, 
            settings_file=global_options.settings, 
            local_settings_file=global_options.local_settings))
        for name, t in tables:
            if t.__mapping_only__:
                continue
            print "%s;" % str(CreateTable(t).compile(dialect=engine.dialect)).rstrip()
            for x in t.indexes:
                print "%s;" % CreateIndex(x)

class DumpCommand(SQLCommandMixin, Command):
    name = 'dump'
    args = '<appname, appname, ...>'
    help = 'Dump all models records according all available tables. If no tables, then process the whole database.'
    option_list = (
        make_option('-o', dest='output_dir', default='./data',
            help='Output the data files to this directory.'),
        make_option('-t', '--text', dest='text', action='store_true', default=False,
            help='Dump files in text format.'),
        make_option('--delimiter', dest='delimiter', default=',',
            help='delimiter character used in text file. Default is ",".'),
        make_option('--encoding', dest='encoding', default='utf-8',
            help='Character encoding used in text file. Default is "utf-8".'),
        make_option('-z', dest='zipfile', 
            help='Compress table files into a zip file.'),
    )
    has_options = True
    check_apps = True
    
    def handle(self, options, global_options, *args):
        from zipfile import ZipFile, ZIP_DEFLATED
        from StringIO import StringIO

        output_dir = os.path.join(options.output_dir, options.engine)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        engine = get_engine(options, global_options)
        
        zipfile = None
        if options.zipfile:
            zipfile = ZipFile(options.zipfile, 'w', compression=ZIP_DEFLATED)
            
        inspector = Inspector.from_engine(engine)

        tables = get_sorted_tables(get_tables(global_options.apps_dir, args, 
            engine_name=options.engine, 
            settings_file=global_options.settings, 
            local_settings_file=global_options.local_settings))
        _len = len(tables)
        for i, (name, t) in enumerate(tables):
            if global_options.verbose:
                print 'Dumpping %s...' % show_table(name, t, i, _len),
            filename = os.path.join(output_dir, name+'.txt')
            if options.text:
                format = 'txt'
            else:
                format = None
            #process zipfile
            if options.zipfile:
                fileobj = StringIO()
                filename = os.path.basename(filename)
            else:
                fileobj = filename
            t = dump_table(t, fileobj, engine, delimiter=options.delimiter, 
                format=format, encoding=options.encoding, inspector=inspector,
                engine_name=engine.engine_name)
            #write zip content
            if options.zipfile and zipfile:
                zipfile.writestr(filename, fileobj.getvalue())
            if global_options.verbose:
                print t
            
        if zipfile:
            zipfile.close()
            
class DumpTableCommand(SQLCommandMixin, Command):
    name = 'dumptable'
    args = '<tablename, tablename, ...>'
    help = 'Dump all tables records according all available apps. If no apps, then will do nothing.'
    option_list = (
        make_option('-o', dest='output_dir', default='./data',
            help='Output the data files to this directory.'),
        make_option('-t', '--text', dest='text', action='store_true', default=False,
            help='Dump files in text format.'),
        make_option('--delimiter', dest='delimiter', default=',',
            help='delimiter character used in text file. Default is ",".'),
        make_option('--encoding', dest='encoding', default='utf-8',
            help='Character encoding used in text file. Default is "utf-8".'),
        make_option('-z', dest='zipfile', 
            help='Compress table files into a zip file.'),
   )
    has_options = True
    
    def handle(self, options, global_options, *args):
        from zipfile import ZipFile, ZIP_DEFLATED
        from StringIO import StringIO
        
        output_dir = os.path.join(options.output_dir, options.engine)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        engine = get_engine(options, global_options)

        if not args:
            print "Failed! You should pass one or more tables name."
            sys.exit(1)
            
        zipfile = None
        if options.zipfile:
            zipfile = ZipFile(options.zipfile, 'w', compression=ZIP_DEFLATED)

        inspector = Inspector.from_engine(engine)
        
        tables = get_sorted_tables(get_tables(global_options.apps_dir, tables=args,
            engine_name=options.engine, settings_file=global_options.settings, 
            local_settings_file=global_options.local_settings))
        _len = len(tables)

        for i, (name, t) in enumerate(tables):
            if global_options.verbose:
                print '[%s] Dumpping %s...' % (options.engine, show_table(name, t, i, _len)),
            filename = os.path.join(output_dir, name+'.txt')
            if options.text:
                format = 'txt'
            else:
                format = None
            #process zipfile
            if options.zipfile:
                fileobj = StringIO()
                filename = os.path.basename(filename)
            else:
                fileobj = filename
                
            t = dump_table(t, fileobj, engine, delimiter=options.delimiter, 
                format=format, encoding=options.encoding, inspector=inspector,
                engine_name=engine.engine_name)

            #write zip content
            if options.zipfile and zipfile:
                zipfile.writestr(filename, fileobj.getvalue())
            if global_options.verbose:
                print t
            
        if zipfile:
            zipfile.close()
            
class DumpTableFileCommand(SQLCommandMixin, Command):
    name = 'dumptablefile'
    args = 'tablename text_filename'
    help = 'Dump the table records to a text file. '
    option_list = (
        make_option('-t', '--text', dest='text', action='store_true', default=False,
            help='Dump files in text format.'),
        make_option('--delimiter', dest='delimiter', default=',',
            help='delimiter character used in text file. Default is ",".'),
        make_option('--encoding', dest='encoding', default='utf-8',
            help='Character encoding used in text file. Default is "utf-8".'),
    )
    has_options = True
    
    def handle(self, options, global_options, *args):
        
        engine = get_engine(options, global_options)

        if len(args) != 2:
            print self.print_help(self.prog_name, 'dumptablefile')
            sys.exit(1)
            
        inspector = Inspector.from_engine(engine)

        name = args[0]
        tables = get_tables(global_options.apps_dir, tables=[name],
            engine_name=options.engine, settings_file=global_options.settings, 
            local_settings_file=global_options.local_settings)
        t = tables[name]
        if global_options.verbose:
            print '[%s] Dumpping %s...' % (options.engine, show_table(name, t, 0, 1)),
        if options.text:
            format = 'txt'
        else:
            format = None
        t = dump_table(t, args[1], engine, delimiter=options.delimiter, 
            format=format, encoding=options.encoding, inspector=inspector,
            engine_name=engine.engine_name)
        if global_options.verbose:
            print t
        
class LoadCommand(SQLCommandMixin, Command):
    name = 'load'
    args = '<appname, appname, ...>'
    help = 'Load all models records according all available apps. If no apps, then process the whole database.'
    option_list = (
        make_option('-d', dest='dir', default='./data',
            help='Directory of data files.'),
        make_option('-b', dest='bulk', default='100',
            help='Bulk number of insert.'),
        make_option('-t', '--text', dest='text', action='store_true', default=False,
            help='Load files in text format.'),
        make_option('--delimiter', dest='delimiter', default=',',
            help='delimiter character used in text file. Default is ",".'),
        make_option('--encoding', dest='encoding', default='utf-8',
            help='Character encoding used in text file. Default is "utf-8".'),
    )
    has_options = True
    check_apps = True
    
    def handle(self, options, global_options, *args):
        from uliweb import orm
        
        if args:
            message = """This command will delete all data of [%s]-[%s] before loading, 
are you sure to load data""" % (options.engine, ','.join(args))
        else:
            message = """This command will delete whole database [%s] before loading, 
are you sure to load data""" % options.engine

        get_answer(message)

        path = os.path.join(options.dir, options.engine)
        if not os.path.exists(path):
            os.makedirs(path)
        
        engine = get_engine(options, global_options)

        tables = get_sorted_tables(get_tables(global_options.apps_dir, args, 
            engine_name=options.engine, 
            settings_file=global_options.settings, 
            local_settings_file=global_options.local_settings))
        _len = len(tables)
        for i, (name, t) in enumerate(tables):
            if t.__mapping_only__:
                if global_options.verbose:
                    msg = 'SKIPPED(Mapping Table)'
                    print '[%s] Loading %s...%s' % (options.engine, show_table(name, t, i, _len), msg)
                continue
            if global_options.verbose:
                print '[%s] Loading %s...' % (options.engine, show_table(name, t, i, _len)),
            try:
                orm.Begin()
                filename = os.path.join(path, name+'.txt')
                if options.text:
                    format = 'txt'
                else:
                    format = None
                t = load_table(t, filename, engine, delimiter=options.delimiter, 
                    format=format, encoding=options.encoding, bulk=int(options.bulk),
                    engine_name=engine.engine_name)
                orm.Commit()
                if global_options.verbose:
                    print t
                
            except:
                log.exception("There are something wrong when loading table [%s]" % name)
                orm.Rollback()

class LoadTableCommand(SQLCommandMixin, Command):
    name = 'loadtable'
    args = '<tablename, tablename, ...>'
    help = 'Load all tables records according all available tables. If no tables, then will do nothing.'
    option_list = (
        make_option('-d', dest='dir', default='./data',
            help='Directory of data files.'),
        make_option('-b', dest='bulk', default='100',
            help='Bulk number of insert.'),
        make_option('-t', '--text', dest='text', action='store_true', default=False,
            help='Load files in text format.'),
        make_option('--delimiter', dest='delimiter', default=',',
            help='delimiter character used in text file. Default is ",".'),
        make_option('--encoding', dest='encoding', default='utf-8',
            help='Character encoding used in text file. Default is "utf-8".'),
    )
    has_options = True
    
    def handle(self, options, global_options, *args):
        from uliweb import orm
        
        if args:
            message = """This command will delete all data of [%s]-[%s] before loading, 
are you sure to load data""" % (options.engine, ','.join(args))
        else:
            print "Failed! You should pass one or more tables name."
            sys.exit(1)

        ans = get_answer(message, answers='Yn', quit='q')

        path = os.path.join(options.dir, options.engine)
        if not os.path.exists(path):
            os.makedirs(path)
        
        engine = get_engine(options, global_options)

        tables = get_sorted_tables(get_tables(global_options.apps_dir, 
            engine_name=options.engine, 
            settings_file=global_options.settings, tables=args,
            local_settings_file=global_options.local_settings))
        _len = len(tables)
        
        for i, (name, t) in enumerate(tables):
            if t.__mapping_only__:
                if global_options.verbose:
                    msg = 'SKIPPED(Mapping Table)'
                    print '[%s] Loading %s...%s' % (options.engine, show_table(name, t, i, _len), msg)
                continue
            if global_options.verbose:
                print '[%s] Loading %s...' % (options.engine, show_table(name, t, i, _len)),
            try:
                orm.Begin()
                filename = os.path.join(path, name+'.txt')
                if options.text:
                    format = 'txt'
                else:
                    format = None
                t = load_table(t, filename, engine, delimiter=options.delimiter, 
                    format=format, encoding=options.encoding, delete=ans=='Y', 
                    bulk=int(options.bulk), engine_name=engine.engine_name)
                orm.Commit()
                if global_options.verbose:
                    print t
            except:
                log.exception("There are something wrong when loading table [%s]" % name)
                orm.Rollback()

class LoadTableFileCommand(SQLCommandMixin, Command):
    name = 'loadtablefile'
    args = 'tablename text_filename'
    help = 'Load table data from text file. If no tables, then will do nothing.'
    option_list = (
        make_option('-b', dest='bulk', default='100',
            help='Bulk number of insert.'),
        make_option('-t', '--text', dest='text', action='store_true', default=False,
            help='Load files in text format.'),
        make_option('--delimiter', dest='delimiter', default=',',
            help='delimiter character used in text file. Default is ",".'),
        make_option('--encoding', dest='encoding', default='utf-8',
            help='Character encoding used in text file. Default is "utf-8".'),
    )
    has_options = True
    
    def handle(self, options, global_options, *args):
        from uliweb import orm
        
        if len(args) != 2:
            print self.print_help(self.prog_name, 'loadtablefile')
            sys.exit(1)
            
        if args:
            message = """Do you want to delete all data of [%s]-[%s] before loading, if you choose N, the data will not be deleted""" % (options.engine, args[0])
        else:
            print "Failed! You should pass one or more tables name."
            sys.exit(1)

        ans = get_answer(message, answers='Yn', quit='q')

        engine = get_engine(options, global_options)

        name = args[0]
        tables = get_tables(global_options.apps_dir, engine_name=options.engine, 
            settings_file=global_options.settings, tables=[name],
            local_settings_file=global_options.local_settings)
        t = tables[name]
        if t.__mapping_only__:
            if global_options.verbose:
                msg = 'SKIPPED(Mapping Table)'
                print '[%s] Loading %s...%s' % (options.engine, show_table(name, t, i, _len), msg)
            return
        
        if global_options.verbose:
            print '[%s] Loading %s...' % (options.engine, show_table(name, t, 0, 1)), 
        try:
            orm.Begin()
            if options.text:
                format = 'txt'
            else:
                format = None
            t = load_table(t, args[1], engine, delimiter=options.delimiter, 
                format=format, encoding=options.encoding, delete=ans=='Y', 
                bulk=int(options.bulk), engine_name=engine.engine_name)
            orm.Commit()
            if global_options.verbose:
                print t
        except:
            log.exception("There are something wrong when loading table [%s]" % name)
            orm.Rollback()

class DbinitCommand(SQLCommandMixin, Command):
    name = 'dbinit'
    args = '<appname, appname, ...>'
    help = "Initialize database, it'll run the code in dbinit.py of each app. If no apps, then process the whole database."
    check_apps = True

    def handle(self, options, global_options, *args):
        from uliweb.core.SimpleFrame import get_app_dir
        from uliweb import orm

        engine = get_engine(options, global_options)

        if not args:
            apps_list = self.get_apps(global_options)
        else:
            apps_list = args
        
        for p in apps_list:
            if not is_pyfile_exist(get_app_dir(p), 'dbinit'):
                continue
            m = '%s.dbinit' % p
            try:
                if global_options.verbose:
                    print "[%s] Processing %s..." % (options.engine, m)
                orm.Begin()
                mod = __import__(m, fromlist=['*'])
                orm.Commit()
            except ImportError:
                orm.Rollback()
                log.exception("There are something wrong when importing module [%s]" % m)

class SqldotCommand(SQLCommandMixin, Command):
    name = 'sqldot'
    args = '<appname, appname, ...>'
    help = "Create graphviz dot file. If no apps, then process the whole database."
    check_apps = True
    
    def handle(self, options, global_options, *args):
        from graph import generate_dot

        engine = get_engine(options, global_options)

        if args:
            apps = args
        else:
            apps = self.get_apps(global_options)
        
        tables = get_tables(global_options.apps_dir, apps, engine_name=options.engine, 
            settings_file=global_options.settings, 
            local_settings_file=global_options.local_settings)
        print generate_dot(tables, apps)
        
class SqlHtmlCommand(SQLCommandMixin, Command):
    name = 'sqlhtml'
    args = '<appname, appname, ...>'
    help = "Create database documentation in HTML format. If no apps, then process the whole database."
    check_apps = True
    
    def handle(self, options, global_options, *args):
        from gendoc import generate_html
    
        engine = get_engine(options, global_options)
        
        if args:
            apps = args
        else:
            apps = self.get_apps(global_options)
        
        tables = get_tables(global_options.apps_dir, args, engine_name=options.engine, 
            settings_file=global_options.settings, 
            local_settings_file=global_options.local_settings)
        print generate_html(tables, apps)
    
class ValidatedbCommand(SQLCommandMixin, Command):
    name = 'validatedb'
    args = '<appname, appname, ...>'
    help = "Validate database or apps, check if the table structure is matched with source code."
    option_list = (
        make_option('-t', dest='traceback', action='store_true', default=False,
            help='Print traceback when validating failed.'),
    )
    check_apps = True
    has_options = True
    
    def handle(self, options, global_options, *args):
        
        engine = get_engine(options, global_options)

        if args:
            apps = args
        else:
            apps = self.get_apps(global_options)
        
        tables = get_sorted_tables(get_tables(global_options.apps_dir, apps, 
            engine_name=options.engine, 
            settings_file=global_options.settings, 
            local_settings_file=global_options.local_settings))
        _len = len(tables)
        
        for i, (name, t) in enumerate(tables):
            exist = engine.dialect.has_table(engine.connect(), t.name)
            if not exist:
                flag = 'NOT EXISTED'
            else:
                try:
                    result = list(do_(t.select().limit(1), engine.engine_name))
                    flag = 'OK'
                except Exception as e:
                    if options.traceback:
                        import traceback
                        traceback.print_exc()
                    flag = 'FAILED'
                
            if global_options.verbose or flag!='OK':
                print 'Validating [%s] %s...%s' % (options.engine, show_table(name, t, i, _len), flag)

def get_commands(mod):
    import types
    
    commands = {}
    
    def check(c):
        return (inspect.isclass(c) and 
            issubclass(c, Command) and c is not Command and not issubclass(c, CommandManager))
    
    for name in dir(mod):
        c = getattr(mod, name)
        if check(c):
            commands[c.name] = c
        
    return commands

class AlembicCommand(SQLCommandMixin, CommandManager):
    name = 'alembic'
    args = 'alembic_commands'
    check_apps_dirs = True

    def get_commands(self, global_options):
        import subcommands
        cmds = get_commands(subcommands)
        return cmds
    
