from uliweb.i18n import format_locale
from uliweb.i18n import ugettext_lazy as _

_LANGUAGES = {
    'en_US':_('English'), 
    'zh_CN':_('Simplified Chinese'),
}
LANGUAGES = {}
for k, v in _LANGUAGES.items():
    LANGUAGES[format_locale(k)] = v

def startup_installed(sender):
    """
    @LANGUAGE_CODE
    """
    import os
    from uliweb.core.SimpleFrame import get_app_dir
    from uliweb.i18n import install, set_default_language
    from uliweb.utils.common import pkg, expand_path
    
    path = pkg.resource_filename('uliweb', '')
    _dirs = []
    for d in sender.settings.get_var('I18N/LOCALE_DIRS', []):
        _dirs.append(expand_path(d))
    localedir = ([os.path.normpath(sender.apps_dir + '/..')] + 
        [get_app_dir(appname) for appname in sender.apps] + [path] + _dirs)
    install('uliweb', localedir)
    set_default_language(sender.settings.I18N.LANGUAGE_CODE)
    
def prepare_default_env(sender, env):
    from uliweb.i18n import ugettext_lazy
    env['_'] = ugettext_lazy
