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
        return {'form':form, 'msg':''}
    if request.method == 'POST':
        flag = form.validate(request.params)
        if flag:
            f, d = authenticate(username=form.username.data, password=form.password.data)
            if f:
                request.session.remember = form.rememberme.data
                login(form.username.data)
                next = request.POST.get('next', '/')
                return redirect(next)
            else:
                data = d
        msg = form.errors.get('_', '') or _('Login failed!')
        return {'form':form, 'msg':str(msg)}

def register():
    from uliweb.contrib.auth import create_user
    from forms import RegisterForm
    
    form = RegisterForm()
    
    if request.method == 'GET':
        form.next.data = request.GET.get('next', '/')
        return {'form':form, 'msg':''}
    if request.method == 'POST':
        flag = form.validate(request.params)
        if flag:
            f, d = create_user(username=form.username.data, password=form.password.data)
            if f:
                next = request.POST.get('next', '/')
                return redirect(next)
            else:
                form.errors.update(d)
                
        msg = form.errors.get('_', '') or _('Register failed!')
        return {'form':form, 'msg':str(msg)}
        
def logout():
    from uliweb.contrib.auth import logout as out
    out()
    next = request.GET.get('next', '/')
    return redirect(next)
