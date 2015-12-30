##################################################################
# This module is desired by Django
##################################################################
import sys, os
from optparse import make_option, OptionParser, IndentedHelpFormatter
import uliweb
from uliweb.utils.common import log

def handle_default_options(options):
    """
    Include any default options that all commands should accept here
    so that ManagementUtility can handle them before searching for
    user commands.

    """
    if options.pythonpath:
        sys.path.insert(0, options.pythonpath)

class CommandError(Exception):
    """
    Exception class indicating a problem while executing a management
    command.

    If this exception is raised during the execution of a management
    command, it will be caught and turned into a nicely-printed error
    message to the appropriate output stream (i.e., stderr); as a
    result, raising this exception (with a sensible description of the
    error) is the preferred way to indicate that something has gone
    wrong in the execution of a command.

    """
    pass

def get_answer(message, answers='Yn', default='Y', quit=''):
    """
    Get an answer from stdin, the answers should be 'Y/n' etc.
    If you don't want the user can quit in the loop, then quit should be None.
    """
    if quit and quit not in answers:
        answers = answers + quit
        
    message = message + '(' + '/'.join(answers) + ')[' + default + ']:'
    ans = raw_input(message).strip().upper()
    if default and not ans:
        ans = default.upper()
    while ans not in answers.upper():
        ans = raw_input(message).strip().upper()
    if quit and ans == quit.upper():
        print "Command be cancelled!"
        sys.exit(0)
    return ans

def get_commands(mod):
    """
    Find commands from a module
    """
    import inspect
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

def get_input(prompt, default=None, choices=None, option_value=None):
    """
    If option_value is not None, then return it. Otherwise get the result from 
    input.
    """
    if option_value is not None:
        return option_value
    
    choices = choices or []
    while 1:
        r = raw_input(prompt+' ').strip()
        if not r and default is not None:
            return default
        if choices:
            if r not in choices:
                r = None
            else:
                break
        else:
            break
    return r

class CommandMetaclass(type):
    def __init__(cls, name, bases, dct):
        option_list = list(dct.get('option_list', []))
        if dct.get('options_inherit', True):
            for c in bases:
                if hasattr(c, 'option_list') and isinstance(c.option_list, list):
                    option_list.extend(c.option_list)
        cls.option_list = option_list
        
class Command(object):
    __metaclass__ = CommandMetaclass
    
    option_list = ()
    help = ''
    args = ''
    check_apps_dirs = True
    check_apps = False
    skip_options = False #if True, then it'll skip not defined options and keep them in args

    def create_parser(self, prog_name, subcommand):
        """
        Create and return the ``OptionParser`` which will be used to
        parse the arguments to this command.
    
        """
        return OptionParser(prog=prog_name,
                            usage=self.usage(subcommand),
                            version='',
                            add_help_option = False,
                            option_list=self.option_list)
    def get_version(self):
        return "Uliweb version is %s" % uliweb.version

    def usage(self, subcommand):
        """
        Return a brief description of how to use this command, by
        default from the attribute ``self.help``.
    
        """
        if len(self.option_list) > 0:
            usage = '%%prog %s [options] %s' % (subcommand, self.args)
        else:
            usage = '%%prog %s %s' % (subcommand, self.args)
        if self.help:
            return '%s\n\n%s' % (usage, self.help)
        else:
            return usage
    
    def print_help(self, prog_name, subcommand):
        """
        Print the help message for this command, derived from
        ``self.usage()``.
    
        """
        parser = self.create_parser(prog_name, subcommand)
        parser.print_help()
        
    def get_apps(self, global_options, include_apps=None):
        from uliweb.core.SimpleFrame import get_apps
        
        return get_apps(global_options.apps_dir, include_apps=include_apps, 
            settings_file=global_options.settings, local_settings_file=global_options.local_settings)
    
    def get_application(self, global_options, default_settings=None):
        from uliweb.manage import make_simple_application

        app = make_simple_application(project_dir=global_options.project,
            settings_file=global_options.settings, 
            local_settings_file=global_options.local_settings,
            default_settings=default_settings
            )
        from uliweb import application
        return application
        
    def run_from_argv(self, prog, subcommand, global_options, argv):
        """
        Set up any environment changes requested, then run this command.
    
        """
        self.prog_name = prog
        if self.skip_options:
            parser = NewOptionParser(prog=self.prog_name,
                     usage=self.usage(subcommand),
                    version='',
                    formatter = NewFormatter(),
                     add_help_option = False,
                     option_list=self.option_list)
        else:
            parser = self.create_parser(prog, subcommand)
        options, args = parser.parse_args(argv)
        self.execute(args, options, global_options)
        
    def execute(self, args, options, global_options):
        from uliweb.utils.common import check_apps_dir

        #add apps_dir to global_options and insert it to sys.path
        if global_options.apps_dir not in sys.path:
            sys.path.insert(0, global_options.apps_dir)
        
        if self.check_apps_dirs:
            check_apps_dir(global_options.apps_dir)
        if self.check_apps and args: #then args should be apps
            all_apps = self.get_apps(global_options)
            apps = args
            args = []
            for p in apps:
                if p not in all_apps:
                    print 'Error: Appname %s is not a valid app' % p
                    sys.exit(1)
                else:
                    args.append(p)
        try:
            self.handle(options, global_options, *args)
        except CommandError as e:
            log.exception(e)
            sys.exit(1)

    def handle(self, options, global_options, *args):
        """
        The actual logic of the command. Subclasses must implement
        this method.
    
        """
        raise NotImplementedError()
    
