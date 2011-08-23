from uliweb.core.SimpleFrame import expose
from Portal.modules.menu import menu
from uliweb import response, request, application, error, settings
import os

def __begin__():
    response.menu=menu(request, 'Documents')

@expose('/documents')
def documents():
    return _show('content.rst')

def _show(filename, lang=None, render=True):
    from uliweb.utils.rst import to_html
    from uliweb.core.template import template
    from uliweb.i18n import get_language, format_locale
    if not filename.endswith('.rst'):
        filename += '.rst'
    if not lang:
        #get from query string, and auto set_cookie
        lang = request.GET.get('lang')
        if not lang:
            lang = get_language()
        else:
            response.set_cookie(settings.I18N.LANGUAGE_COOKIE_NAME, lang, max_age=365*24*3600)
    if lang:
        lang = format_locale(lang)
        f = application.get_file(os.path.join(lang, filename), dir='files')
        if f:
            filename = f
    _f = application.get_file(filename, dir='files')
    if _f:
        content = file(_f).read()
        if render:
            content = to_html(template(content, env=application.get_view_env()))
        else:
            content = to_html(content)
        response.write(application.template('show_document.html', locals()))
        return response
    else:
        error("Can't find the file %s" % filename)
    
@expose('/documents/<path:filename>', defaults={'lang':''})
#@expose('/documents/<path:filename>')
#def show_document(filename, lang=''):
#this is also available
@expose('/documents/<lang>/<path:filename>')
def show_document(filename, lang):
    return _show(filename, lang, False)