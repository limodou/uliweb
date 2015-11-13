from uliweb.core.commands import Command, CommandManager, get_commands
from optparse import make_option

class DataDictCommand(CommandManager):
    #change the name to real command name, such as makeapp, makeproject, etc.
    name = 'datadict'
    #help information
    help = "Data dict tool, create index, validate models' of apps or tables"
    #args information, used to display show the command usage message
    args = ''
    #if True, it'll check the current directory should has apps directory
    check_apps_dirs = True
    #if True, it'll check args parameters should be valid apps name
    check_apps = False
    #if True, it'll skip not predefined parameters in options_list, otherwise it'll
    #complain not the right parameters of the command, it'll used in subcommands or
    #passing extra parameters to a special command
    skip_options = True




    def get_commands(self, global_options):
        import datadict_subcommands as subcommands
        cmds = get_commands(subcommands)
        return cmds