class NewFormatter(IndentedHelpFormatter):
    def format_heading(self, heading):
        return "%*s%s:\n" % (self.current_indent, "", 'Global Options')

class NewOptionParser(OptionParser):
    def _process_args(self, largs, rargs, values):
        while rargs:
            arg = rargs[0]
            longarg = False
            try:
                if arg[0:2] == "--" and len(arg) > 2:
                    # process a single long option (possibly with value(s))
                    # the superclass code pops the arg off rargs
                    longarg = True
                    self._process_long_opt(rargs, values)
                elif arg[:1] == "-" and len(arg) > 1:
                    # process a cluster of short options (possibly with
                    # value(s) for the last one only)
                    # the superclass code pops the arg off rargs
                    self._process_short_opts(rargs, values)
                else:
                    # it's either a non-default option or an arg
                    # either way, add it to the args list so we can keep
                    # dealing with options
                    del rargs[0]
                    raise Exception
            except:
                if longarg:
                    if '=' in arg:
                        del rargs[0]
                largs.append(arg)
                
class CommandManager(Command):
    usage_info = "%prog [global_options] [subcommand [options] [args]]"
    
    def __init__(self, argv=None, commands=None, prog_name=None, global_options=None):
        self.argv = argv
        self.prog_name = prog_name or os.path.basename(self.argv[0])
        self.commands = commands
        self.global_options = global_options
    
    def get_commands(self, global_options):
        if callable(self.commands):
            commands = self.commands(global_options)
        else:
            commands = self.commands
        return commands
    
    def print_help_info(self, global_options):
        """
        Returns the script's main help text, as a string.
        """
        usage = ['',"Type '%s help <subcommand>' for help on a specific subcommand." % self.prog_name,'']
        usage.append('Available subcommands:')
        commands = self.get_commands(global_options).keys()
        commands.sort()
        for cmd in commands:
            usage.append('  %s' % cmd)
        return '\n'.join(usage)
    
    def fetch_command(self, global_options, subcommand):
        """
        Tries to fetch the given subcommand, printing a message with the
        appropriate command called from the command line (usually
        "uliweb") if it can't be found.
        """
        commands = self.get_commands(global_options)
        try:
            klass = commands[subcommand]
        except KeyError:
            sys.stderr.write("Unknown command: %r\nType '%s help' for usage.\nMany commands will only run at project directory, maybe the directory is not right.\n" % \
                (subcommand, self.prog_name))
            sys.exit(1)
        return klass
    
    def execute(self, callback=None):
        """
        Given the command-line arguments, this figures out which subcommand is
        being run, creates a parser appropriate to that command, and runs it.
        """
        # Preprocess options to extract --settings and --pythonpath.
        # These options could affect the commands that are available, so they
        # must be processed early.
        self.parser = parser = NewOptionParser(prog=self.prog_name,
                             usage=self.usage_info,
#                             version=self.get_version(),
                             formatter = NewFormatter(),
                             add_help_option = False,
                             option_list=self.option_list)
        
        if not self.global_options:
            global_options, args = parser.parse_args(self.argv)
            global_options.apps_dir = os.path.normpath(os.path.join(global_options.project, 'apps'))
            handle_default_options(global_options)
            args = args[1:]
        else:
            global_options = self.global_options
            args = self.argv

        if global_options.envs:
            for x in global_options.envs:
                if '=' in x:
                    k, v = x.split('=')
                    os.environ[k.strip()] = v.strip()
                else:
                    print ('Error: environment variable definition (%s) format is not right, '
                           'shoule be -Ek=v or -Ek="a b"' % x)

        global_options.settings = global_options.settings or os.environ.get('SETTINGS', 'settings.ini')
        global_options.local_settings = global_options.local_settings or os.environ.get('LOCAL_SETTINGS', 'local_settings.ini')
        
        if callback:
            callback(global_options)
            
        if len(args) == 0:
            if global_options.version:
                print self.get_version()
                sys.exit(0)
            else:
                self.print_help(global_options)
                sys.ext(1)

        self.do_command(args, global_options)

    def print_help(self, options):
        self.parser.print_help()
        sys.stderr.write(self.print_help_info(options) + '\n')
        sys.exit(0)

    def do_command(self, args, global_options):
        try:
            subcommand = args[0]
        except IndexError:
            subcommand = 'help' # Display help if no arguments were given.
    
        if subcommand == 'help':
            if len(args) > 1:
                command = self.fetch_command(global_options, args[1])
                if issubclass(command, CommandManager):
                    cmd = command(['help'], None, '%s %s' % (self.prog_name, args[1]), global_options=global_options)
                    cmd.execute()
                else:
                    command().print_help(self.prog_name, args[1])
                sys.exit(0)
            else:
                self.print_help(global_options)
        if global_options.help:
            self.print_help(global_options)
        else:
            command = self.fetch_command(global_options, subcommand)
            if issubclass(command, CommandManager):
                cmd = command(args[1:], None, '%s %s' % (self.prog_name, subcommand), global_options=global_options)
                cmd.execute()
            else:
                cmd = command()
                cmd.run_from_argv(self.prog_name, subcommand, global_options, args[1:])
    
