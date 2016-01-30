#!/usr/bin/env python
import sys, os
import logging
import inspect
from optparse import make_option
import uliweb
from uliweb.core.commands import Command, CommandManager
from uliweb.core import SimpleFrame

apps_dir = 'apps'
__commands__ = {}

log = logging.getLogger('uliweb.console')

def get_commands(global_options):
    global __commands__
    
    def check(c):
        return (inspect.isclass(c) and 
            issubclass(c, Command) and c is not Command and c is not CommandManager)
    
    def find_mod_commands(mod):
        for name in dir(mod):
            c = getattr(mod, name)
            if check(c):
                register_command(c)
        
    def collect_commands():
        from uliweb import get_apps, get_app_dir
        from uliweb.utils.common import is_pyfile_exist
        
        apps = get_apps(global_options.apps_dir, settings_file=global_options.settings,
                local_settings_file=global_options.local_settings)
        for f in apps:
            path = get_app_dir(f)
            if is_pyfile_exist(path, 'commands'):
                m = '%s.commands' % f
                mod = __import__(m, fromlist=['*'])
            
                find_mod_commands(mod)

    collect_commands()
    return __commands__
    
def register_command(kclass):
    global __commands__
    __commands__[kclass.name] = kclass
    
workpath = os.path.join(os.path.dirname(__file__), 'lib')
if workpath not in sys.path:
    sys.path.insert(0, os.path.join(workpath, 'lib'))

def install_config(apps_dir):
    from uliweb.utils import pyini
    #user can configure custom PYTHONPATH, so that uliweb can add these paths
    #to sys.path, and user can manage third party or public apps in a separate
    #directory
    config_filename = os.path.join(apps_dir, 'config.ini')
    if os.path.exists(config_filename):
        c = pyini.Ini(config_filename)
        paths = c.GLOBAL.get('PYTHONPATH', [])
        if paths:
            for p in reversed(paths):
                p = os.path.abspath(os.path.normpath(p))
                if not p in sys.path:
                    sys.path.insert(0, p)
                    
def make_application(debug=None, apps_dir='apps', project_dir=None, 
    include_apps=None, debug_console=True, settings_file=None, 
    local_settings_file=None, start=True, default_settings=None, 
    dispatcher_cls=None, dispatcher_kwargs=None, debug_cls=None, debug_kwargs=None, 
    reuse=True, verbose=False, pythonpath=None):
    """
    Make an application object
    """
    from uliweb.utils.common import import_attr
    from werkzeug.debug import DebuggedApplication
    
    #is reuse, then create application only one
    if reuse and hasattr(SimpleFrame.__global__, 'application') and SimpleFrame.__global__.application:
        return SimpleFrame.__global__.application
    
    #process settings and local_settings
    settings_file = settings_file or os.environ.get('SETTINGS', 'settings.ini')
    local_settings_file = local_settings_file or os.environ.get('LOCAL_SETTINGS', 'local_settings.ini')
    
    dispatcher_cls = dispatcher_cls or SimpleFrame.Dispatcher
    dispatcher_kwargs = dispatcher_kwargs or {}
    
    if project_dir:
        apps_dir = os.path.abspath(os.path.normpath(os.path.join(project_dir, 'apps')))
    if not project_dir:
        project_dir = os.path.abspath(os.path.normpath(os.path.abspath(os.path.join(apps_dir, '..'))))
        
    if pythonpath:
        if isinstance(pythonpath, str):
            pythonpath = pythonpath.split(';')
        for x in pythonpath:
            if x not in sys.path:
                sys.path.insert(0, x)

    if project_dir not in sys.path:
        sys.path.insert(0, project_dir)

    if apps_dir not in sys.path:
        sys.path.insert(0, apps_dir)

    install_config(apps_dir)
    
    application = app = dispatcher_cls(apps_dir=apps_dir, 
        include_apps=include_apps, 
        settings_file=settings_file, 
        local_settings_file=local_settings_file, 
        start=start,
        default_settings=default_settings,
        reset=True,
        **dispatcher_kwargs)
    
    if verbose:
        log.info(' * settings file is "%s"' % settings_file)
        log.info(' * local settings file is "%s"' % local_settings_file)
    
    #settings global application object
    SimpleFrame.__global__.application = app
    
    #process wsgi middlewares
    middlewares = []
    parameters = {}
    for name, v in uliweb.settings.get('WSGI_MIDDLEWARES', {}).iteritems():
        order, kwargs = 500, {}
        if not v:
            continue
        if isinstance(v, (list, tuple)):
            if len(v) > 3:
                logging.error('WSGI_MIDDLEWARE %s difinition is not right' % name)
                raise uliweb.UliwebError('WSGI_MIDDLEWARE %s difinition is not right' % name)
            cls = v[0]
            if len(v) == 2:
                if isinstance(v[1], int):
                    order = v[1]
                else:
                    kwargs = v[1]
            else:
                order, kwargs = v[1], v[2]
        else:
            cls = v
        middlewares.append((order, name))
        parameters[name] = cls, kwargs
        
    middlewares.sort(cmp=lambda x, y: cmp(x[0], y[0]))
    for name in reversed([x[1] for x in middlewares]):
        clspath, kwargs = parameters[name]
        cls = import_attr(clspath)
        app = cls(app, **kwargs)
                
    debug_flag = uliweb.settings.GLOBAL.DEBUG
    if debug or (debug is None and debug_flag):
        if not debug_cls:
            debug_cls = DebuggedApplication
            
        log.setLevel(logging.DEBUG)
        log.info(' * Loading DebuggedApplication...')
        app.debug = True
        app = debug_cls(app, uliweb.settings.GLOBAL.get('DEBUG_CONSOLE', False))
    return app

def make_simple_application(apps_dir='apps', project_dir=None, include_apps=None, 
    settings_file='', local_settings_file='', 
    default_settings=None, dispatcher_cls=None, dispatcher_kwargs=None, reuse=True,
    pythonpath=None):
    settings = {'ORM/AUTO_DOTRANSACTION':False}
    settings.update(default_settings or {})
    return make_application(apps_dir=apps_dir, project_dir=project_dir,
        include_apps=include_apps, debug_console=False, debug=False,
        settings_file=settings_file, local_settings_file=local_settings_file,
        start=False, default_settings=settings, dispatcher_cls=dispatcher_cls, 
        dispatcher_kwargs=dispatcher_kwargs, reuse=reuse, pythonpath=pythonpath)

