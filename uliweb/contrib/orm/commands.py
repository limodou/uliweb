import os, sys
import datetime
from decimal import Decimal
from uliweb.core.commands import Command, get_answer
from optparse import make_option
from uliweb.utils.common import log, is_pyfile_exist
from sqlalchemy.types import *

def get_engine(apps_dir):
    from uliweb.core.SimpleFrame import Dispatcher
    settings = {'ORM/DEBUG_LOG':False, 'ORM/AUTO_CREATE':True}
    app = Dispatcher(apps_dir=apps_dir, start=False, default_settings=settings)
    engine = app.settings.ORM.CONNECTION
    return engine

def get_tables(apps_dir, apps=None, engine=None, import_models=False, settings_file='settings.ini', local_settings_file='local_settings.ini'):
    from uliweb.core.SimpleFrame import get_apps, get_app_dir
    from uliweb import orm
    from sqlalchemy import create_engine
    from StringIO import StringIO
    
    if not engine:
        engine = get_engine(apps_dir)
    
    _engine = engine[:engine.find('://')+3]
    
    buf = StringIO()
    
    con = create_engine(_engine, strategy='mock', executor=lambda s, p='': buf.write(str(s) + p))
    db = orm.get_connection(con)
    
    if import_models:
        apps = get_apps(apps_dir, settings_file=settings_file, local_settings_file=local_settings_file)
        if apps:
            apps_list = apps
        else:
            apps_list = apps[:]
        models = []
        for p in apps_list:
            if p not in apps:
                log.error('Error: Appname %s is not a valid app' % p)
                continue
            if not is_pyfile_exist(get_app_dir(p), 'models'):
                continue
            m = '%s.models' % p
            try:
                mod = __import__(m, {}, {}, [''])
                models.append(mod)
            except ImportError:
                log.exception("There are something wrong when importing module [%s]" % m)
        
    else:
        old_models = orm.__models__.keys()
        try:
            for tablename, m in orm.__models__.items():
                orm.get_model(tablename)
        except:
            print "Problems to models like:", list(set(old_models) ^ set(orm.__models__.keys()))
            raise
            
    if apps:
        tables = {}
        for tablename, m in db.metadata.tables.iteritems():
            if hasattr(m, '__appname__') and m.__appname__ in apps:
                tables[tablename] = db.metadata.tables[tablename]
    else:
        tables = db.metadata.tables
                
    return tables

def dump_table(table, filename, con, std=None, delimiter=',', format=None, encoding='utf-8'):
    from uliweb.utils.common import str_value
    from StringIO import StringIO
    import csv
    
    if not std:
        if isinstance(filename, (str, unicode)):
            std = open(filename, 'w')
        else:
            std = filename
    else:
        std = sys.stdout
    result = con.execute(table.select())
    fields = []
    for c in table.c:
        fields.append(c.name)
    if not format:
        print >>std, '#', ' '.join(fields)
    elif format == 'txt':
        print >>std, '#', ','.join(fields)
    for r in result:
        if not format:
            print >>std, r
        elif format == 'txt':
            buf = StringIO()
            fw = csv.writer(buf, delimiter=delimiter)
            fw.writerow([str_value(x, encoding=encoding) for x in r])
            print >>std, buf.getvalue().rstrip()
        else:
            raise Exception, "Can't support the text format %s" % format
  
def load_table(table, filename, con, delimiter=',', format=None, encoding='utf-8', delete=True):
    import csv
    from uliweb.utils.date import to_date, to_datetime
    
    if delete:
        con.execute(table.delete())
    
    if not os.path.exists(filename):
        log.info("The table [%s] data is not existed." % table.name)
        return 
    
    f = fin = open(filename, 'rb')
    try:
        first_line = f.readline()
        fields = first_line[1:].strip().split()
        n = 1
        if format:
            fin = csv.reader(f, delimiter=delimiter)
            
        for line in fin:
            try:
                n += 1
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
                ins = table.insert().values(**params)
                con.execute(ins)
            except:
                log.error('Error: Line %d' % n)
                raise
    finally:
        f.close()

class SyncdbCommand(Command):
    name = 'syncdb'
    help = 'Sync models with database. But all models should be defined in settings.ini.'
    
    def handle(self, options, global_options, *args):
        from sqlalchemy import create_engine

        engine = get_engine(global_options.apps_dir)
        con = create_engine(engine)
        
        for name, t in get_tables(global_options.apps_dir, settings_file=global_options.settings, local_settings_file=global_options.local_settings).items():
            if global_options.verbose:
                print 'Creating %s...' % name