class ApplicationCommandManager(CommandManager):
    option_list = (
        make_option('--help', action='store_true', dest='help',
            help='show this help message and exit.'),
        make_option('-v', '--verbose', action='store_true', 
            help='Output the result in verbose mode.'),
        make_option('-s', '--settings', dest='settings', default='',
            help='Settings file name. Default is "settings.ini".'),
        make_option('-y', '--yes', dest='yes', action='store_true',
            help='Automatic yes to prompt.'),
        make_option('-L', '--local_settings', dest='local_settings', default='',
            help='Local settings file name. Default is "local_settings.ini".'),
        make_option('--project', default='.', dest='project',
            help='Your project directory, default is current directory.'),
        make_option('--pythonpath', default='',
            help='A directory to add to the Python path, e.g. "/home/myproject".'),
        make_option('--version', action='store_true', dest='version',
            help="show program's version number and exit."),
#        make_option('--include-apps', default=[], dest='include_apps',
#            help='Including extend apps when execute the command.'),
        make_option('-E', dest='envs', default=[], action='append',
            help="Environment variables definition, "
                "e.g. -Efontname=\"Your Name\", support multi variables."),
    )
    help = ''
    args = ''
    
def execute_command_line(argv=None, commands=None, prog_name=None, callback=None):
    m = ApplicationCommandManager(argv, commands, prog_name)
    m.execute(callback)
    
if __name__ == '__main__':
    execute_command_line(sys.argv)