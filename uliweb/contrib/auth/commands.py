from uliweb.core.commands import Command
from uliweb.contrib.orm.commands import SQLCommandMixin

class CreateSuperUserCommand(SQLCommandMixin, Command):
    name = 'createsuperuser'
    help = 'Create a super user account.'
    
    def handle(self, options, global_options, *args):
        from uliweb.manage import make_simple_application
        from uliweb import orm
        from getpass import getpass
        
        app = make_simple_application(apps_dir=global_options.apps_dir, 
            settings_file=global_options.settings, local_settings_file=global_options.local_settings)
        db = orm.get_connection()
        
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
        
        User = orm.get_model('user', options.engine)
        user = User(username=username, email=email)
        user.set_password(password)
        user.is_superuser = True
        user.save()

class EncryptPasswordCommand(Command):
    name = 'encryptpassword'
    help = 'Encrypt password.'

    def handle(self, options, global_options, *args):
        from uliweb import functions
        from uliweb.core.SimpleFrame import get_settings, __global__
        import getpass
        
        settings = get_settings(global_options.project, settings_file=global_options.settings, 
            local_settings_file=global_options.local_settings)
        __global__.settings = settings
        password = getpass.getpass('Input your password(Blank will quit):')
        if not password:
            return
        password1 = getpass.getpass('Enter your password twice:')
        if password != password1:
            print "Your password is not matched, please run the command again"
        else:
            print functions.encrypt_password(password)
