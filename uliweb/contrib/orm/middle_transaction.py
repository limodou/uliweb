from uliweb import Middleware
from uliweb.orm import Begin, CommitAll, RollbackAll, set_echo

class TransactionMiddle(Middleware):
    ORDER = 80
    
    def __init__(self, application, settings):
        self.settings = settings
        
    def process_request(self, request):
        Begin()

    def process_response(self, request, response):
        from uliweb import response as res
        try:
            return response
        finally:
            CommitAll()

            #add post_commit process
            if hasattr(response, 'post_commit') and response.post_commit:
                response.post_commit()
                
            if response is not res and hasattr(res, 'post_commit') and res.post_commit:
                res.post_commit()
            
    def process_exception(self, request, exception):
        RollbackAll()
