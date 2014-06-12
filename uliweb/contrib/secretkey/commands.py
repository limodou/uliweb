import os
from uliweb.core.commands import Command
from optparse import make_option

class MakeKeyCommand(Command):
    name = 'makekey'
    help = 'Make secret key to to a file.'
    option_list = (
        make_option('-o', dest="output", 
            help='Output key file name.'),
    )

    def handle(self, options, global_options, *args):
        from random import choice
        from uliweb.core.SimpleFrame import get_settings
        from uliweb.core.commands import get_answer
        
        settings = get_settings(global_options.project, settings_file=global_options.settings, 
            local_settings_file=global_options.local_settings)
        output = options.output or settings.SECRETKEY.SECRET_FILE
        keyfile = os.path.join(global_options.project, output)
        if os.path.exists(keyfile):
            message = 'The file %s is already existed, do you want to overwrite' % keyfile
            ans = 'Y' if global_options.yes else get_answer(message)
            if ans != 'Y':
                return
        print 'Creating secretkey file %s...' % keyfile,
        f = open(keyfile, 'wb')
        secret_key = ''.join([choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)') for i in range(settings.SECRETKEY.KEY_LENGTH)])
        f.write(secret_key)
        print 'OK'

