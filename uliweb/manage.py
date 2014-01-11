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
        from uliweb import get_apps
        
        apps = get_apps(global_options.apps_dir, settings_file=global_options.settings,
                local_settings_file=global_options.local_settings)
        for f in apps:
            m = '%s.commands' % f
            try:
                mod = __import__(m, fromlist=['*'])
            except ImportError as e:
                if not str(e).startswith('No module named'):
                    import traceback
                    traceback.print_exc()
                continue
            
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
    include_apps=None, debug_console=True, settings_file='settings.ini', 
    local_settings_file='local_settings.ini', start=True, default_settings=None, 
    dispatcher_cls=None, dispatcher_kwargs=None, debug_cls=None, debug_kwargs=None, reuse=True):
    """
    Make an application object
    """
    from uliweb.utils.common import import_attr
    from werkzeug.debug import DebuggedApplication
    
    #is reuse, then create application only one
    if reuse and hasattr(SimpleFrame.__global__, 'application') and SimpleFrame.__global__.application:
        return SimpleFrame.__global__.application
    
    dispatcher_cls = dispatcher_cls or SimpleFrame.Dispatcher
    dispatcher_kwargs = dispatcher_kwargs or {}
    
    if project_dir:
        apps_dir = os.path.normpath(os.path.join(project_dir, 'apps'))
    if not project_dir:
        project_dir = os.path.normpath(os.path.abspath(os.path.join(apps_dir, '..')))
        
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
        **dispatcher_kwargs)
    
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
    settings_file='settings.ini', local_settings_file='local_settings.ini', 
    default_settings=None, dispatcher_cls=None, dispatcher_kwargs=None, reuse=True):
    settings = {'ORM/AUTO_DOTRANSACTION':False}
    settings.update(default_settings or {})
    return make_application(apps_dir=apps_dir, project_dir=project_dir,
        include_apps=include_apps, debug_console=False, debug=False,
        settings_file=settings_file, local_settings_file=local_settings_file,
        start=False, default_settings=settings, dispatcher_cls=dispatcher_cls, 
        dispatcher_kwargs=dispatcher_kwargs, reuse=reuse)

class MakeAppCommand(Command):
    name = 'makeapp'
    args = 'appname'
    help = 'Create a new app according the appname parameter.'
    option_list = (
        make_option('-f', action='store_true', dest="force", 
            help='Force to create app directory.'),
    )
    has_options = True
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
                if options.force:
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
    option_list = (
        make_option('-f', action='store_true', dest="force", 
            help='Force to create project directory.'),
    )
    has_options = True
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
            if options.force:
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
            setup_file = os.path.join(project_name, 'setup.py')
            text = template_file(setup_file, {'project_name':project_name})
            with open(setup_file, 'w') as f:
                f.write(text)
            #rename .gitignore.template to .gitignore
            os.rename(os.path.join(project_name, '.gitignore.template'), os.path.join(project_name, '.gitignore'))
register_command(MakeProjectCommand)

class SupportCommand(Command):
    name = 'support'
    help = 'Add special support to existed project, such as: gae, dotcloud, sae, bae, fcgi, heroku, tornado, gevent, gevent-socketio'
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
                        prompt, default = v
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
    has_options = True
    
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
    
class ExportCommand(Command):
    name = 'export'
    help = 'Export all installed apps or specified module source files to output directory.'
    args = '[module1 module2]'
    check_apps_dirs = True
    option_list = (
        make_option('-d', dest='outputdir',  
            help='Output directory of exported files.'),
    )
    has_options = True

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
    )
    has_options = True
    
    def handle(self, options, global_options, *args):
        if not args:
            print "Error: There is no command module name behind call command."
            return
        else:
            command = args[0]
        
        if options.application:
            self.get_application(global_options)
            
        if not options.appname:
            apps = self.get_apps(global_options)
        else:
            apps = [options.appname]
        exe_flag = False
        
        def get_module(command, apps):
            if '.' in command:
                yield command
            else:
                for f in apps:
                    yield '%s.%s' % (f, command)
                
        for m in get_module(command, apps):
            try:
                mod = __import__(m, fromlist=['*'])
                if global_options.verbose:
                    print "Importing... %s" % m
                if hasattr(mod, 'call'):
                    getattr(mod, 'call')(args, options, global_options)
                elif hasattr(mod, 'main'):
                    getattr(mod, 'main')(args, options, global_options)
                else:
                    raise Exception("Can't find call or main function in module %s" % m)
                exe_flag = True
            except ImportError:
                pass
            
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
    args = '[appname, appname, ...]'
    check_apps = False
    check_apps_dirs = False
    
    def handle(self, options, global_options, *args):
        from uliweb.utils.common import extract_dirs
        from uliweb import get_app_dir
        
        if not args:
            extract_dirs('uliweb', 'template_files/command', '.', verbose=global_options.verbose)
        else:
            for f in args:
                p = get_app_dir(f)
                extract_dirs('uliweb', 'template_files/command', p, verbose=global_options.verbose)