class MakeAppCommand(Command):
    name = 'makeapp'
    args = 'appname'
    help = 'Create a new app according the appname parameter.'
    check_apps_dirs = False
    
    def handle(self, options, global_options, *args):
        from uliweb.utils.common import extract_dirs

        if not args:
            appname = ''
            while not appname:
                appname = raw_input('Please enter app name:')
            apps = [appname]
        else:
            apps = args
        
        for appname in apps:
            ans = '-1'
            app_path = appname.replace('.', '//')
            if os.path.exists('apps'):
                path = os.path.join('apps', app_path)
            else:
                path = app_path
            
            if os.path.exists(path):
                if global_options.yes:
                    ans = 'y'
                while ans not in ('y', 'n'):
                    ans = raw_input('The app directory has been existed, do you want to overwrite it?(y/n)[n]')
                    if not ans:
                        ans = 'n'
            else:
                ans = 'y'
            if ans == 'y':
                extract_dirs('uliweb', 'template_files/app', path, verbose=global_options.verbose)
register_command(MakeAppCommand)

class MakePkgCommand(Command):
    name = 'makepkg'
    args = '<pkgname1, pkgname2, ...>'
    help = 'Create new python package folders.'
    check_apps_dirs = False

    def handle(self, options, global_options, *args):
        if not args:
            while not args:
                args = raw_input('Please enter python package name:')
            args = [args]
        
        for p in args:
            if not os.path.exists(p):
                os.makedirs(p)
            initfile = os.path.join(p, '__init__.py')
            if not os.path.exists(initfile):
                f = open(initfile, 'w')
                f.close()
register_command(MakePkgCommand)

class MakeProjectCommand(Command):
    name = 'makeproject'
    help = 'Create a new project directory according the project name'
    args = 'project_name'
    check_apps_dirs = False

    def handle(self, options, global_options, *args):
        from uliweb.utils.common import extract_dirs
        from uliweb.core.template import template_file
        
        if not args:
            project_name = ''
            while not project_name:
                project_name = raw_input('Please enter project name:')
        else:
            project_name = args[0]
        
        ans = '-1'
        if os.path.exists(project_name):
            if global_options.yes:
                ans = 'y'
            while ans not in ('y', 'n'):
                ans = raw_input('The project directory has been existed, do you want to overwrite it?(y/n)[n]')
                if not ans:
                    ans = 'n'
        else:
            ans = 'y'
        if ans == 'y':
            extract_dirs('uliweb', 'template_files/project', project_name, verbose=global_options.verbose)
            #template setup.py
            setup_file = os.path.join(project_name, 'setup.py.template')
            text = template_file(setup_file, {'project_name':project_name})
            setup_file_py = os.path.join(project_name, 'setup.py')
            with open(setup_file_py, 'w') as f:
                f.write(text)
            os.unlink(setup_file)
            #rename .gitignore.template to .gitignore
            os.rename(os.path.join(project_name, '.gitignore.template'), os.path.join(project_name, '.gitignore'))
register_command(MakeProjectCommand)

class MakeModuleCommand(Command):
    name = 'makemodule'
    help = 'Create a new uliweb module directory according the module name'
    args = 'module_name'
    check_apps_dirs = False

    def handle(self, options, global_options, *args):
        from uliweb.utils.common import extract_dirs
        from uliweb.core.template import template_file

        if not args:
            module_name = ''
            while not module_name:
                module_name = raw_input('Please enter module name:')
        else:
            module_name = args[0]

        if not module_name.startswith('uliweb-'):
            print 'Please use "uliweb-xxx" to name the module'
            return

        ans = '-1'
        if os.path.exists(module_name):
            if global_options.yes:
                ans = 'y'
            while ans not in ('y', 'n'):
                ans = raw_input('The module directory has been existed, do you want to overwrite it?(y/n)[n]')
                if not ans:
                    ans = 'n'
        else:
            ans = 'y'
        if ans == 'y':
            extract_dirs('uliweb', 'template_files/module', module_name,
                         verbose=global_options.verbose)
            #template setup.py
            setup_file = os.path.join(module_name, 'setup.py.template')
            text = template_file(setup_file, {'module_name':module_name})
            setup_file_py = os.path.join(module_name, 'setup.py')
            with open(setup_file_py, 'w') as f:
                f.write(text)
            os.unlink(setup_file)
            #rename .gitignore.template to .gitignore
            os.rename(os.path.join(module_name, '.gitignore.template'),
                      os.path.join(module_name, '.gitignore'))
            #rename module/module to module_name/module_name
            os.rename(os.path.join(module_name, 'module'),
                      os.path.join(module_name, module_name.replace('-', '_')))
register_command(MakeModuleCommand)

class SupportCommand(Command):
    name = 'support'
    help = 'Add special support to existed project, such as: tornado, gevent, gevent-socketio'
    args = 'supported_type'
    check_apps_dirs = True

    def handle(self, options, global_options, *args):
        from uliweb.utils.common import copy_dir
        from uliweb.utils.common import pkg
        
        _types = []
        support_dirs = {}
        app_dirs = [os.path.join(SimpleFrame.get_app_dir(appname), 'template_files/support') for appname in self.get_apps(global_options)]
        for path in [pkg.resource_filename('uliweb', 'template_files/support/')] + app_dirs:
            if os.path.exists(path):
                for f in os.listdir(path):
                    _path = os.path.join(path, f)
                    if os.path.isdir(_path) and not f.startswith('.'):
                        _name = f
                        _types.append(_name)
                        support_dirs[_name] = _path

        support_type = args[0] if args else ''
        while not support_type in _types and support_type != 'quit':
            print 'Supported types:\n'
            print '    ' + '\n    '.join(sorted(_types))
            print
            support_type = raw_input('Please enter support type[quit to exit]:')
        
        if support_type != 'quit':
            src_dir = support_dirs[support_type]
            copy_dir(src_dir, '.', verbose=global_options.verbose)
register_command(SupportCommand)

