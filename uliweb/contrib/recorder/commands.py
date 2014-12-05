import os, sys
from uliweb.core.commands import Command, get_answer, CommandManager, get_commands
from optparse import make_option
import inspect

class RecorderCommand(CommandManager):
    name = 'recorder'
    args = 'recorder_commands'
    check_apps_dirs = True

    def get_commands(self, global_options):
        import subcommands
        cmds = get_commands(subcommands)
        return cmds
    
