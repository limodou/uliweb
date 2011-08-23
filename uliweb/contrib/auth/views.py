from uliweb.core.SimpleFrame import expose
from uliweb.i18n import ugettext_lazy as _

def login():
    from uliweb.contrib.auth import authenticate, login
    from forms import LoginForm
    from uliweb.form import Submit, Tag
    
    LoginForm.form_buttons = [Submit(value=_('Login'), _class="button")]
    
    form = LoginForm()
    
    if request.method == 'GET':
        form.next.data = request.GET.get('next', '/')
        return {'form':form, 'message':''}
    if request.method == 'POST':
        flag = form.validate(request.params)
        if flag:
            f, d = authenticate(request, username=form.username.data, password=form.password.data)
            if f:
                request.session.remember = form.rememberme.data
                login(request, form.username.data)
                next = request.POST.get('next', '/')
                return redirect(next)
            else:
                data = d
        m = form.errors.get('_', '') or 'Login failed!'
        message = '<p class="error message">%s</p>' % m
        return {'form':form, 'message':message}

def register():
    from uliweb.contrib.auth import create_user
    from forms import RegisterForm
    
    form = RegisterForm()
    
    if request.method == 'GET':
        form.next.data = request.GET.get('next', '/')
        return {'form':form, 'message':''}
    if request.method == 'POST':
        flag = form.validate(request.params)
        if flag:
            f, d = create_user(request, username=form.username.data, password=form.password.data)
            if f:
                next = request.POST.get('next', '/')
                return redirect(next)
            else:
                form.errors.update(d)
                
        m = form.errors.get('_', '') or 'Register failed!'
        message = '<p class="error message">%s</p>' % m
        return {'form':form, 'message':message, 'message_type':'error'}
        
def logout():
    from uliweb.contrib.auth import logout as out
    out(request)
    next = request.GET.get('next', '/')
    return redirect(next)
    
def admin():
    from forms import ChangePasswordForm
    changepasswordform = ChangePasswordForm()
    if request.method == 'GET':
        return {'changepasswordform':changepasswordform}
    if request.method == 'POST':
        if request.POST.get('action') == 'changepassword':
            flag = changepasswordform.valiate(request.POST, request)
            if flag:
                return redirect(request.path)
            else:
                message = '<p class="error message">There was something wrong! Please fix them.</p>'
                return {'changepasswordform':changepasswordform, 
                    'message':message}
