from uliweb.middleware import Middleware
from weto.session import Session, SessionCookie

class SessionMiddle(Middleware):
    ORDER = 50
    def __init__(self, application, settings):
        from datetime import timedelta
        self.options = dict(settings.get('SESSION_STORAGE', {}))
        
        #process Session options
        self.session_expiry_time = settings.SESSION.remember_me_timeout
        self.session_storage_type = settings.SESSION.type
        
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
        self.timeout = settings.SESSION.timeout
        
    def process_request(self, request):
        key = request.cookies.get(SessionCookie.default_cookie_id)
        if not key:
            key = request.values.get(SessionCookie.default_cookie_id)
        session = Session(key, storage_type=self.session_storage_type, 
            options=self.options, expiry_time=self.session_expiry_time)
        request.session = session

    def process_response(self, request, response):
        session = request.session
        if session.deleted:
            response.delete_cookie(session.cookie.cookie_id)
        else:
            flag = session.save()
            if flag:
                c = session.cookie
                if session.remember:
                    max_age = c.expiry_time
                else:
                    max_age = self.timeout
                response.set_cookie(c.cookie_id,
                        session.key, max_age=max_age,
                        expires=None, domain=c.domain,
                        path=c.path,
                        secure=c.secure)
        return response
        
