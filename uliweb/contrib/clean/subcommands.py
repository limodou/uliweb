import os
from optparse import make_option
from uliweb.core.commands import Command, get_answer

class DirCommand(Command):
    name = 'dir'
    args = 'directory [,...]'
    help = 'Clear all files or file patterns in dirs.'
    option_list = (
        make_option('-e', '--extension', dest='extensions', action='append', default=[],
            help='Only matches extension. E.g. .txt'),
        make_option('-x', '--exclude_extensions', dest='exclude_extensions', action='append', default=[],
            help='Not matches extension.'),
        make_option('-r', '--recursion', dest='recursion', action='store_true', default=False,
            help='Recursion the directory.'),
        make_option('-d', '--days', dest='days', type='int', default=7,
            help='Delta days before now.'),
    )

    def handle(self, options, global_options, *args):

        self.get_application(global_options)

        for d in args:
            self.clean_dir(d, extensions=options.extensions,
                           exclude_extensions=options.exclude_extensions,
                           days=options.days, recursion=options.recursion,
                           verbose=global_options.verbose)

    def clean_dir(self, dir, extensions, exclude_extensions, recursion, days, verbose=False):
        from uliweb.utils.common import walk_dirs
        import datetime
        from uliweb.utils import date

        now = date.now()
        i = 0
        for f in walk_dirs(dir, include_ext=extensions, exclude_ext=exclude_extensions,
                           recursion=recursion, file_only=True):
            t = datetime.datetime.fromtimestamp(os.path.getmtime(f))
            if not days or (days and (now-t).days >= days):
                try:
                    os.unlink(f)
                    if verbose:
                        print 'Clean filename {}...'.format(f)
                    i += 1
                except:
                    import traceback
                    traceback.print_exc()
        print 'Cleaned {} files'.format(i)


class ModelCommand(Command):
    name = 'model'
    args = 'model [,...]'
    help = 'Clear all models.'
    option_list = (
        make_option('-d', '--days', dest='days', type='int', default=7,
            help='Delta days before now.'),
    )

    def handle(self, options, global_options, *args):

        self.get_application(global_options)

        for d in args:
            self.clean_model(d,
                           days=options.days,
                           verbose=global_options.verbose)

    def clean_model(self, model, days, verbose=False):
        from uliweb import functions
        import time

        if verbose:
            print 'Clean {}...'.format(model)
        M = functions.get_model(model)
        if hasattr(M, 'clear_data'):
            b = time.time()
            M.clear_data(days)
            print 'Used {} seconds to clean the {}'.format(time.time()-b, model)
        else:
            print 'There is no clear_data() function defined for {}'.format(model)
