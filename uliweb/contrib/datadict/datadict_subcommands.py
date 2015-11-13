import os
from uliweb.core.commands import Command, CommandManager, get_commands
from optparse import make_option

class CreateIndexCommand(Command):
    #change the name to real command name, such as makeapp, makeproject, etc.
    name = 'createindex'
    #command line parameters definition
    option_list = (
        make_option('-f', dest='ddfile', default='datadict.csv',
            help='Output datadict filename, default is datadict.csv.'),
        make_option('-r', dest='replace', default=False, action='store_true',
            help='Replace existed data dict file.'),
        make_option('--engine', dest='engine', default='default',
            help='Select database engine.'),
    )
    #help information
    help = 'Create or update datadict file which will be saved to datadict.csv'
    #args information, used to display show the command usage message
    args = 'appname, appname'
    #if True, it'll check the current directory should has apps directory
    check_apps_dirs = True
    #if True, it'll check args parameters should be valid apps name
    check_apps = True
    #if True, it'll skip not predefined parameters in options_list, otherwise it'll
    #complain not the right parameters of the command, it'll used in subcommands or
    #passing extra parameters to a special command
    skip_options = False
    options_inherit = True

    def handle(self, options, global_options, *args):
        import csv

        dd = {}

        app = self.get_application(global_options)
        if os.path.exists(options.ddfile):
            if not options.replace:
                dd = self._read(options.ddfile)
        with open(options.ddfile, 'w') as f:
            writer = csv.writer(f, delimiter=',', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(['name', 'fieldname', 'type', 'type_name'])
            for table, prop in self._get_columns(options, global_options, args):
                self._parse_prop(dd, prop)
            self._write(writer, dd)

    def _get_value(self, row):
        return row['fieldname'], row['type'], row['type_name']

    def _read(self, ddfile):
        """
        Import index just like:

            {'key':['value', 'value'], ...}
        """
        import csv

        d = {}
        with open(ddfile) as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = row['name']
                if key.startswith('#'):
                    key = key[1:]
                    deprecated = True
                else:
                    deprecated = False
                value = d.setdefault(key, {})
                value[self._get_value(row)] = deprecated
        return d

    def _write(self, writer, dd):
        for k, _v in sorted(dd.items(), key=lambda x:x[0].lower()):
            for row, deprecated in _v.items():
                if deprecated:
                    _key = ['#%s' % k]
                else:
                    _key = k
                row = [_key] + list(row)
                writer.writerow(row)

    def _parse_prop(self, dd, row):
        """
        :param dd: datadict
        :param _row: (tablename, row)
        :return:
        """
        key = row['name']
        if key.startswith('#'):
            deprecated = True
        else:
            deprecated = False
        v = dd.get(key)
        _value = self._get_value(row)
        if not v:
            v = dd.setdefault(key, {})
            v[_value] = deprecated
        else:
            if not _value in v:
                v[_value] = deprecated

    def _get_columns(self, options, global_options, args, tables=None):
        from uliweb import functions
        from uliweb.orm import ManyToMany, ModelNotFound
        from uliweb.contrib.orm.commands import get_tables, get_sorted_tables

        if not tables:
            if args:
                apps = args
            else:
                apps = self.get_apps(global_options)
        else:
            apps = None

        tables = get_sorted_tables(get_tables(global_options.apps_dir, apps, tables=tables,
            engine_name=options.engine,
            settings_file=global_options.settings,
            local_settings_file=global_options.local_settings))

        for tablename, table in tables:
            try:
                t = functions.get_model(tablename)
            except ModelNotFound:
                continue
            for name, f in t._fields_list:
                if not isinstance(f, ManyToMany):
                    yield tablename, f.to_column_info()


class CheckCommand(CreateIndexCommand):
    #change the name to real command name, such as makeapp, makeproject, etc.
    name = 'check'
    #command line parameters definition
    option_list = (
        make_option('-f', dest='ddfile', default='datadict.csv',
            help='Output datadict filename, default is datadict.csv.'),
        make_option('-t', '--table', dest='tables', action='append', default=[],
            help='Tables name which you want to check. This parameter can be multiple.'),
        make_option('--engine', dest='engine', default='default',
            help='Select database engine.'),
    )
    #help information
    help = 'Check apps or tables with data dict file.'
    #args information, used to display show the command usage message
    args = 'appname, appname'
    #if True, it'll check the current directory should has apps directory
    check_apps_dirs = True
    #if True, it'll check args parameters should be valid apps name
    check_apps = True
    #if True, it'll skip not predefined parameters in options_list, otherwise it'll
    #complain not the right parameters of the command, it'll used in subcommands or
    #passing extra parameters to a special command
    skip_options = False
    options_inherit = False

    def handle(self, options, global_options, *args):
        import csv

        dd = {}

        app = self.get_application(global_options)
        if os.path.exists(options.ddfile):
            dd = self._read(options.ddfile)
        for tablename, prop in self._get_columns(options, global_options, args, options.tables):
            self._check_prop(dd, tablename, prop)

    def _check_prop(self, dd, tablename, row):
        key = row['name']
        v = dd.get(key)
        if not v:
            print '[%s.%s] Not Existed' % (tablename, key)
        else:
            _key = self._get_value(row)
            deprecated = v.get(_key, None)
            if deprecated is None:
                print '[%s.%s] Not Found' % (tablename, key)
            else:
                if deprecated:
                    print '[%s.%s] Deprecated' % (tablename, key)
