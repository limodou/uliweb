from uliweb import Middleware, functions

class AuthMiddle(Middleware):
    ORDER = 100
    
    def process_request(self, request):
        request.user = functions.get_auth_user()

    def process_response(self, request, response):
        functions.update_user_session_expiry_time()
        return response
