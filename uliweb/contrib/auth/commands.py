import os, sys
import datetime
from uliweb.core.commands import Command
from optparse import make_option
from uliweb.utils.common import log, is_pyfile_exist

class CreateSuperUserCommand(Command):
    name = 'createsuperuser'
    help = 'Create a super user account.'
    
    def handle(self, options, global_options, *args):
        from uliweb.core.SimpleFrame import Dispatcher
        from uliweb import orm
        from getpass import getpass
        
        app = Dispatcher(apps_dir=global_options.project, start=False)
        orm.set_auto_create(True)
        db = orm.get_connection(app.settings.ORM.CONNECTION)
        
        username = ''
        while not username:
            username = raw_input("Please enter the super user's name: ")
        email = ''
        while not email:
            email = raw_input("Please enter the email of [%s]: " % username)
            
        password = ''
        while not password:
            password = getpass("Please enter the password for [%s(%s)]: " % (username, email))
        repassword = ''
        while not repassword:
            repassword = getpass("Please enter the password again: ")
        
        if password != repassword:
            print "The password is not matched, can't create super user!"
            return
        
        orm.set_dispatch_send(False)
        
        User = orm.get_model('user')
        user = User(username=username, email=email)
        user.set_password(password)
        user.is_superuser = True
        user.save()
