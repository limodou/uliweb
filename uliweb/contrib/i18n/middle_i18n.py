import re

from uliweb.i18n import set_language, format_locale
from uliweb import Middleware
from logging import getLogger
from uliweb.utils.common import request_url

accept_language_re = re.compile(r'''
        ([A-Za-z]{1,8}(?:-[A-Za-z]{1,8})*|\*)   # "en", "en-au", "x-y-z", "*"
        (?:;q=(0(?:\.\d{,3})?|1(?:.0{,3})?))?   # Optional "q=1.00", "q=0.8"
        (?:\s*,\s*|$)                            # Multiple accepts per header.
        ''', re.VERBOSE)

def get_language_from_request(request, settings):
    #check query_string, and the key will be defined in settings.ini
    #now only support GET method
    debug = '__debug__' in request.GET
    log = getLogger(__name__)
    url_lang_key = settings.get_var('I18N/URL_LANG_KEY')
    if url_lang_key:
        lang = request.GET.get(url_lang_key)
        if lang:
            if debug:
                log.info('Detect from URL=%s, lang_key=%s, lang=%s' %
                         (request_url(), url_lang_key, lang))
            return lang

    #check session
    if hasattr(request, 'session'):
        lang = request.session.get('uliweb_language')
        if lang:
            if debug:
                log.info('Detect from session=%s, lang=%s' %
                         ('uliweb_language', lang))
            return lang

    #check cookie
    lang = request.cookies.get(settings.I18N.LANGUAGE_COOKIE_NAME)
    if lang:
        if debug:
            log.info('Detect from cookie=%s, lang=%s' %
                     (settings.I18N.LANGUAGE_COOKIE_NAME, lang))
        return lang

    #check browser HTTP_ACCEPT_LANGUAGE head
    accept = request.environ.get('HTTP_ACCEPT_LANGUAGE', None)
    if not accept:
        if debug:
            log.info('Detect from settings of LANGUAGE_CODE=%s' % lang)
        return settings.I18N.get('LANGUAGE_CODE')
    languages = settings.I18N.get('SUPPORT_LANGUAGES', [])
    for accept_lang, unused in parse_accept_lang_header(accept):
        if accept_lang == '*':
            break

        normalized = format_locale(accept_lang)
        if not normalized:
            continue
        
        if normalized in languages:
            if debug:
                log.info('Detect from HTTP Header=%s, lang=%s' %
                         ('HTTP_ACCEPT_LANGUAGE', normalized))
            return normalized

    #return default lanaguage
    lang = settings.I18N.get('LANGUAGE_CODE')
    if debug:
        log.info('Detect from settings of LANGUAGE_CODE=%s' % lang)
    return lang

def parse_accept_lang_header(lang_string):
    """
    Parses the lang_string, which is the body of an HTTP Accept-Language
    header, and returns a list of (lang, q-value), ordered by 'q' values.

    Any format errors in lang_string results in an empty list being returned.
    """
    result = []
    pieces = accept_language_re.split(lang_string)
    if pieces[-1]:
        return []
    for i in range(0, len(pieces) - 1, 3):
        first, lang, priority = pieces[i : i + 3]
        if first:
            return []
        priority = priority and float(priority) or 1.0
        result.append((lang, priority))
    result.sort(lambda x, y: -cmp(x[1], y[1]))
    return result

class I18nMiddle(Middleware):
    def process_request(self, request):
        lang = get_language_from_request(request, self.settings)
        if lang:
            set_language(lang)