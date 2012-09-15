#! /usr/bin/env python
#coding=utf-8

import re

from uliweb import Middleware, functions

_POST_FORM_RE = re.compile(r'(<form\W[^>]*\bmethod\s*=\s*(\'|"|)POST(\'|"|)\b[^>]*>)', re.IGNORECASE)

_HTML_TYPES = ('text/html', 'application/xhtml+xml')

class CSRFMiddleware(Middleware):
    ORDER = 150

    def __init__(self, application, settings):
        super(CSRFMiddleware, self).__init__(application, settings)

    def process_request(self, request):
        # process each request
        if self.settings.get_var('CSRF/enable', False):
            if request.method in ('POST', 'DELETE', 'PUT', 'PATCH') or (request.method == 'GET' and request.GET.get(self.settings.CSRF.form_token_name)):
                functions.check_csrf_token()

    def process_response(self, request, response):
        if not self.settings.get_var('CSRF/enable', False):
            return response
        
        token = functions.csrf_token()

        response.set_cookie(self.settings.CSRF.cookie_token_name, token, max_age=self.settings.CSRF.timeout)

        if getattr(response, 'csrf_pass', False):
            return response

        if response.headers['Content-Type'].split(';')[0] in _HTML_TYPES:

            def add_csrf_field(match):
                """Returns the matched <form> tag plus the added <input> element"""

                return (match.group() + 
                    '\n<input type="hidden" name="%s" value="%s">' % (self.settings.CSRF.form_token_name, functions.csrf_token()))

            # Modify any POST forms
            response.data = _POST_FORM_RE.sub(add_csrf_field, response.data)

        return response