class ConfigCommand(Command):
    name = 'config'
    help = 'Output config info for different support, such as: nginx, uwsgi, etc.'
    args = 'supported_type'
    check_apps_dirs = True

    def handle(self, options, global_options, *args):
        from uliweb.utils.common import pkg
        from uliweb.utils.pyini import Ini
        from uliweb.core.commands import get_input
        from uliweb.core.template import template_file
        import glob
        
        _types = []
        config_files = {}
        app_dirs = [os.path.join(SimpleFrame.get_app_dir(appname), 'template_files/config') for appname in self.get_apps(global_options)]
        for path in [pkg.resource_filename('uliweb', 'template_files/config/')] + app_dirs:
            if os.path.exists(path):
                files = glob.glob(os.path.join(path, '*.conf'))
                if files:
                    for f in files:
                        _name = os.path.splitext(os.path.basename(f))[0]
                        _types.append(_name)
                        config_files[_name] = f
        
        support_type = args[0] if args else ''
        while not support_type in _types and support_type != 'quit':
            print 'Supported types:\n'
            print '    ' + '\n    '.join(sorted(_types))
            print
            support_type = raw_input('Please enter support type[quit to exit]:')
        
        if support_type != 'quit':
            conf_file = config_files[support_type]
            conf_ini = conf_file[:-5] + '.ini'
            
            if not os.path.exists(conf_file):
                log.error("%s config can't be found" % support_type)
                sys.exit(1)
                
            data = {}
            data['project_dir'] = os.path.abspath(os.getcwd())
            data['project'] = os.path.basename(data['project_dir'])
            if os.path.exists(conf_ini):
                x = Ini(conf_ini)
                for k, v in x.INPUT.items():
                    if isinstance(v, (tuple, list)):
                        if len(v) == 2:
                            prompt, default = v
                        else:
                            prompt = v[0]
                            default = ''
                    else:
                        prompt, default = v or '', ''
                    if not prompt.strip():
                        prompt = 'Please input %s[%s]:' % (k, default)
                    r = get_input(prompt, default=default)
                    data[k] = r
                data.update(x.get('DEFAULT', {}))
                
            print
            print template_file(conf_file, data)
            
register_command(ConfigCommand)

class ExportStaticCommand(Command):
    """
    Compress js and css will follow the rule that: if the filename include 
    '.min.' or '.pack.',
    then don't process it.
    """
    name = 'exportstatic'
    help = 'Export all installed apps static directory to output directory.'
    args = 'output_directory [app1, app2, ...]'
    check_apps_dirs = True
    option_list = (
        make_option('-c', '--check', action='store_true', 
            help='Check if the output files or directories have conflicts.'),
        make_option('--js', action='store_true', dest='js', default=False,
            help='Enable javascript compress process.'),
        make_option('--css', action='store_true', dest='css', default=False,
            help='Enable css compress process.'),
        make_option('--auto', action='store_true', dest='auto', default=False,
            help='Enable javascript and css both compress process.'),
    )

    def handle(self, options, global_options, *args):
        from uliweb.utils.common import copy_dir_with_check
        from uliweb import settings
        
        self.get_application(global_options)
        
        if not args:
            print >>sys.stderr, "Error: outputdir should be a directory and existed"
            sys.exit(0)
        else:
            outputdir = os.path.abspath(args[0])
            if global_options.verbose:
                print "Export direcotry is %s ..." % outputdir
                
        if not args[1:]:
            apps = self.get_apps(global_options)
        else:
            apps = args[1:]
        dirs = [os.path.join(SimpleFrame.get_app_dir(appname), 'static') for appname in apps]
        self.options = options
        self.global_options = global_options
        copy_dir_with_check(dirs, outputdir, False, options.check, processor=self.process_file)
        
        self.process_combine(outputdir, global_options.verbose)
        
    def process_combine(self, outputdir, verbose=False):
        #automatically process static combine
        from uliweb.contrib.template import init_static_combine
        from rjsmin.rjsmin import jsmin
        from rcssmin.rcssmin import cssmin
        import glob

        #delete combined files
        for f in glob.glob(os.path.join(outputdir, '_cmb_*')):
            try:
                os.remove(f)
            except:
                print "Error: static file [%s] can't be deleted"
                
        d = init_static_combine()
        for k, v in d.items():
            filename = os.path.join(outputdir, k)
            if verbose:
                print 'Process ... %s' % filename
            readme = os.path.splitext(filename)[0] + '.txt'
            with open(filename, 'w') as f:
                ext = os.path.splitext(k)[1]
                if ext == '.js':
                    processor = jsmin
                elif ext == '.css':
                    processor = cssmin
                else:
                    print "Error: Unsupport type %s" % ext
                    sys.exit(1)
                for x in v:
                    fname = os.path.join(outputdir, x)
                    if verbose:
                        print '    add %s' % fname
                    kwargs = {}
                    if ext == '.css':
                        kwargs = {'base_dir':os.path.dirname(x)}
                    f.write(processor(open(fname).read(), **kwargs))
                    f.write('\n')
                 
            with open(readme, 'w') as r:
                for x in v:
                    r.write(x)
                    r.write('\n')
        
    def process_file(self, sfile, dpath, dfile):
        from rjsmin.rjsmin import jsmin
        from rcssmin.rcssmin import cssmin
        
        js_compressor = None
        css_compressor = None
        
        if sfile.endswith('.js') and ('.min.' not in sfile and '.pack.' not in sfile) and (self.options.js or self.options.auto):
            open(dfile, 'w').write(jsmin(open(sfile).read()))
            if self.global_options.verbose:
                print 'Compress %s to %s' % (sfile, dfile)
            return True
        if sfile.endswith('.css') and ('.min.' not in sfile and '.pack.' not in sfile) and (self.options.css or self.options.auto):
            open(dfile, 'w').write(cssmin(open(sfile).read()))
            if self.global_options.verbose:
                print 'Compress %s to %s' % (sfile, dfile)
            return True
register_command(ExportStaticCommand)


class ExportconfigjsCommand(Command):
    #change the name to real command name, such as makeapp, makeproject, etc.
    name = 'exportconfigjs'
    #command line parameters definition
    option_list = (
        make_option('-d', '--directory', dest='directory', default='.',
            help='Output config.js to this directory.'),
        make_option('-a', '--app', dest='app', default='',
            help='Output config.js to this appname/static.'),
    )
    #help information
    help = 'Export requirejs config.js. If no filename, it will be config.js'
    #args information, used to display show the command usage message
    args = '[filename]'
    #if True, it'll check the current directory should has apps directory
    check_apps_dirs = True
    #if True, it'll check args parameters should be valid apps name
    check_apps = False
    #if True, it'll skip not predefined parameters in options_list, otherwise it'll
    #complain not the right parameters of the command, it'll used in subcommands or
    #passing extra parameters to a special command
    skip_options = False
    #if inherit the base class option_list, default True is inherit
    options_inherit = True


    def handle(self, options, global_options, *args):
        self.get_application(global_options)

        from uliweb import application, get_app_dir

        if args:
            fname = args[0]
        else:
            fname = 'config.js'
        filename = application.get_file(fname, dir='template_files')
        path = []
        if options.app:
            path.append(os.path.join(get_app_dir(options.app), 'static'))
        path.append(options.directory)
        path.append(fname)
        o_filename = os.path.join(*path)
        dir = os.path.dirname(o_filename)
        if not os.path.exists(dir):
            os.makedirs(dir)

        ini = application.get_config('ui_modules.ini')
        with open(o_filename, 'w') as f:
            f.write(application.template(filename, {'modules':ini.UI_MODULES}))
        print 'Output config file to {}'.format(o_filename)
