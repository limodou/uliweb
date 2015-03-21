from uliweb.core.commands import Command


class CeleryCommand(Command):
    name = 'celery'
    args = 'celery_commands'
    check_apps_dirs = True
    skip_options = True

    def handle(self, options, global_options, *args):
        from celery.bin import celery
        self.get_application(global_options)
        args = list(args)
        args.insert(0, 'celery')
        celery.main(args)