class ResetCommand(Command):
    name = 'reset'
    args = '<appname, appname, ...>'
    help = 'Reset the apps models(drop and recreate). If no apps, then reset the whole database.'
    check_apps = True
    
    def handle(self, options, global_options, *args):
        from sqlalchemy import create_engine

        if args:
            message = """This command will drop all tables of app [%s], are you sure to reset""" % ','.join(args)
        else:
            message = """This command will drop whole database, are you sure to reset"""
        get_answer(message)
        
        engine = get_engine(global_options.apps_dir)
        con = create_engine(engine)
        
        for name, t in get_tables(global_options.apps_dir, args, settings_file=global_options.settings, local_settings_file=global_options.local_settings).items():
            if global_options.verbose:
                print 'Resetting %s...' % name
            t.drop(con)
            t.create(con)

class ResetTableCommand(Command):
    name = 'resettable'
    args = '<tablename, tablename, ...>'
    help = 'Reset the tables(drop and recreate). If no tables, then will do nothing.'
    
    def handle(self, options, global_options, *args):
        from sqlalchemy import create_engine
        from uliweb import orm

        if not args:
            print "Failed! You should pass one or more tables name."
            sys.exit(1)

        message = """This command will drop all tables [%s], are you sure to reset""" % ','.join(args)
        get_answer(message)
        
        engine = get_engine(global_options.apps_dir)
        con = create_engine(engine)
        
        for name in args:
            m = orm.get_model(name)
            if not m:
                print "Error! Can't find the table %s...Skipped!" % name
                continue
            t = m.table
            if global_options.verbose:
                print 'Resetting %s...' % name
            t.drop(con)
            t.create(con)

class DropTableCommand(Command):
    name = 'droptable'
    args = '<tablename, tablename, ...>'
    help = 'Drop the tables. If no tables, then will do nothing.'
    
    def handle(self, options, global_options, *args):
        from sqlalchemy import create_engine
        from uliweb import orm

        if not args:
            print "Failed! You should pass one or more tables name."
            sys.exit(1)

        message = """This command will drop all tables [%s], are you sure to drop""" % ','.join(args)
        get_answer(message)
        
        engine = get_engine(global_options.apps_dir)
        con = create_engine(engine)
        
        for name in args:
            m = orm.get_model(name)
            if not m:
                print "Error! Can't find the table %s...Skipped!" % name
                continue
            t = m.table
            if global_options.verbose:
                print 'Dropping %s...' % name
            t.drop(con)

class SQLCommand(Command):
    name = 'sql'
    args = '<appname, appname, ...>'
    help = 'Display the table creation sql statement. If no apps, then process the whole database.'
    check_apps = True
    
    def handle(self, options, global_options, *args):
        from sqlalchemy.schema import CreateTable
        
        for name, t in sorted(get_tables(global_options.apps_dir, args, settings_file=global_options.settings, local_settings_file=global_options.local_settings).items()):
            _t = CreateTable(t)
            print _t
            
class DumpCommand(Command):
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
        from sqlalchemy import create_engine
        from zipfile import ZipFile
        from StringIO import StringIO

        if not os.path.exists(options.output_dir):
            os.makedirs(options.output_dir)
        
        engine = get_engine(global_options.apps_dir)
        con = create_engine(engine)
        
        zipfile = None
        if options.zipfile:
            zipfile = ZipFile(options.zipfile, 'w')

        for name, t in get_tables(global_options.apps_dir, args, engine=engine, settings_file=global_options.settings, local_settings_file=global_options.local_settings).items():
            if global_options.verbose:
                print 'Dumpping %s...' % name
            filename = os.path.join(options.output_dir, name+'.txt')
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
            dump_table(t, fileobj, con, delimiter=options.delimiter, 
                format=format, encoding=options.encoding)
            #write zip content
            if options.zipfile and zipfile:
                zipfile.writestr(filename, fileobj.getvalue())
        if zipfile:
            zipfile.close()
            
class DumpTableCommand(Command):
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
   )
    has_options = True
    
    def handle(self, options, global_options, *args):
        from sqlalchemy import create_engine
        from uliweb import orm
        
        if not os.path.exists(options.output_dir):
            os.makedirs(options.output_dir)
        
        engine = get_engine(global_options.apps_dir)
        con = create_engine(engine)

        if not args:
            print "Failed! You should pass one or more tables name."
            sys.exit(1)
            
        tables = get_tables(global_options.apps_dir, args, engine=engine, settings_file=global_options.settings, local_settings_file=global_options.local_settings)
        for name in args:
            if name in tables:
                t = tables[name]
                if global_options.verbose:
                    print 'Dumpping %s...' % name
                filename = os.path.join(options.output_dir, name+'.txt')
                if options.text:
                    format = 'txt'
                else:
                    format = None
                dump_table(t, filename, con, delimiter=options.delimiter, 
                    format=format, encoding=options.encoding)