register_command(ExportconfigjsCommand)


class ExportCommand(Command):
    name = 'export'
    help = 'Export all installed apps or specified module source files to output directory.'
    args = '[module1 module2]'
    check_apps_dirs = True
    option_list = (
        make_option('-d', dest='outputdir',  
            help='Output directory of exported files.'),
    )

    def handle(self, options, global_options, *args):
        from uliweb.utils.common import extract_dirs
        
        if not options.outputdir:
            print >>sys.stderr, "Error: please give the output directory with '-d outputdir' argument"
            sys.exit(0)
        else:
            outputdir = options.outputdir
    
        if not args:
            apps = self.get_apps(global_options)
        else:
            apps = args
        if not os.path.exists(outputdir):
            os.makedirs(outputdir)
        for app in apps:
            dirs = app.split('.')
            mod = []
            dest = outputdir
            for m in dirs:
                mod.append(m)
                dest = os.path.join(dest, m)
                module = '.'.join(mod)
                if global_options.verbose:
                    print 'Export %s to %s ...' % (module, dest)
                if module == app:
                    recursion = True
                else:
                    recursion = False
                extract_dirs(module, '', dest, verbose=global_options.verbose, recursion=recursion)
                
register_command(ExportCommand)

#class ExtractUrlsCommand(Command):
#    name = 'extracturls'
#    help = 'Extract all url mappings from view modules to a specified file.'
#    args = ''
#    
#    def handle(self, options, global_options, *args):
#        urlfile = 'urls.py'
#        
#        application = SimpleFrame.Dispatcher(apps_dir=global_options.project, start=False)
#        filename = os.path.join(application.apps_dir, urlfile)
#        if os.path.exists(filename):
#            answer = raw_input("Error: [%s] is existed already, do you want to overwrite it[Y/n]:" % urlfile)
#            if answer.strip() and answer.strip.lower() != 'y':
#                return
#        f = file(filename, 'w')
#        print >>f, "from uliweb import simple_expose\n"
#        application.url_infos.sort()
#        for url, kw in application.url_infos:
#            endpoint = kw.pop('endpoint')
#            if kw:
#                s = ['%s=%r' % (k, v) for k, v in kw.items()]
#                t = ', %s' % ', '.join(s)
#            else:
#                t = ''
#            print >>f, "simple_expose(%r, %r%s)" % (url, endpoint, t)
#        f.close()
#        print 'urls.py has been created successfully.'
#register_command(ExtractUrlsCommand)
#        
class CallCommand(Command):
    name = 'call'
    help = 'Call <exefile>.py for each installed app according the command argument.'
    args = '[-a appname] exefile'
    option_list = (
        make_option('-a', dest='appname',
            help='Appname. If not provide, then will search exefile in whole project.'),
        make_option('--without-application', action='store_false', default=True, dest='application',
            help='If create application first, default is False.'),
        make_option('--gevent', action='store_true', default=False, dest='gevent',
            help='Apply gevent monkey patch before execute the script.'),
    )

    def handle(self, options, global_options, *args):
        from uliweb.utils.common import is_pyfile_exist
        from uliweb.core.SimpleFrame import get_app_dir
        
        if not args:
            print "Error: There is no command module name behind call command."
            return
        else:
            command = args[0]
        
        if options.gevent:
            from gevent import monkey
            
            monkey.patch_all()
            
        if options.application:
            self.get_application(global_options)
            
        if not options.appname:
            apps = self.get_apps(global_options)
        else:
            apps = [options.appname]
        exe_flag = False
        
        def get_module(command, apps):
            if '.' in command:
                yield 'mod', '', command
            else:
                for f in apps:
                    yield 'app', f, command
                
        for _type, app, m in get_module(command, apps):
            mod = None
            if _type == 'mod':
                mod_name = m
                if global_options.verbose:
                    print "Importing... %s" % mod_name
                mod = __import__(m, fromlist=['*'])
            else:
                path = get_app_dir(app)
                if is_pyfile_exist(path, m):
                    mod_name = app + '.' + m
                    if global_options.verbose:
                        print "Importing... %s" % mod_name
                    mod = __import__('%s.%s' % (app, m), fromlist=['*'])
            
            if mod:
                if hasattr(mod, 'call'):
                    getattr(mod, 'call')(args, options, global_options)
                elif hasattr(mod, 'main'):
                    getattr(mod, 'main')(args, options, global_options)
                else:
                    print "Can't find call() or main() function in module %s" % mod_name
                exe_flag = True
            
        if not exe_flag:
            print "Error: Can't import the [%s], please check the file and try again." % command
register_command(CallCommand)
 
class InstallCommand(Command):
    name = 'install'
    help = 'install [appname,...] extra modules listed in requirements.txt'
    args = '[appname]'
    
    def handle(self, options, global_options, *args):
        from uliweb.core.SimpleFrame import get_app_dir
        
        #check pip or setuptools
        try:
            import pip
        except:
            print "Error: can't import pip module, please install it first"
            sys.exit(1)
            
        apps = args or self.get_apps(global_options)
            
        def get_requirements():
            for app in apps:
                path = get_app_dir(app)
                r_file = os.path.join(path, 'requirements.txt')
                if os.path.exists(r_file):
                    yield r_file
            r_file = os.path.join(global_options.project, 'requirements.txt')
            if os.path.exists(r_file):
                yield r_file
                
        for r_file in get_requirements():
            if global_options.verbose:
                print "Processing... %s" % r_file
            os.system('pip install -r %s' % r_file)
            
register_command(InstallCommand)

