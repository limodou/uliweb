from uliweb.core.commands import CommandManager


class CeleryCommand(CommandManager):
    name = 'celery'
    args = 'celery_commands'
    check_apps_dirs = True

    def do_command(self, args, global_options):
        from celery.bin import celery
        self.get_application(global_options)
        args.insert(0, 'celery')
        celery.main(args)
