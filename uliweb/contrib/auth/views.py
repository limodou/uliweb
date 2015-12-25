from uliweb.core.SimpleFrame import functions
from uliweb.i18n import ugettext_lazy as _
import urllib

def add_prefix(url):
    from uliweb import settings
    return settings.DOMAINS.static.get('url_prefix', '') + url

def login():
    from uliweb.contrib.auth import login

    form = functions.get_form('auth.LoginForm')()

    if request.user:
        next = request.GET.get('next')
        if next:
            return redirect(next)

    if request.method == 'GET':
        form.next.data = request.GET.get('next', request.referrer or add_prefix('/'))
        return {'form':form, 'msg':''}
    if request.method == 'POST':
        flag = form.validate(request.params)
        if flag:
            f, d = functions.authenticate(username=form.username.data, password=form.password.data)
            if f:
                request.session.remember = form.rememberme.data
                login(form.username.data)
                next = urllib.unquote(request.POST.get('next', add_prefix('/')))
                return redirect(next)
            else:
                form.errors.update(d)
        msg = form.errors.get('_', '') or _('Login failed!')
        return {'form':form, 'msg':str(msg)}

def register():
    from uliweb.contrib.auth import create_user, login

    form = functions.get_form('auth.RegisterForm')()

    if request.method == 'GET':
        form.next.data = request.GET.get('next', add_prefix('/'))
        return {'form':form, 'msg':''}
    if request.method == 'POST':
        flag = form.validate(request.params)
        if flag:
            from uliweb import settings
            f, d = create_user(username=form.username.data,
                password=form.password.data,
                auth_type=settings.AUTH.AUTH_TYPE_DEFAULT)
            if f:
                #add auto login support 2012/03/23
                login(d)
                next = urllib.unquote(request.POST.get('next', add_prefix('/')))
                return redirect(next)
            else:
                form.errors.update(d)

        msg = form.errors.get('_', '') or _('Register failed!')
        return {'form':form, 'msg':str(msg)}

def logout():
    from uliweb.contrib.auth import logout as out
    from uliweb import settings
    out()
    next = urllib.unquote(request.POST.get('next', add_prefix('/')))
    return redirect(next)