class MakeCmdCommand(Command):
    name = 'makecmd'
    help = 'Created a commands.py to the apps or current directory.'
    args = 'appname'
    check_apps = False
    check_apps_dirs = False
    
    def handle(self, options, global_options, *args):
        from uliweb.core.commands import get_input, get_answer
        from uliweb.core.template import template_file
        from uliweb.utils.common import extract_dirs
        from uliweb import get_app_dir

        if not args:
            path = '.'
        else:
            path = get_app_dir(args[0])
        cmd_filename = os.path.join(path, 'commands.py')

        overwrite = True
        if os.path.exists(cmd_filename):
            overwrite = get_answer('The commands.py is already existed, '
                            'do you want to overwrite it',
                            quit='q',
                            default='n') == 'Y'

        if overwrite:
            command_file = open(cmd_filename, 'w')
        else:
            command_file = open(cmd_filename, 'a')
        try:
            if overwrite:
                command_file.write(self._render_tempfile('command_head.tmpl'))
            d = {}
            d['name'] = get_input('Command name:')
            d['has_subcommands'] = get_answer('Has subcommands', default='n') == 'Y'

            command_file.write(self._render_tempfile('command.tmpl', d))

            if d['has_subcommands']:
                subcommand_filename = os.path.join(path, d['name']+'_subcommands.py')
                if overwrite:
                    sub_file = open(subcommand_filename, 'w')
                else:
                    sub_file = open(subcommand_filename, 'a')
                try:
                    if overwrite:
                        sub_file.write(self._render_tempfile('command_head.tmpl'))
                    d = {'name':'demoSub', 'has_subcommands':False}
                    sub_file.write(self._render_tempfile('command.tmpl', d))
                finally:
                    sub_file.close()
        finally:
            command_file.close()

    def _get_tempfile(self, tmplname):
        from uliweb.utils.common import pkg

        return os.path.join(pkg.resource_filename('uliweb', 'template_files/command'), tmplname)

    def _render_tempfile(self, tmplname, vars=None):
        from uliweb.core.template import template_file

        tempfile = self._get_tempfile(tmplname)
        return template_file(tempfile, vars or {})

register_command(MakeCmdCommand)

class RunserverCommand(Command):
    name = 'runserver'
    help = 'Start a new development server. And it can also startup an app without a whole project.'
    args = '[appname appname ...]'
    option_list = (
        make_option('-h', dest='hostname', default='localhost',
            help='Hostname or IP.'),
        make_option('-p', dest='port', type='int', default=8000,
            help='Port number.'),
        make_option('--no-reload', dest='reload', action='store_false', default=True,
            help='If auto reload the development server. Default is True.'),
        make_option('--no-debug', dest='debug', action='store_false', default=True,
            help='If auto enable debug mode. Default is True.'),
        make_option('--nocolor', dest='color', action='store_false', default=True,
            help='Disable colored log info. Default is False.'),
        make_option('--thread', dest='thread', action='store_true', default=False,
            help='If use thread server mode. Default is False.'),
        make_option('--processes', dest='processes', type='int', default=1,
            help='The default number of processes to start.'),
        make_option('--ssl', dest='ssl', action='store_true',
            help='Using SSL to access http.'),
        make_option('--ssl-key', dest='ssl_key', default='ssl.key',
            help='The SSL private key filename.'),
        make_option('--ssl-cert', dest='ssl_cert', default='ssl.cert',
            help='The SSL certificate filename.'),
        make_option('--tornado', dest='tornado', action='store_true', default=False,
            help='Start uliweb server with tornado.'),
        make_option('--gevent', dest='gevent', action='store_true', default=False,
            help='Start uliweb server with gevent.'),
        make_option('--gevent-socketio', dest='gsocketio', action='store_true', default=False,
            help='Start uliweb server with gevent-socketio.'),
        make_option('--coverage', dest='coverage', action='store_true', default=False,
            help='Start uliweb server with coverage.'),
    )
    develop = False
    check_apps_dirs = False
    
    def handle(self, options, global_options, *args):
        import logging
        from logging import StreamHandler
        from uliweb.utils.coloredlog import ColoredFormatter
        from uliweb.utils.common import check_apps_dir
        import subprocess

        if self.develop:
            include_apps = ['plugs.develop']
        else:
            include_apps = []

        #add appname runable support, it'll automatically create a default project
        #if you want to startup an app, it'll use a temp directory, default is
        old_apps_dir = os.path.abspath(global_options.apps_dir)
        if args:
            include_apps.extend(args)
            project_home_dir = os.path.join(os.path.expanduser('~'), '.uliweb')
            if not os.path.exists(project_home_dir):
                os.makedirs(project_home_dir)

            subprocess.call('uliweb makeproject -y project', cwd=project_home_dir, shell=True)
            global_options.project = os.path.join(project_home_dir, 'project')
            global_options.apps_dir = os.path.join(global_options.project, 'apps')

        check_apps_dir(global_options.apps_dir)

        extra_files = collect_files(global_options, global_options.apps_dir, self.get_apps(global_options, include_apps))
        
        if options.color:
            def format(self, record):
                if not hasattr(self, 'new_formatter'):
                    if self.formatter:
                        fmt = ColoredFormatter(format=self.formatter._fmt, datefmt=self.formatter.datefmt, log_colors=uliweb.settings.get('LOG.COLORS', {}))
                    else:
                        fmt = ColoredFormatter()
                    self.new_formatter = fmt
                else:
                    fmt = self.new_formatter
                return fmt.format(record)
            setattr(StreamHandler, 'format', format)
            
        def get_app(debug_cls=None):
            return make_application(options.debug, project_dir=global_options.project,
                        include_apps=include_apps, settings_file=global_options.settings,
                        local_settings_file=global_options.local_settings, debug_cls=debug_cls,
                        verbose=global_options.verbose, pythonpath=old_apps_dir)

        cov = None
        try:
            if options.coverage:
                try:
                    from coverage import coverage
                except ImportError:
                    print "Error: Can't import coverage!"
                    return

                cov = coverage(source=['apps'])
                cov.start()
            if options.tornado:
                self.run_tornado(options, extra_files, get_app)
            elif options.gevent:
                self.run_gevent(options, extra_files, get_app)
            elif options.gsocketio:
                self.run_gevent_socketio(options, extra_files, get_app)
            else:
                self.run_simple(options, extra_files, get_app)
        finally:
            if cov:
                cov.stop()
                cov.html_report(directory='covhtml')

    def run_tornado(self, options, extra_files, get_app):
        try:
            import tornado.wsgi
            import tornado.httpserver
            import tornado.ioloop
            import tornado.autoreload
        except:
            print 'Error: Please install tornado first'
            return

        if options.ssl:
            ctx = {
                "certfile": options.ssl_cert,
                "keyfile": options.ssl_key,
            }
            log.info(' * Running on https://%s:%d/' % (options.hostname, options.port))
        else:
            ctx = None
            log.info(' * Running on http://%s:%d/' % (options.hostname, options.port))

        container = tornado.wsgi.WSGIContainer(get_app())
        http_server = tornado.httpserver.HTTPServer(container,
            ssl_options=ctx)
        http_server.listen(options.port, address=options.hostname)
        loop=tornado.ioloop.IOLoop.instance()
        if options.reload:
            for f in extra_files:
                tornado.autoreload.watch(f)
            tornado.autoreload.start(loop)
        loop.start()

    def run_gevent(self, options, extra_files, get_app):
        try:
            from gevent.wsgi import WSGIServer
            from gevent import monkey
        except:
            print 'Error: Please install gevent first'
            return
        from werkzeug.serving import run_with_reloader
        from functools import partial

        monkey.patch_all()

        run_with_reloader = partial(run_with_reloader, extra_files=extra_files)

        if options.ssl:
            ctx = {
                "certfile": options.ssl_cert,
                "keyfile": options.ssl_key,
            }
        else:
            ctx = {}
        @run_with_reloader
        def run_server():
            log.info(' * Running on http://%s:%d/' % (options.hostname, options.port))
            http_server = WSGIServer((options.hostname, options.port), get_app(), **ctx)
            http_server.serve_forever()

        run_server()

    def run_gevent_socketio(self, options, extra_files, get_app):
        try:
            from gevent import monkey
        except:
            print 'Error: Please install gevent first'
            return
        try:
            from socketio.server import SocketIOServer
        except:
            print 'Error: Please install gevent-socketio first'
            sys.exit(1)
        from werkzeug.serving import run_with_reloader
        from functools import partial

        monkey.patch_all()

        from werkzeug.debug import DebuggedApplication
        class MyDebuggedApplication(DebuggedApplication):
            def __call__(self, environ, start_response):
                # check if websocket call
                if "wsgi.websocket" in environ and not environ["wsgi.websocket"] is None:
                    # a websocket call, no debugger ;)
                    return self.application(environ, start_response)
                # else go on with debugger
                return DebuggedApplication.__call__(self, environ, start_response)

        if options.ssl:
            ctx = {
                "certfile": options.ssl_cert,
                "keyfile": options.ssl_key,
            }
        else:
            ctx = {}

        run_with_reloader = partial(run_with_reloader, extra_files=extra_files)

        @run_with_reloader
        def run_server():
            log.info(' * Running on http://%s:%d/' % (options.hostname, options.port))
            SocketIOServer((options.hostname, options.port), get_app(MyDebuggedApplication), resource="socket.io", **ctx).serve_forever()

        run_server()

    def run_simple(self, options, extra_files, get_app):
        from werkzeug.serving import run_simple

        if options.ssl:
            ctx = 'adhoc'

            default = False
            if not os.path.exists(options.ssl_key):
                log.info(' * SSL key file (%s) not found, will use default ssl config' % options.ssl_key)
                default = True
            if not os.path.exists(options.ssl_cert) and not default:
                log.info(' * SSL cert file (%s) not found, will use default ssl config' % options.ssl_cert)
                default = True

            if not default:
                ctx = (options.ssl_key, options.ssl_cert)
        else:
            ctx = None

            run_simple(options.hostname, options.port, get_app(), options.reload, False, True,
                extra_files, 1, options.thread, options.processes, ssl_context=ctx)

