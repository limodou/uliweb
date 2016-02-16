from uliweb.core.commands import CommandManager, get_commands

class CleanCommand(CommandManager):
    name = 'clean'
    args = 'subcommands'
    check_apps_dirs = True

    def get_commands(self, global_options):
        import subcommands
        cmds = get_commands(subcommands)
        return cmds
    
