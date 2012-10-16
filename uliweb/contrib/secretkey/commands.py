import os
from uliweb.core.commands import Command

class MakeKeyCommand(Command):
    name = 'makekey'
    help = 'Make secret key to to a file.'
    has_options = False
    
    def handle(self, options, global_options, *args):
        from random import choice
        from uliweb.core.SimpleFrame import get_settings
        settings = get_settings(global_options.project, settings_file=global_options.settings, 
            local_settings_file=global_options.local_settings)
        keyfile = os.path.join(global_options.project, settings.SECRETKEY.SECRET_FILE)
        f = open(keyfile, 'wb')
        secret_key = ''.join([choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)') for i in range(settings.SECRETKEY.KEY_LENGTH)])
        f.write(secret_key)