register_command(RunserverCommand)

class DevelopCommand(RunserverCommand):
    name = 'develop'
    develop = True
register_command(DevelopCommand)

class StaticizeCommand(RunserverCommand):
    """
    Staticize a site, limit:

    1. Only support Get method
    2. Json result shuld be exposed as @expose('xxx.json')
    3. Support redirect
    4. Support i18n
    5. Not support parameter of URL

    It not works like a spyder.
    """
    name = 'staticize'
    help = 'Statizice a site to static web pages.'
    args = '[options] output_directory'
    check_apps_dirs = True
    option_list = (
        make_option('-l', dest='lang', default='',
            help='Language of the site, default it no language specified.'),
        # make_option('-o', dest='outputfile', default='',
        #     help='Output staticize script.'),
    )

    def handle(self, options, global_options, *args):
        import uliweb.core.SimpleFrame
        from uliweb.core.SimpleFrame import get_app_dir, url_for as _old_url_for
        import uliweb.contrib.i18n.middle_i18n as i18n
        from urlparse import urlparse

        if not args:
            print "Please give output directory."
            sys.exit(1)

        path = dst_path = args[0]
        # if options.lang:
        #     path = os.path.join(dst_path, options.lang)
        # else:
        #     path = dst_path

        #redefine url_for
        def _u(endpoint, **values):
            url = _old_url_for(endpoint, **values)
            return self.fix_url(url)
        uliweb.core.SimpleFrame.url_for = _u

        #redefine get_language_from_request
        def _get_language_from_request(request, settings):
            return options.lang
        i18n.get_language_from_request = _get_language_from_request

        app = self.get_application(global_options,
                                   default_settings={'I18N/URL_LANG_KEY':'lang'})

        from uliweb.core.SimpleFrame import url_map
        from uliweb.utils.test import client_from_application
        from werkzeug import Response

        Response.autocorrect_location_header = False

        client = client_from_application(app)

        u = []
        for i, r in enumerate(sorted(url_map.iter_rules(), key=lambda x:x.rule)):
            #only execute GET method
            end_point = r.rule[1:] or 'index.html'
            p = os.path.join(path, end_point)
            p = self.fix_url(p)
            print 'GET %s to %s' % (r.rule, p)

            base_dir = os.path.dirname(p)
            if not os.path.exists(base_dir):
                os.makedirs(base_dir)

            # u.append((r.rule, methods, r.endpoint))
            with open(os.path.join(p), 'w') as f:
                response = client.get(r.rule, data={'lang':options.lang})
                if response.status_code == 302:
                    f.write('<meta http-equiv="Refresh" content="0; url=%s" />' %
                            self.fix_url(response.location))
                else:
                    text = self.convert_text(response.data)
                    f.write(text)
            # if i>1:
            #     return

        print "Export static files to %s" % dst_path
        call('uliweb exportstatic %s/static' % dst_path)


    def convert_text(self, text):
        from HTMLParser import HTMLParser
        from urlparse import urlparse, urlunparse

        pos = []
        class MyHTMLParser(HTMLParser):
            def handle_starttag(self, tag, attrs):
                if tag == 'a':
                    _attrs = dict(attrs)
                    if 'href' in _attrs:
                        p = self.getpos()
                        pos.append([p[0], p[1], _attrs.get('href'), len(self.get_starttag_text()), _attrs])

        parser = MyHTMLParser()
        parser.feed(text)

        lines = text.splitlines()
        num = 0
        for line, start, href, length, attrs in reversed(pos):
            r = urlparse(href)
            if r.scheme or r.netloc:
                continue
            #relative url
            else:
                href = self.fix_url(href)
                x = list(r)
                x[2] = href
                url = urlunparse(x)
                attrs['href'] = url
                tag = '<a ' + ' '.join(['%s="%s"' % (k, v) for k, v in attrs.items()]) + '>'
                old_line = lines[line-1]
                lines[line-1] = old_line[:start] + tag + old_line[start+length:]
                num += 1

        if num > 0:
            return '\n'.join(lines)
        else:
            return text

    def fix_url(self, p):
        if p == '#':
            return p
        if p == '/':
            return '/index.html'
        if os.path.splitext(p)[1]:
            pass
        else:
            p += '.html'
        return p