register_command(MakeCmdCommand)

class RunserverCommand(Command):
    name = 'runserver'
    help = 'Start a new development server.'
    args = ''
    has_options = True
    option_list = (
        make_option('-h', dest='hostname', default='localhost',
            help='Hostname or IP.'),
        make_option('-p', dest='port', type='int', default=8000,
            help='Port number.'),
        make_option('--no-reload', dest='reload', action='store_false', default=True,
            help='If auto reload the development server. Default is True.'),
        make_option('--no-debug', dest='debug', action='store_false', default=True,
            help='If auto enable debug mode. Default is True.'),
        make_option('--color', dest='color', action='store_true', default=False,
            help='Output colored log info. Default is False.'),
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
    )
    develop = False
    
    def handle(self, options, global_options, *args):
        from werkzeug.serving import run_simple
        import logging
        from logging import StreamHandler
        from uliweb.utils.coloredlog import ColoredFormatter
        
        if self.develop:
            include_apps = ['plugs.develop']
        else:
            include_apps = []
        
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
                        local_settings_file=global_options.local_settings, debug_cls=debug_cls)
        
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
        
        if options.tornado:
            try:
                import tornado.wsgi
                import tornado.httpserver
                import tornado.ioloop
                import tornado.autoreload
            except:
                print 'Error: Please install tornado first'
                sys.exit(1)
               
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
        elif options.gevent:
            try:
                from gevent.wsgi import WSGIServer
                from gevent import monkey
            except:
                print 'Error: Please install gevent first'
                sys.exit(1)
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
            
        elif options.gsocketio:
            try:
                from gevent import monkey
            except:
                print 'Error: Please install gevent first'
                sys.exit(1)
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
        else:
            run_simple(options.hostname, options.port, get_app(), options.reload, False, True,
                extra_files, 1, options.thread, options.processes, ssl_context=ctx)
register_command(RunserverCommand)

class DevelopCommand(RunserverCommand):
    name = 'develop'
    develop = True
register_command(DevelopCommand)

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
    
class ShellCommand(Command):
    name = 'shell'
    help = 'Create a new interactive python shell environment.'
    args = '<filename>'
    check_apps_dirs = True
    has_options = True
#    option_list = (
#        make_option('-i', dest='ipython', default=False, action='store_true',
#            help='Using ipython if exists.'),
#    )
    banner = "Uliweb Command Shell"
    
    def make_shell_env(self, global_options):
        from uliweb import functions
        
        application = SimpleFrame.Dispatcher(project_dir=global_options.project, 
            settings_file=global_options.settings, 
            local_settings_file=global_options.local_settings, 
            start=False)
        
        if global_options.project not in sys.path:
            sys.path.insert(0, global_options.project)
        
        env = {'application':application, 'settings':application.settings, 'functions':functions}
        return env
    
    def handle(self, options, global_options, *args):
        namespace = self.make_shell_env(global_options)
#        if options.ipython:
#            try:
#                import IPython
#            except ImportError:
#                pass
#            else:
#                sh = IPython.Shell.IPShellEmbed(banner=self.banner)
#                sh(global_ns={}, local_ns=namespace)
#                return
        from code import interact, InteractiveConsole
        Interpreter = MyInteractive(namespace)
        if args:
            def call():
                execfile(args[0], namespace)
        else:
            call = None
        Interpreter.interact(self.banner, call=call)
register_command(ShellCommand)

