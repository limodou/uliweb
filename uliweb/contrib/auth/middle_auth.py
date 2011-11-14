from uliweb import Middleware

class AuthMiddle(Middleware):
    ORDER = 100
    
    def process_request(self, request):
        from uliweb.contrib.auth import get_user
        request.user = get_user()