register_command(StaticizeCommand)

from code import interact, InteractiveConsole
class MyInteractive(InteractiveConsole):
    def interact(self, banner=None, call=None):
        """Closely emulate the interactive Python console.
    
        The optional banner argument specify the banner to print
        before the first interaction; by default it prints a banner
        similar to the one printed by the real Python interpreter,
        followed by the current class name in parentheses (so as not
        to confuse this with the real interpreter -- since it's so
        close!).
    
        """
        try:
            sys.ps1
        except AttributeError:
            sys.ps1 = ">>> "
        try:
            sys.ps2
        except AttributeError:
            sys.ps2 = "... "
        cprt = 'Type "help", "copyright", "credits" or "license" for more information.'
        if banner is None:
            self.write("Python %s on %s\n%s\n(%s)\n" %
                       (sys.version, sys.platform, cprt,
                        self.__class__.__name__))
        else:
            self.write("%s\n" % str(banner))
        more = 0
        if call:
            call()
        while 1:
            try:
                if more:
                    prompt = sys.ps2
                else:
                    prompt = sys.ps1
                try:
                    line = self.raw_input(prompt)
                    # Can be None if sys.stdin was redefined
                    encoding = getattr(sys.stdin, "encoding", None)
                    if encoding and not isinstance(line, unicode):
                        line = line.decode(encoding)
                except EOFError:
                    self.write("\n")
                    break
                else:
                    more = self.push(line)
            except KeyboardInterrupt:
                self.write("\nKeyboardInterrupt\n")
                self.resetbuffer()
                more = 0

from uliweb import __version__

class ShellCommand(Command):
    name = 'shell'
    help = 'Create a new interactive python shell environment.'
    args = '<filename>'
    check_apps_dirs = True
    option_list = (
        make_option('-I', dest='no_ipython', default=False, action='store_true',
            help='Not using ipython.'),
        make_option('-n', '--notebook', dest='notebook', default=False, action='store_true',
            help='Starting ipython notebook.'),
        make_option('-m', '--module', dest='module', default='',
            help="Module name that will be executed when starting the shell."),
    )
    banner = "Uliweb %s Command Shell" % __version__
    skip_options = True

    def make_shell_env(self, global_options):
        from uliweb import functions, settings
        from uliweb.core.SimpleFrame import Dispatcher

        application = self.get_application(global_options)
        
        if global_options.project not in sys.path:
            sys.path.insert(0, global_options.project)

        env = {'application':application, 'settings':settings, 'functions':functions}
        return env
    
    def handle(self, options, global_options, *args):
        import subprocess as sub

        args = list(args)

        namespace = self.make_shell_env(global_options)
        try:
            import readline
        except ImportError:
            print "Module readline not available."
        else:
            import rlcompleter
            readline.parse_and_bind("tab: complete")

        try:
            import IPython
        except ImportError:
            IPython = None

        #according to https://github.com/ipython/ipython/wiki/Cookbook%3a-Updating-code-for-use-with-IPython-0.11-and-later
        if IPython and not options.no_ipython:

            if options.module:
                _args = ['-m', options.module]
            else:
                _args = []

            if options.notebook:
                # from IPython.html.notebookapp import NotebookApp
                # app = NotebookApp.instance()
                # app.initialize(['--ext', 'uliweb.utils.ipython_extension'] + args)
                # app.start()

                version = int(IPython.__version__.split('.')[0])
                if version < 3:
                    cmd = ' '.join(['ipython', 'notebook'] + args)
                else:
                    cmd = ' '.join(['jupyter', 'notebook'] + args)
                os.environ.update({'LOCAL_SETTINGS':global_options.local_settings,
                       'SETTINGS':global_options.settings})
                sub.call(cmd, shell=True, cwd=os.getcwd())
            else:
                if options.module:
                    _args.append('-i')
                IPython.start_ipython(_args + args, user_ns=namespace, banner2=self.banner)
        else:
            if not IPython and not options.no_ipython:
                print "Error: Can't import IPython, please install it first"

            from code import interact, InteractiveConsole
            Interpreter = MyInteractive(namespace)
            if args or options.module:
                def call():
                    mod = __import__(options.module or args[0], {}, {}, ['*'])
                    namespace.update(vars(mod))
            else:
                call = None
            Interpreter.interact(self.banner, call=call)
register_command(ShellCommand)

