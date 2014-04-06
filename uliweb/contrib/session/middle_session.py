from uliweb import Middleware, settings
from uliweb.utils.common import import_attr, application_path
from uliweb.core.SimpleFrame import RedirectException
from weto.session import Session, SessionCookie

class SessionMiddle(Middleware):
    def __init__(self, application, settings):
        from datetime import timedelta
        self.options = dict(settings.get('SESSION_STORAGE', {}))
        self.options['data_dir'] = application_path(self.options['data_dir'])
        if 'url' not in self.options:
            _url = (settings.get_var('ORM/CONNECTION', '') or
            settings.get_var('ORM/CONNECTIONS', {}).get('default', {}).get('CONNECTION', ''))
            if _url:
                self.options['url'] = _url
        
        #process Session options
        self.remember_me_timeout = settings.SESSION.remember_me_timeout
        self.session_storage_type = settings.SESSION.type
        self.timeout = settings.SESSION.timeout
        Session.force = settings.SESSION.force
        
        #process Cookie options
        SessionCookie.default_domain = settings.SESSION_COOKIE.domain
        SessionCookie.default_path = settings.SESSION_COOKIE.path
        SessionCookie.default_secure = settings.SESSION_COOKIE.secure
        SessionCookie.default_cookie_id = settings.SESSION_COOKIE.cookie_id

        if isinstance(settings.SESSION_COOKIE.timeout, int):
            timeout = timedelta(seconds=settings.SESSION_COOKIE.timeout)
        else:
            timeout = settings.SESSION_COOKIE.timeout
        SessionCookie.default_expiry_time = timeout
        
    def process_request(self, request):
        key = request.cookies.get(SessionCookie.default_cookie_id)
        if not key:
            key = request.values.get(SessionCookie.default_cookie_id)
        serial_cls_path = settings.SESSION.serial_cls
        if serial_cls_path:
            serial_cls = import_attr(serial_cls_path)
        else:
            serial_cls = None
        session = Session(key, storage_type=self.session_storage_type, 
            options=self.options, expiry_time=self.timeout, serial_cls=serial_cls)
        request.session = session

    def process_response(self, request, response):
        session = request.session
        if session.deleted:
            response.delete_cookie(session.cookie.cookie_id)
        else:
            cookie_max_age = None
            c = session.cookie
            if session.remember:
                session.set_expiry(self.remember_me_timeout)
                cookie_max_age = self.remember_me_timeout
            else:
                cookie_max_age = c.expiry_time
            flag = session.save()
            if flag:
                response.set_cookie(c.cookie_id,
                    session.key, max_age=cookie_max_age,
                    expires=None, domain=c.domain,
                    path=c.path, secure=c.secure)
        return response
        
    def process_exception(self, request, e):
        """
        Still process session data when specially Exception
        """
        if isinstance(e, RedirectException):
            response = e.get_response()
            self.process_response(request, response)
