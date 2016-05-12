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
                           recursion=recursion, file_only=True, use_default_pattern=False):
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
    help = 'Clear all models. Model should has clear_data(days, cont) method.'
    option_list = (
        make_option('-d', '--days', dest='days', type='int', default=7,
            help='Delta days before now.'),
        make_option('-c', '--count', dest='count', type='int', default=5000,
            help='Records count of cleaning at one time. Default is 5000.'),
    )

    def handle(self, options, global_options, *args):

        self.get_application(global_options)

        for d in args:
            self.clean_model(d,
                       days=options.days,
                       count=options.count,
                       verbose=global_options.verbose)

    def clean_model(self, model, days, count, verbose=False):
        from uliweb import functions
        import time
        import logging
        import types
        from uliweb.orm import Begin, Commit, Rollback

        log = logging.getLogger(__name__)

        if verbose:
            print 'Clean {}, days={}, count={} ...'.format(model, days, count)
        M = functions.get_model(model)
        if hasattr(M, 'clear_data'):
            b = time.time()
            t = 0
            Begin()
            try:
                ret = M.clear_data(days, count)
                Commit()
            except Exception as e:
                Rollback()
                log.exception(e)
                return

            if isinstance(ret, types.GeneratorType):
                while 1:
                    Begin()
                    try:
                        n = ret.next()
                        t += n
                        Commit()
                    except StopIteration:
                        break
                    except Exception as e:
                        Rollback()
                        log.exception(e)
                        break
            else:
                t = ret


            print 'Used {} seconds to clean the {}, total records is {}'.format(time.time()-b, model, t)
        else:
            print 'There is no clear_data() function defined for {}'.format(model)