class FindCommand(Command):
    name = 'find'
    help = 'Find objects in uliweb, such as: view, template, static file etc.'
    args = ''
    check_apps_dirs = True
    option_list = (
        make_option('-t', '--template', dest='template', 
            help='Find template file path according template filename.'),
        make_option('-u', '--url', dest='url', 
            help='Find views function path according url.'),
        make_option('-U', '--search-url', dest='url_pattern',
            help='Search url according url_pattern.'),
        make_option('-c', '--static', dest='static',
            help='Find static file path according static filename.'),
        make_option('-m', '--model', dest='model', 
            help='Find model definition according model name.'),
        make_option('-o', '--option', dest='option', 
            help='Find ini option defined in which settings.ini.'),
        make_option('--tree', dest='tree', action='store_true', 
            help='Find template invoke tree, should be used with -t option together.'),
        make_option('--blocks', dest='blocks', action='store_true', 
            help='Display blocks defined in a template, only available when searching template.'),
        make_option('--with-filename', dest='with_filename', action='store_true', 
            help='Display blocks defined in a template with template filename.'),
        make_option('--source', dest='source', action='store_true',
            help='Output generated python source code of template.'),
        make_option('--comment', dest='comment', action='store_true',
            help='Output generated python source code of template and also output comment for each line.'),
    )
    
    def handle(self, options, global_options, *args):
        self.get_application(global_options)

        if options.url:
            self._find_url(options.url)
        if options.url_pattern:
            self._search_url(options.url_pattern)
        elif options.template:
            self._find_template(options.template, options.tree,
                    options.blocks, options.with_filename,
                    options.source, options.comment)
        elif options.static:
            self._find_static(global_options, options.static)
        elif options.model:
            self._find_model(global_options, options.model)
        elif options.option:
            self._find_option(global_options, options.option)
        
    def _find_url(self, url):
        from uliweb.core.SimpleFrame import url_map
        from werkzeug.test import EnvironBuilder
        from uliweb import NotFound, application

        builder = EnvironBuilder(url)
        env = builder.get_environ()
        
        url_adapter = url_map.bind_to_environ(env)
        try:
            rule, values = url_adapter.match(return_rule=True)
            print rule.rule, '--->', rule.endpoint
            mod, handler_cls, func = application.get_handler(rule.endpoint)
            if func.__doc__:
                print '\nDescription:', func.__doc__.strip()
        except NotFound:
            print 'Not Found'

    def _search_url(self, pattern):
        from uliweb.core.SimpleFrame import url_map
        import fnmatch

        urls = []
        for r in url_map.iter_rules():
            if r.methods:
                methods = ' '.join(list(r.methods))
            else:
                methods = ''
            urls.append((r.rule, methods, r.subdomain, r.endpoint))
        urls.sort()

        n = 0
        for url in urls:
            if fnmatch.fnmatch(url[0], pattern):
                print url[0], '    ', url[3]
                n += 1
        print 'Total', n

    def _find_template(self, template, tree, blocks, with_filename,
                   source, comment):
        """
        If tree is true, then will display the track of template extend or include
        """
        from uliweb import application
        from uliweb.core.template import _format_code

        def get_rel_filename(filename, path):
            f1 = os.path.splitdrive(filename)[1]
            f2 = os.path.splitdrive(path)[1]
            f = os.path.relpath(f1, f2).replace('\\', '/')
            if f.startswith('..'):
                return filename.replace('\\', '/')
            else:
                return f
        
        template_file = None

        if not tree:
            application.template_loader.comment = comment
            files = application.template_loader.find_templates(template)
            if files:
                template_file = files[0]

                for x in files:
                    print x

                if source:
                    print
                    print '---------------- source of %s ---------------' % template
                    t = application.template_loader.load(template_file)
                    if t and comment:
                        print _format_code(t.code).rstrip()
                        print
                    else:
                        print t.code
                        print

            else:
                print 'Not Found'
        else:
            application.template_loader.print_tree(template)
                
        if template_file and blocks:
            application.template_loader.print_blocks(template, with_filename)
            
    def _find_static(self, global_options, static):
        from uliweb import get_app_dir
        
        apps = self.get_apps(global_options)
        
        for appname in reversed(apps):
            path = os.path.join(get_app_dir(appname), 'static', static)
            if os.path.exists(path):
                print '%s' % path
                return
        print 'Not Found'
        
    def _find_model(self, global_options, model):
        from uliweb import settings
        
        model_path = settings.MODELS.get(model, 'Not Found')
        print model_path
        
    def _find_option(self, global_options, option):
        from uliweb import settings
        from uliweb.core.SimpleFrame import collect_settings
        from uliweb.utils.pyini import Ini

        print '------ Combined value of [%s] ------' % option
        print settings.get_var(option)

        print '------ Detail   value of [%s] ------' % option
        sec_flag = '/' not in option
        if not sec_flag:
            section, key = option.split('/')

        for f in collect_settings(global_options.project, settings_file=global_options.settings,
            local_settings_file=global_options.local_settings):
            x = Ini(f, raw=True, basepath=global_options.apps_dir)
            if sec_flag:
                if option in x:
                    print x[option]
            else:
                if section in x:
                    if key in x[section]:
                        v = x[section][key]
                        print "%s %s%s" % (str(v), key, v.value())
                
register_command(FindCommand)

class ValidateTemplateCommand(Command):
    name = 'validatetemplate'
    help = 'Validate template files syntax.'
    args = '[appname] [-f tempaltefile]'
    check_apps_dirs = True
    option_list = (
        make_option('-f', dest='template',
            help='Template filename which will be validated.'),
    )

    def handle(self, options, global_options, *args):
        self.get_application(global_options)
        from uliweb import application as app
        if options.template:
            files = [options.template]
        else:
            if args:
                files = self._find_templates(args)
            else:
                files = self._find_templates(app.apps)
        self._validate_templates(app, files, global_options.verbose)

    def _find_templates(self, apps):
        from glob import glob
        from uliweb import get_app_dir
        from uliweb.utils.common import walk_dirs

        for app in apps:
            path = os.path.join(get_app_dir(app), 'templates')
            for f in walk_dirs(path, include_ext=['.html']):
                yield f

    def _validate_templates(self, app, files, verbose):
        """
        If tree is true, then will display the track of template extend or include
        """
        from uliweb import application
        from uliweb.core.template import template_file
        from uliweb.utils.common import trim_path

        app.template_loader.log = None
        for f in files:
            try:
                t = app.template_loader.load(f)
                if verbose:
                    print 'PASSED', f
            except Exception as e:
                print 'FAILED', f, str(e)

register_command(ValidateTemplateCommand)

def collect_files(options, apps_dir, apps):
    files = [os.path.join(apps_dir, options.settings), 
        os.path.join(apps_dir, options.local_settings)]
    
    def f(path):
        if not os.path.exists(path):
            log.error("Path %s is not existed!" % path)
            return
        
        for r in os.listdir(path):
            if r in ['.svn', '_svn', '.git'] or r.startswith('.'):
                continue
            fpath = os.path.join(path, r)
            if os.path.isdir(fpath):
                f(fpath)
            else:
                ext = os.path.splitext(fpath)[1]
                if ext in ['.py', '.ini']:
                    files.append(fpath)
                if ext == '.html' and 'taglibs' in fpath:
                    files.append(fpath)

    from uliweb import get_app_dir
    for p in apps:
        path = get_app_dir(p)
        files.append(os.path.join(path, 'config.ini'))
        files.append(os.path.join(path, 'settings.ini'))
        f(path)
    return files

def call(args=None):
    from uliweb.core.commands import execute_command_line
    
    def callback(global_options):
        apps_dir = os.path.abspath(global_options.apps_dir or os.path.join(os.getcwd(), 'apps'))
        if os.path.exists(apps_dir) and apps_dir not in sys.path:
            sys.path.insert(0, apps_dir)
           
        install_config(apps_dir)
    
    from uliweb.i18n.i18ntool import I18nCommand
    register_command(I18nCommand)
    
    if isinstance(args, (unicode, str)):
        import shlex
        args = shlex.split(args)
    
    execute_command_line(args or sys.argv, get_commands, 'uliweb', callback)

def main():
    call()
    
if __name__ == '__main__':
    main()