class FindCommand(Command):
    name = 'find'
    help = 'Find objects in uliweb, such as: view, template, static file etc.'
    args = ''
    check_apps_dirs = True
    has_options = True
    option_list = (
        make_option('-t', '--template', dest='template', 
            help='Find template file path according template filename.'),
        make_option('-u', '--url', dest='url', 
            help='Find views function path according url.'),
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
    )
    
    def handle(self, options, global_options, *args):
        self.get_application(global_options)
        if options.url:
            self._find_url(options.url)
        elif options.template:
            self._find_template(options.template, options.tree, options.blocks, options.with_filename)
        elif options.static:
            self._find_static(global_options, options.static)
        elif options.model:
            self._find_model(global_options, options.model)
        elif options.option:
            self._find_option(global_options, options.option)
        
    def _find_url(self, url):
        from uliweb.core.SimpleFrame import url_map
        from werkzeug.test import EnvironBuilder
        from uliweb import NotFound
        
        builder = EnvironBuilder(url)
        env = builder.get_environ()
        
        url_adapter = url_map.bind_to_environ(env)
        try:
            endpoint, values = url_adapter.match()
            print '%s' % endpoint
        except NotFound:
            print 'Not Found'

    def _find_template(self, template, tree, blocks, with_filename):
        """
        If tree is true, then will display the track of template extend or include
        """
        from uliweb import application
        from uliweb.core.template import Template, BaseBlockNode
        
        def get_rel_filename(filename, path):
            f1 = os.path.splitdrive(filename)[1]
            f2 = os.path.splitdrive(path)[1]
            f = os.path.relpath(f1, f2).replace('\\', '/')
            if f.startswith('..'):
                return filename.replace('\\', '/')
            else:
                return f
        
        filename = None
        template_file = None
        if not tree:
            for dir in application.template_dirs:
                filename = os.path.join(dir, template)
                if os.path.exists(filename):
                    if not template_file:
                        template_file = filename
                    print filename.replace('\\', '/')
        else:
            tree_ids = {}
            nodes = {}
                    
            def make_tree(alist):
                parents = []
                for p, c, prop in alist:
                    _ids = tree_ids.setdefault(p, [])
                    _ids.append(c)
                    nodes[c] = {'id':c, 'prop':prop}
                    parents.append(p)
                
                d = list(set(parents) - set(nodes.keys()))
                for x in d:
                    nodes[x] = {'id':x, 'prop':''}
                return d
                    
            def print_tree(subs, cur=None, level=1, indent=4):
                for x in subs:
                    n = nodes[x]
                    caption = ('(%s)' % n['prop']) if n['prop'] else ''
                    if cur == n['id']:
                        print '-'*(level*indent-1)+'>', '%s%s' % (caption, n['id'])
                    else:
                        print ' '*level*indent, '%s%s' % (caption, n['id'])
                    print_tree(tree_ids.get(x, []), cur=cur, level=level+1, indent=indent)
            
            templates = []
            path = os.getcwd()
            for dir in application.template_dirs:
                filename = os.path.join(dir, template)
                if os.path.exists(filename):
                    if not template_file:
                        template_file = filename
                    
                    print get_rel_filename(filename, path)
                    print
                    print '-------------- Tree --------------'
                    break
            if filename:
                def see(action, cur_filename, filename):
                    #templates(get_rel_filename(filename, path), cur_filename, action)
                    if action == 'extend':
                        templates.append((get_rel_filename(filename, path), get_rel_filename(cur_filename, path), action))
                    else:
                        templates.append((get_rel_filename(cur_filename, path), get_rel_filename(filename, path), action))
                    
                t = Template(open(filename, 'rb').read(), vars={}, dirs=application.template_dirs, see=see)
                t.set_filename(filename)
                t.get_parsed_code()

                print_tree(make_tree(templates), get_rel_filename(filename, path))
                
        if template_file and blocks:
            print
            print '-------------- Blocks --------------'
            t = Template(open(template_file, 'rb').read(), vars={}, dirs=application.template_dirs)
            t.set_filename(template)
            t.get_parsed_code()
            
            path = os.getcwd()
            
            def p(node, tab=4):
                for x in node.nodes:
                    if isinstance(x, BaseBlockNode):
                        if x.name in t.content.root.block_vars:
                            x = t.content.root.block_vars[x.name][-1]
                            _file = x.template_file
                        else:
                            _file = x.template_file
                        
                        f = get_rel_filename(_file, path)
                        if with_filename:
                            print ' '*tab + x.name, '  ('+f+')'
                        else:
                            print ' '*tab + x.name
                        p(x, tab+4)
            p(t.content)
            
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
            x = Ini(f, raw=True)
            if sec_flag:
                if option in x:
                    print x[option]
            else:
                if section in x:
                    if key in x[section]:
                        v = x[section][key]
                        print "%s %s%s" % (str(v), key, v.value())
                
register_command(FindCommand)

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
        apps_dir = global_options.apps_dir or os.path.join(os.getcwd(), 'apps')
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