class DumpTableFileCommand(Command):
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
        from sqlalchemy import create_engine
        from uliweb import orm
        
        engine = get_engine(global_options.apps_dir)
        con = create_engine(engine)

        if len(args) != 2:
            print self.print_help(self.prog_name, 'dumptablefile')
            sys.exit(1)
            
        name = args[0]
        tables = get_tables(global_options.apps_dir, engine=engine, settings_file=global_options.settings, local_settings_file=global_options.local_settings)
        t = tables[name]
        if global_options.verbose:
            print 'Dumpping %s...' % name
        if options.text:
            format = 'txt'
        else:
            format = None
        dump_table(t, args[1], con, delimiter=options.delimiter, 
            format=format, encoding=options.encoding)

class LoadCommand(Command):
    name = 'load'
    args = '<appname, appname, ...>'
    help = 'Load all models records according all available apps. If no apps, then process the whole database.'
    option_list = (
        make_option('-d', dest='dir', default='./data',
            help='Directory of data files.'),
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
            message = """This command will delete all data of [%s] before loading, 
are you sure to load data""" % ','.join(args)
        else:
            message = """This command will delete whole database before loading, 
are you sure to load data"""

        get_answer(message)

        if not os.path.exists(options.dir):
            os.makedirs(options.dir)
        
        engine = get_engine(global_options.apps_dir)
        con = orm.get_connection(engine)

        for name, t in get_tables(global_options.apps_dir, args, engine=engine, settings_file=global_options.settings, local_settings_file=global_options.local_settings).items():
            if global_options.verbose:
                print 'Loading %s...' % name
            try:
                con.begin()
                filename = os.path.join(options.dir, name+'.txt')
                if options.text:
                    format = 'txt'
                else:
                    format = None
                load_table(t, filename, con, delimiter=options.delimiter, 
                    format=format, encoding=options.encoding)
                con.commit()
            except:
                log.exception("There are something wrong when loading table [%s]" % name)
                con.rollback()

class LoadTableCommand(Command):
    name = 'loadtable'
    args = '<tablename, tablename, ...>'
    help = 'Load all tables records according all available tables. If no tables, then will do nothing.'
    option_list = (
        make_option('-d', dest='dir', default='./data',
            help='Directory of data files.'),
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
            message = """This command will delete all data of [%s] before loading, 
are you sure to load data""" % ','.join(args)
        else:
            print "Failed! You should pass one or more tables name."
            sys.exit(1)

        get_answer(message)

        if not os.path.exists(options.dir):
            os.makedirs(options.dir)
        
        engine = get_engine(global_options.apps_dir)
        con = orm.get_connection(engine)

        tables = get_tables(global_options.apps_dir, args, engine=engine, settings_file=global_options.settings, local_settings_file=global_options.local_settings)
        for name in args:
            if name in tables:
                t = tables[name]
                if global_options.verbose:
                    print 'Loading %s...' % name
                try:
                    con.begin()
                    filename = os.path.join(options.dir, name+'.txt')
                    if options.text:
                        format = 'txt'
                    else:
                        format = None
                    load_table(t, filename, con, delimiter=options.delimiter, 
                        format=format, encoding=options.encoding)
                    con.commit()
                except:
                    log.exception("There are something wrong when loading table [%s]" % name)
                    con.rollback()

class LoadTableFileCommand(Command):
    name = 'loadtablefile'
    args = 'tablename text_filename'
    help = 'Load table data from text file. If no tables, then will do nothing.'
    option_list = (
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
            message = """Do you want to delete all data of [%s] before loading, if you choose N, the data will not be deleted""" % args[0]
        else:
            print "Failed! You should pass one or more tables name."
            sys.exit(1)

        ans = get_answer(message, answers='Yn', quit='q')

        engine = get_engine(global_options.apps_dir)
        con = orm.get_connection(engine)

        name = args[0]
        tables = get_tables(global_options.apps_dir, args, engine=engine, settings_file=global_options.settings, local_settings_file=global_options.local_settings)
        t = tables[name]
        if global_options.verbose:
            print 'Loading %s...' % name
        try:
            con.begin()
            if options.text:
                format = 'txt'
            else:
                format = None
            load_table(t, args[1], con, delimiter=options.delimiter, 
                format=format, encoding=options.encoding, delete=ans=='Y')
            con.commit()
        except:
            log.exception("There are something wrong when loading table [%s]" % name)
            con.rollback()

class DbinitCommand(Command):
    name = 'dbinit'
    args = '<appname, appname, ...>'
    help = "Initialize database, it'll run the code in dbinit.py of each app. If no apps, then process the whole database."
    check_apps = True

    def handle(self, options, global_options, *args):
        from uliweb.core.SimpleFrame import get_app_dir, Dispatcher
        from uliweb import orm

        app = Dispatcher(project_dir=global_options.project, start=False)

        if not args:
            apps_list = self.get_apps(global_options)
        else:
            apps_list = args
        
        con = orm.get_connection()
        
        for p in apps_list:
            if not is_pyfile_exist(get_app_dir(p), 'dbinit'):
                continue
            m = '%s.dbinit' % p
            try:
                if global_options.verbose:
                    print "Processing %s..." % m
                con.begin()
                mod = __import__(m, fromlist=['*'])
                con.commit()
            except ImportError:
                con.rollback()
                log.exception("There are something wrong when importing module [%s]" % m)

class SqldotCommand(Command):
    name = 'sqldot'
    args = '<appname, appname, ...>'
    help = "Create graphviz dot file. If no apps, then process the whole database."
    check_apps = True
    
    def handle(self, options, global_options, *args):
        from uliweb.core.SimpleFrame import Dispatcher
        from graph import generate_dot

        app = Dispatcher(project_dir=global_options.project, start=False)
        if args:
            apps = args
        else:
            apps = self.get_apps(global_options)
        
        engine = get_engine(global_options.apps_dir)
        
        tables = get_tables(global_options.apps_dir, None, engine=engine, settings_file=global_options.settings, local_settings_file=global_options.local_settings)
        print generate_dot(tables, apps)
        
class SqlHtmlCommand(Command):
    name = 'sqlhtml'
    args = '<appname, appname, ...>'
    help = "Create database documentation in HTML format. If no apps, then process the whole database."
    check_apps = True
    
    def handle(self, options, global_options, *args):
        from uliweb.core.SimpleFrame import Dispatcher
        from gendoc import generate_html
    
        app = Dispatcher(project_dir=global_options.project, start=False)
        if args:
            apps = args
        else:
            apps = self.get_apps(global_options)
        
        engine = get_engine(global_options.apps_dir)
        
        tables = get_tables(global_options.apps_dir, apps, engine=engine, settings_file=global_options.settings, local_settings_file=global_options.local_settings)
        print generate_html(tables, apps)
    
class ValidatedbCommand(Command):
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
        from uliweb.core.SimpleFrame import Dispatcher
        from gendoc import generate_html
        from sqlalchemy import create_engine
        
        app = Dispatcher(project_dir=global_options.project, start=False)
        if args:
            apps = args
        else:
            apps = self.get_apps(global_options)
        
        engine = get_engine(global_options.apps_dir)
        con = create_engine(engine)
        
        tables = get_tables(global_options.apps_dir, apps, engine=engine, settings_file=global_options.settings, local_settings_file=global_options.local_settings)
        
        for name, t in get_tables(global_options.apps_dir, args, engine=engine, settings_file=global_options.settings, local_settings_file=global_options.local_settings).items():
            try:
                result = list(con.execute(t.select().limit(1)))
                flag = 'ok'
            except Exception as e:
                if options.traceback:
                    import traceback
                    traceback.print_exc()
                flag = 'fail'
                
            if global_options.verbose or flag=='fail':
                print 'Validating %s...%s' % (name, flag)

class InitAlembicCommand(Command):
    name = 'init_alembic'
    help = 'init alembic environment to current project'
    args = ''
    check_apps_dirs = True

    def handle(self, options, global_options, *args):
        from uliweb.utils.common import extract_dirs, pkg
        from uliweb.core.template import template_file
        
        extract_dirs('uliweb.contrib.orm', 'templates/alembic', '.', verbose=global_options.verbose, replace=False)
        engine_string = get_engine(global_options.apps_dir)
        ini_file = os.path.join(pkg.resource_filename('uliweb.contrib.orm', 'templates/alembic/alembic.ini'))
        text = template_file(ini_file, {'CONNECTION':engine_string})
        with open(os.path.join(global_options.project, 'alembic.ini'), 'w') as f:
            f.write(text)
            