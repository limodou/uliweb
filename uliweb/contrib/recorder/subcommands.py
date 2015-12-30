import os
from optparse import make_option
from uliweb.core.commands import Command, get_answer

class ClearCommand(Command):
    name = 'clear'
    help = 'Clear all records of recorder.'

    def handle(self, options, global_options, *args):
        from uliweb import functions
        from uliweb.orm import Commit

        self.get_application(global_options)

        Recorder = functions.get_model('uliwebrecorder')
        Recorder.all().clear()
        Commit()

class StartCommand(Command):
    name = 'start'
    help = 'Start recorder monitor process.'

    def handle(self, options, global_options, *args):
        from uliweb import functions
        from uliweb.orm import Commit

        self.get_application(global_options)

        S = functions.get_model('uliwebrecorderstatus')
        s = S.all().one()
        if not s:
            s = S(status='S')
        else:
            s.status = 'S'
        s.save()
        Commit()

class StopCommand(Command):
    name = 'stop'
    help = 'Stop recorder monitor process.'

    def handle(self, options, global_options, *args):
        from uliweb import functions
        from uliweb.orm import Commit

        self.get_application(global_options)

        S = functions.get_model('uliwebrecorderstatus')
        s = S.all().one()
        if s:
            s.status = 'E'
            s.save()
            Commit()

class StatusCommand(Command):
    name = 'status'
    help = 'Show status of recorder monitor.'

    def handle(self, options, global_options, *args):
        from uliweb import functions

        self.get_application(global_options)

        S = functions.get_model('uliwebrecorderstatus')
        s = S.all().one()
        if s:
            status = s.status
        else:
            status = 'E'
        print 'Recorder status is', S.status.get_display_value(status).upper()

class PrintCommand(Command):
    name = 'print'
    help = 'Print all records of recorder.'
    args = '[--time begin_time] [--id begin_id] outputfile'
    option_list = (
        make_option('--time', dest='begin_time',
            help='All records which great and equal than this time will be processed.'),
        make_option('--id', dest='id',
            help='All records which great and equal than the id value will be processed.'),
        make_option('--template', dest='template', default='recorder.tpl',
            help='Output template file. Default is recorder.tpl.'),
        make_option('--template_row', dest='template_row', default='recorder_row.tpl',
            help='Easy rocord fo recorder output template file. Default is recorder_row.tpl.'),
    )

    def handle(self, options, global_options, *args):
        from uliweb.utils.common import pkg
        from uliweb import functions
        from uliweb.core.template import template_file
        from uliweb.orm import true
        import time

        self.get_application(global_options)

        Recorder = functions.get_model('uliwebrecorder')

        if args:
            if os.path.exists(args[0]):
                message = "Ths file %s is already exists, do you want to overwrite it?" % args[0]
                ans = 'Y' if global_options.yes else get_answer(message)
                if ans != 'Y':
                    return

            out = open(args[0], 'w')
            relpath = os.path.normpath(os.path.relpath(os.path.dirname(args[0]) or './', '.')).replace('\\', '/')
        else:
            out = sys.stdout
            relpath = '.'

        condition = true()
        if options.begin_time:
            condition = (Recorder.c.begin_datetime >= options.begin_time) & condition
        if options.id:
            condition = (Recorder.c.id >= int(options.id)) & condition

        path = pkg.resource_filename('uliweb.contrib.recorder', 'template_files')
        tplfile = os.path.join(path, options.template).replace('\\', '/')
        row_tplfile = os.path.join(path, options.template_row).replace('\\', '/')

        out.write('#coding=utf8\n')
        if global_options.verbose:
            print '#recorder template is "%s"' % tplfile
            print '#recorder row template is "%s"' % row_tplfile

        begin = time.time()
        rows = []
        for row in Recorder.filter(condition):
            rows.append(template_file(row_tplfile, {'row':row}).rstrip())

        out.write(template_file(tplfile, {'project_dir':relpath, 'rows':rows}))
        out.write('\n#total %d records output, time used %ds\n' % (len(rows), time.time()-begin))