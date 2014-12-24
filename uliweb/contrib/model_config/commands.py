import os
from uliweb import functions
from optparse import make_option
from uliweb.core.commands import Command, get_input, get_answer

class MigrateModelConfigCommand(Command):
    name = 'migrate_model_config'
    help = 'Migrate model config models.'
    args = ''
    check_apps_dirs = True
    check_apps = False
    option_list = (
        make_option('-r', '--reset', dest='reset', action='store_true', help='Just reset model config models.'),
    )

    def reset_model(self, model_name, reset):
        M = functions.get_model(model_name, signal=False)
        engine = M.get_engine().engine
        if not M.table.exists(engine):
            print "Table %s(%s) is not existed. ... CREATED" % (model_name, M.tablename)
            M.table.create(engine)
        else:
            if reset:
                print "Table %s(%s) existed. ... RESET" % (model_name, M.tablename)
                M.table.drop(engine)
                M.table.create(engine)
            else:
                print "Table %s(%s) existed. ... MIGRATE" % (model_name, M.tablename)
                M.migrate()

    def handle(self, options, global_options, *args):
        self.get_application(global_options)

        self.reset_model('model_config', options.reset)
        self.reset_model('model_config_his', options.reset)



        