from uliweb.form import *
from uliweb.i18n import ugettext as _

class RegisterForm(Form):
    form_buttons = Submit(value=_('Register'), _class="btn btn-primary")
#    form_title = _('Register')
    
    username = StringField(label=_('Username'), required=True)
    password = PasswordField(label=_('Password'), required=True)
    password1 = PasswordField(label=_('Password again'), required=True)
#    email = StringField(label=_('Email:'))
    next = HiddenField()
    
    def validate_username(self, data, all_data=None):
        from uliweb.orm import get_model
        
        User = get_model('user')
        user = User.get(User.c.username==data)
        if user:
            return _('User "%s" is already existed!') % data
    
    def form_validate(self, all_data):
        if all_data.password != all_data.password1:
            return {'password1' : _('Passwords are not match.')}
    
class LoginForm(Form):
    form_buttons = Submit(value=_('Login'), _class="btn btn-primary")
#    form_title = _('Login')
    
    username = UnicodeField(label=_('Username'), required=True)
    password = PasswordField(label=_('Password'), required=True)
    rememberme = BooleanField(label=_('Remember Me'))
    next = HiddenField()
    
class ChangePasswordForm(Form):
    form_buttons = Submit(value=_('Save'), _class="btn btn-primary")
#    form_title = _('Change Password')
    
    oldpassword = PasswordField(label=_('Old Password'), required=True)
    password = PasswordField(label=_('Password'), required=True)
    password1 = PasswordField(label=_('Password again'), required=True)
    action = HiddenField(default='changepassword')

    def form_validate(self, all_data):
        if all_data.password != all_data.password1:
            return {'password1' : _('Password is not right.')}

    def validate_oldpassword(self, data, all_data=None):
        from uliweb import request
        
        if not request.user.check_password(data):
            return 'Password is not right.'